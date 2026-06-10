import { useCallback } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useOllamaModels, useRecommendedModels } from "../hooks/useOllama";
import { useModelPulls } from "../hooks/useModelPulls";
import { formatBytes } from "../lib/format";
import type { HardwareInfo, ModelFit, OllamaModel, PullStatus, RecommendedModel } from "../lib/api/types";

/** Cookbook-style fit labels: how well a model fits THIS machine. */
const FIT_META: Record<ModelFit, { label: string; tone: "ok" | "info" | "pending" | "danger" | "neutral" }> = {
  great: { label: "✓ Runs great here", tone: "ok" },
  good: { label: "✓ Runs well here", tone: "info" },
  tight: { label: "⚠ Tight fit", tone: "pending" },
  too_big: { label: "✗ Too big for this machine", tone: "danger" },
  unknown: { label: "Fit unknown", tone: "neutral" },
};

function HardwareCard({ hw }: { hw: HardwareInfo }) {
  return (
    <div className="hw-card">
      <span className="hw-icon" aria-hidden="true">💻</span>
      <div className="hw-main">
        <span className="hw-title">Your machine</span>
        <span className="hw-meta">
          {hw.chip ?? hw.platform} · {hw.ram_gb.toFixed(0)} GB {hw.unified_memory ? "unified memory" : "RAM"} ·{" "}
          {hw.cpu_cores} cores
        </span>
      </div>
      <span className="hw-note muted">Models below are scored for this hardware</span>
    </div>
  );
}

function InstalledRow({ model, recommended }: { model: OllamaModel; recommended: string }) {
  const isRecommended = model.name.split(":")[0].toLowerCase() === recommended.toLowerCase();
  return (
    <li className="model-item">
      <div className="model-main">
        <span className="model-name mono">{model.name}</span>
        {isRecommended ? <Badge tone="info">Recommended</Badge> : null}
      </div>
      <div className="model-meta">
        {model.parameter_size ? <span>{model.parameter_size}</span> : null}
        {model.family ? <span>{model.family}</span> : null}
        <span>{formatBytes(model.size_bytes)}</span>
      </div>
    </li>
  );
}

function PullProgress({ status }: { status: PullStatus }) {
  if (status.state === "error") {
    return <p className="pull-error">{status.message ?? "Install failed."}</p>;
  }
  const pct = Math.max(0, Math.min(100, status.percent));
  return (
    <div className="pull-progress">
      <div className="progress-track" aria-hidden="true">
        <div className="progress-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="pull-detail mono">
        {status.detail ?? "starting"} {pct > 0 ? `· ${pct.toFixed(0)}%` : ""}
      </span>
    </div>
  );
}

function RecommendedItem({
  model,
  reachable,
  pull,
  onInstall,
  bestPick,
}: {
  model: RecommendedModel;
  reachable: boolean;
  pull: PullStatus | undefined;
  onInstall: (model: string) => void;
  bestPick: boolean;
}) {
  const isPulling = pull?.state === "pending" || pull?.state === "downloading";
  const justInstalled = pull?.state === "success";
  const installed = model.installed || justInstalled;

  const renderAction = () => {
    if (installed) return <Badge tone="ok" dot>Installed</Badge>;
    if (isPulling) return <Badge tone="info" dot>Installing…</Badge>;
    return (
      <Button
        variant="primary"
        onClick={() => onInstall(model.model)}
        disabled={!reachable}
        title={reachable ? undefined : "Start Ollama to install models"}
      >
        Install
      </Button>
    );
  };

  const fitMeta = FIT_META[model.fit] ?? FIT_META.unknown;

  return (
    <Card className={`rec-item ${bestPick ? "rec-item--best" : ""} ${model.fit === "too_big" ? "rec-item--dim" : ""}`}>
      {bestPick ? <span className="rec-best-ribbon">⭐ Best for your machine</span> : null}
      <div className="rec-head">
        <div>
          <div className="rec-title">
            <span className="model-name">{model.name}</span>
            {model.recommended ? <Badge tone="info">Recommended</Badge> : null}
            {model.category.toLowerCase() !== "recommended" ? (
              <Badge tone="neutral">{model.category}</Badge>
            ) : null}
            <Badge tone={fitMeta.tone} dot>{fitMeta.label}</Badge>
          </div>
          <p className="rec-notes muted">{model.notes}</p>
          <p className="rec-fit muted">{model.fit_reason}</p>
          <p className="rec-tag mono muted">{model.model}</p>
        </div>
        <div className="rec-action">{renderAction()}</div>
      </div>

      <div className="rec-meta">
        {model.size_estimate ? <span>Size: {model.size_estimate}</span> : null}
        {model.min_ram ? <span>RAM: {model.min_ram}</span> : null}
      </div>

      {pull && !installed ? <PullProgress status={pull} /> : null}
    </Card>
  );
}

export function ModelsView() {
  const installed = useOllamaModels();
  const recommended = useRecommendedModels();

  const refreshLists = useCallback(() => {
    installed.refresh();
    recommended.refresh();
  }, [installed, recommended]);

  const { pulls, start } = useModelPulls(refreshLists);

  const installedBody = () => {
    if (installed.state === "checking") return <p className="muted">Checking for installed models…</p>;
    if (installed.state !== "ready" || !installed.data) {
      return (
        <Card className="notice-card">
          <h3>Can&apos;t reach the local backend</h3>
          <p className="muted">Start the Agent Engine, then refresh.</p>
        </Card>
      );
    }
    if (!installed.data.reachable) {
      return (
        <Card className="notice-card">
          <h3>Ollama isn&apos;t running</h3>
          <p className="muted">
            {installed.data.message ??
              "Install Ollama from ollama.com, start it, then refresh."}
          </p>
        </Card>
      );
    }
    if (installed.data.models.length === 0) {
      return <p className="muted">No models installed yet — install one below.</p>;
    }
    return (
      <ul className="model-list">
        {installed.data.models.map((m) => (
          <InstalledRow key={m.name} model={m} recommended={installed.data!.recommended_model} />
        ))}
      </ul>
    );
  };

  const reachable = recommended.data?.reachable ?? false;

  return (
    <div className="view">
      <PageHeader
        icon="🧠"
        title="Models"
        subtitle="Install free local models through Ollama — no terminal required. Nothing downloads automatically."
        badge={<Badge tone="alpha">Live</Badge>}
      />

      <div className="toolbar">
        <span className="muted">
          {installed.data?.reachable
            ? `${installed.data.count} installed`
            : "Ollama status unknown"}
        </span>
        <Button onClick={refreshLists}>↻ Refresh</Button>
      </div>

      <h2 className="section-label">Installed</h2>
      {installedBody()}

      <h2 className="section-label">Recommended for your machine</h2>
      <div className="callout-box">
        <strong>Heads up:</strong> models are large downloads (often 2–5 GB) and run in
        memory. Downloads run in the background — you can keep using the app.
      </div>

      {recommended.state === "checking" ? (
        <p className="muted">Scanning your hardware and loading recommendations…</p>
      ) : recommended.data ? (
        <>
          {recommended.data.hardware ? <HardwareCard hw={recommended.data.hardware} /> : null}
          {!reachable ? (
            <p className="muted">
              Ollama isn&apos;t reachable, so installs are disabled. Start Ollama and refresh.
            </p>
          ) : null}
          <div className="rec-list">
            {recommended.data.models.map((m) => (
              <RecommendedItem
                key={m.model}
                model={m}
                reachable={reachable}
                pull={pulls[m.model]}
                onInstall={start}
                bestPick={m.model === recommended.data!.best_pick}
              />
            ))}
          </div>
        </>
      ) : (
        <Card className="notice-card">
          <h3>Can&apos;t load recommendations</h3>
          <p className="muted">Start the Agent Engine, then refresh.</p>
        </Card>
      )}
    </div>
  );
}
