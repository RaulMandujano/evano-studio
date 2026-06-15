import { useEffect, useRef, useState, type ReactNode } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useBackendResource } from "../hooks/useBackendResource";
import { backendApi } from "../lib/api/client";
import { useNavigate } from "../navigation-context";
import type { OpenClawStatus, PrereqInstallStatus, PrereqTarget, ToolPresence } from "../lib/api/types";

const OPENCLAW_DOCS = "https://docs.openclaw.ai/";

/** Visual state of a step in the guided flow. */
type FlowState = "done" | "current" | "locked";

/** The 3-dot progress bar at the top so a user instantly sees the whole journey. */
function FlowStepper({
  steps,
}: {
  steps: { n: number; label: string; state: FlowState }[];
}) {
  return (
    <div className="flow-stepper" role="list">
      {steps.map((step, i) => (
        <div key={step.n} className="flow-stepper-seg" role="listitem">
          <div className={`flow-stepper-item is-${step.state}`}>
            <span className="flow-stepper-dot">{step.state === "done" ? "✓" : step.n}</span>
            <span className="flow-stepper-label">{step.label}</span>
          </div>
          {i < steps.length - 1 ? (
            <span className={`flow-stepper-line ${step.state === "done" ? "is-done" : ""}`} />
          ) : null}
        </div>
      ))}
    </div>
  );
}

/** One numbered step card. Locked steps are dimmed with a short hint. */
function FlowStep({
  n,
  title,
  state,
  status,
  intro,
  lockedHint,
  children,
}: {
  n: number;
  title: string;
  state: FlowState;
  status: ReactNode;
  intro: string;
  lockedHint?: string;
  children: ReactNode;
}) {
  return (
    <Card className={`oc-flow-step oc-flow-step--${state}`}>
      <div className="oc-flow-step-head">
        <span className={`oc-flow-step-num is-${state}`} aria-hidden="true">
          {state === "done" ? "✓" : n}
        </span>
        <div className="oc-flow-step-title-wrap">
          <h3 className="oc-flow-step-title">{title}</h3>
          <p className="oc-flow-step-intro muted">{intro}</p>
        </div>
        <div className="oc-flow-step-status">{status}</div>
      </div>
      {state === "locked" ? (
        <p className="oc-flow-locked-hint muted">🔒 {lockedHint}</p>
      ) : (
        <div className="oc-flow-step-body">{children}</div>
      )}
    </Card>
  );
}

function Check({
  ok,
  label,
  version,
  action,
  progress,
}: {
  ok: boolean;
  label: string;
  version?: string | null;
  action?: { text: string; onClick: () => void; disabled?: boolean };
  /** Live install feedback shown on its own line below the row. */
  progress?: { message: string; percent: number; tone: "info" | "ok" | "error"; manualUrl?: string };
}) {
  return (
    <li className="oc-check">
      <span className={`oc-mark ${ok ? "is-ok" : "is-missing"}`} aria-hidden="true">
        {ok ? "✓" : "○"}
      </span>
      <span className="oc-check-label">{label}</span>
      {version ? <span className="oc-check-ver mono">{version}</span> : null}
      {!ok && action ? (
        <Button variant="primary" onClick={action.onClick} disabled={action.disabled}>
          {action.text}
        </Button>
      ) : null}
      {progress ? (
        <span className={`oc-check-progress oc-check-progress--${progress.tone}`}>
          {progress.message}
          {progress.percent > 0 && progress.percent < 100 ? ` ${progress.percent}%` : ""}
          {progress.tone === "error" && progress.manualUrl ? (
            <>
              {" "}
              <a
                href={progress.manualUrl}
                onClick={(e) => {
                  e.preventDefault();
                  void window.evano?.services?.openExternal?.(progress.manualUrl!);
                }}
              >
                Download manually
              </a>
            </>
          ) : null}
        </span>
      ) : null}
    </li>
  );
}

/**
 * Evano as the friendly, guided control panel for OpenClaw. This is the app's
 * front door: a clear 3-step "easy install" flow — Install → Choose your AI →
 * Turn it on — so a non-technical user can go from nothing to a running local
 * AI assistant without ever touching a terminal.
 */
export function OpenClawView() {
  const statusRes = useBackendResource<OpenClawStatus>(backendApi.getOpenClawStatus, "oc-status");
  const navigate = useNavigate();
  const s = statusRes.data;

  const [installing, setInstalling] = useState(false);
  const [installMsg, setInstallMsg] = useState<string | null>(null);
  const [mode, setMode] = useState<"free" | "api">("free");
  const [provider, setProvider] = useState("anthropic");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("gemma4:latest");
  const [note, setNote] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  // Per-prerequisite (Node.js / Ollama) one-click install progress.
  const [prereq, setPrereq] = useState<Partial<Record<PrereqTarget, PrereqInstallStatus>>>({});
  const prereqPolls = useRef<Partial<Record<PrereqTarget, number>>>({});

  useEffect(
    () => () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
      Object.values(prereqPolls.current).forEach((id) => id && window.clearInterval(id));
    },
    [],
  );

  const open = (url: string) => void window.evano?.services?.openExternal?.(url);

  // Download + launch the official Node.js/Ollama installer, then poll progress.
  const installPrereq = async (target: PrereqTarget) => {
    setPrereq((p) => ({ ...p, [target]: { state: "downloading", message: "Starting…", percent: 0, download_url: "" } }));
    try {
      const init = await backendApi.installPrereq(target);
      setPrereq((p) => ({ ...p, [target]: init }));
      if (prereqPolls.current[target]) window.clearInterval(prereqPolls.current[target]);
      prereqPolls.current[target] = window.setInterval(async () => {
        try {
          const st = await backendApi.getPrereqInstallStatus(target);
          setPrereq((p) => ({ ...p, [target]: st }));
          if (st.state === "launched" || st.state === "error") {
            window.clearInterval(prereqPolls.current[target]);
            delete prereqPolls.current[target];
            statusRes.refresh();
          }
        } catch {
          /* keep polling */
        }
      }, 1500);
    } catch (e) {
      setPrereq((p) => ({
        ...p,
        [target]: { state: "error", message: e instanceof Error ? e.message : "Install failed.", percent: 0, download_url: "" },
      }));
    }
  };

  // Map a prerequisite's install state to the props the <Check> row needs.
  const prereqBusy = (t: PrereqTarget) => {
    const st = prereq[t];
    return st?.state === "downloading" || st?.state === "launching";
  };
  const prereqLabel = (t: PrereqTarget, base: string) => {
    const st = prereq[t];
    if (st?.state === "downloading") return `Downloading… ${st.percent || 0}%`;
    if (st?.state === "launching") return "Opening installer…";
    return base;
  };
  const prereqProgress = (t: PrereqTarget): { message: string; percent: number; tone: "info" | "ok" | "error"; manualUrl?: string } | undefined => {
    const st = prereq[t];
    if (!st || st.state === "idle") return undefined;
    if (st.state === "error") return { message: st.message, percent: 0, tone: "error", manualUrl: st.download_url };
    if (st.state === "launched") return { message: st.message, percent: 0, tone: "ok" };
    return { message: st.message, percent: st.percent, tone: "info" };
  };

  const install = async () => {
    setInstalling(true);
    setInstallMsg("Installing OpenClaw…");
    try {
      await backendApi.installOpenClaw();
      pollRef.current = window.setInterval(async () => {
        try {
          const st = await backendApi.getOpenClawInstallStatus();
          setInstallMsg(st.message || st.state);
          if (st.state === "success" || st.state === "error") {
            if (pollRef.current) window.clearInterval(pollRef.current);
            setInstalling(false);
            statusRes.refresh();
          }
        } catch {
          /* keep polling */
        }
      }, 2500);
    } catch (e) {
      setInstalling(false);
      setInstallMsg(e instanceof Error ? e.message : "Install failed.");
    }
  };

  const saveConfig = async () => {
    setNote(null);
    setBusy("config");
    try {
      const res = await backendApi.writeOpenClawConfig(
        mode === "free"
          ? { mode: "free", model: model || "gemma4:latest" }
          : { mode: "api", provider, model, api_key: apiKey },
      );
      setNote(res.ok ? (mode === "free" ? "Configured — free local Gemma 4." : "Configured (API).") : res.message);
      statusRes.refresh();
    } catch (e) {
      setNote(e instanceof Error ? e.message : "Couldn't save the config.");
    } finally {
      setBusy(null);
    }
  };

  const enableWebSearch = async () => {
    setNote(null);
    setBusy("web");
    try {
      const res = await backendApi.enableOpenClawWebSearch();
      setNote(res.ok ? "Free web search enabled (DuckDuckGo)." : res.message);
      statusRes.refresh();
    } catch (e) {
      setNote(e instanceof Error ? e.message : "Couldn't enable web search.");
    } finally {
      setBusy(null);
    }
  };

  const gateway = async (action: "start" | "stop") => {
    setNote(null);
    setBusy(action);
    try {
      const res = action === "start"
        ? await backendApi.startOpenClawGateway()
        : await backendApi.stopOpenClawGateway();
      setNote(res.ok ? `Gateway ${action === "start" ? "started" : "stopped"}.` : res.message);
      statusRes.refresh();
    } catch (e) {
      setNote(e instanceof Error ? e.message : "Gateway action failed.");
    } finally {
      setBusy(null);
    }
  };

  const renderBody = () => {
    if (statusRes.state === "checking") return <p className="muted">Checking…</p>;
    if (statusRes.state !== "ready" || !s) {
      return (
        <Card className="notice-card">
          <h3>Can&apos;t reach the local engine</h3>
          <p className="muted">Evano&apos;s engine may still be starting — give it a moment, then retry.</p>
          <div className="form-actions"><Button variant="primary" onClick={statusRes.refresh}>Retry</Button></div>
        </Card>
      );
    }

    const tp = (t: ToolPresence) => t.installed;

    // ---- Derive the three step states (one source of truth) ----------------
    const step1Done = tp(s.openclaw);
    const step2Done = s.config.exists;
    const step3Done = s.gateway.running;

    const stepState = (done: boolean, prevDone: boolean): FlowState =>
      done ? "done" : prevDone ? "current" : "locked";

    const st1: FlowState = step1Done ? "done" : "current";
    const st2: FlowState = stepState(step2Done, step1Done);
    const st3: FlowState = stepState(step3Done, step2Done);

    const allReady = step1Done && step2Done && step3Done;

    return (
      <>
        {/* Hero — what's happening, in one friendly line */}
        <Card className={`oc-hero ${allReady ? "is-ready" : ""}`}>
          <div className="oc-hero-text">
            <h3 className="oc-hero-title">
              {allReady ? "🎉 You're all set!" : "Set up your AI assistant in 3 easy steps"}
            </h3>
            <p className="muted">
              {allReady
                ? "OpenClaw is installed, configured, and running for free with Gemma 4. Open the dashboard to start chatting and connecting channels like WhatsApp or Discord."
                : "Evano installs and configures everything for you — no terminal, no setup files. Just follow the steps below."}
            </p>
          </div>
          <Button onClick={statusRes.refresh}>Refresh</Button>
        </Card>

        <FlowStepper
          steps={[
            { n: 1, label: "Install", state: st1 },
            { n: 2, label: "Choose your AI", state: st2 },
            { n: 3, label: "Turn it on", state: st3 },
          ]}
        />

        {/* ---- STEP 1: Install -------------------------------------------- */}
        <FlowStep
          n={1}
          title="Install OpenClaw"
          state={st1}
          intro="One click installs OpenClaw on your computer. We'll check what's needed."
          status={
            step1Done ? (
              <Badge tone="ok" dot>Installed</Badge>
            ) : (
              <Badge tone="pending" dot>Action needed</Badge>
            )
          }
        >
          <ul className="oc-checklist">
            <Check
              ok={tp(s.node)}
              label="Node.js"
              version={s.node.version}
              action={{ text: prereqLabel("node", "Install Node.js"), onClick: () => installPrereq("node"), disabled: prereqBusy("node") }}
              progress={prereqProgress("node")}
            />
            <Check
              ok={tp(s.ollama)}
              label="Ollama (free local AI)"
              version={s.ollama.version}
              action={{ text: prereqLabel("ollama", "Install Ollama"), onClick: () => installPrereq("ollama"), disabled: prereqBusy("ollama") }}
              progress={prereqProgress("ollama")}
            />
            <li className="oc-check">
              <span className={`oc-mark ${tp(s.openclaw) ? "is-ok" : "is-missing"}`} aria-hidden="true">
                {tp(s.openclaw) ? "✓" : "○"}
              </span>
              <span className="oc-check-label">OpenClaw</span>
              {s.openclaw.version ? <span className="oc-check-ver mono">{s.openclaw.version}</span> : null}
              {!tp(s.openclaw) ? (
                <Button variant="primary" onClick={install} disabled={installing || !tp(s.node)}>
                  {installing ? "Installing…" : "Install OpenClaw"}
                </Button>
              ) : (
                <Badge tone="ok" dot>Installed</Badge>
              )}
            </li>
          </ul>
          {installMsg ? <p className="form-hint">{installMsg}</p> : null}
          {!tp(s.node) ? (
            <p className="form-hint">⚠ Install Node.js first (free), then come back and install OpenClaw.</p>
          ) : null}
          {!tp(s.ollama) ? (
            <p className="form-hint">
              💡 Ollama runs the AI on your computer for free. Install it to use the free option in step 2.
            </p>
          ) : null}
        </FlowStep>

        {/* ---- STEP 2: Choose your AI ------------------------------------- */}
        <FlowStep
          n={2}
          title="Choose your AI"
          state={st2}
          intro="Pick how OpenClaw thinks. The free option runs on your computer — no cost, no account."
          lockedHint="Install OpenClaw in step 1 first."
          status={
            step2Done ? (
              <Badge tone="ok" dot>Configured</Badge>
            ) : (
              <Badge tone="neutral" dot>Not chosen</Badge>
            )
          }
        >
          <div className="oc-choice-grid">
            <label className={`oc-choice ${mode === "free" ? "is-selected" : ""}`}>
              <input type="radio" name="oc-mode" checked={mode === "free"} onChange={() => setMode("free")} />
              <div>
                <div className="oc-choice-title">🆓 Free — local Gemma 4</div>
                <p className="oc-choice-desc muted">Runs on your machine with Ollama. No API key, no monthly cost. Recommended.</p>
              </div>
            </label>
            <label className={`oc-choice ${mode === "api" ? "is-selected" : ""}`}>
              <input type="radio" name="oc-mode" checked={mode === "api"} onChange={() => setMode("api")} />
              <div>
                <div className="oc-choice-title">🔑 Paid API</div>
                <p className="oc-choice-desc muted">Use a provider like Anthropic or OpenAI with your own API key.</p>
              </div>
            </label>
          </div>

          {mode === "free" ? (
            <div className="form-row">
              <label htmlFor="oc-model">Model</label>
              <input id="oc-model" value={model} onChange={(e) => setModel(e.target.value)} placeholder="gemma4:latest" />
            </div>
          ) : (
            <>
              <div className="form-row">
                <label htmlFor="oc-prov">Provider</label>
                <input id="oc-prov" value={provider} onChange={(e) => setProvider(e.target.value)} placeholder="anthropic / openai" />
              </div>
              <div className="form-row">
                <label htmlFor="oc-model2">Model</label>
                <input id="oc-model2" value={model} onChange={(e) => setModel(e.target.value)} placeholder="model name" />
              </div>
              <div className="form-row">
                <label htmlFor="oc-key">API key</label>
                <input id="oc-key" type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="sk-…" />
              </div>
            </>
          )}
          <div className="form-actions">
            <Button variant="primary" onClick={saveConfig} disabled={!tp(s.openclaw) || busy !== null}>
              {busy === "config" ? "Saving…" : "Save & continue"}
            </Button>
            <Button onClick={() => open(OPENCLAW_DOCS)}>OpenClaw docs</Button>
          </div>
          {s.config.exists ? (
            <p className="form-hint">
              Current: <span className="mono">{s.config.provider ?? "?"} / {s.config.model ?? "?"}</span>
            </p>
          ) : null}

          <div className="oc-websearch">
            <span className="oc-websearch-label">🔎 Internet search</span>
            {s.web_search.enabled ? (
              <Badge tone="ok" dot>{s.web_search.provider === "duckduckgo" ? "DuckDuckGo (free)" : s.web_search.provider} ✓</Badge>
            ) : (
              <Button onClick={enableWebSearch} disabled={!tp(s.openclaw) || busy !== null}>
                {busy === "web" ? "Enabling…" : "Enable free web search"}
              </Button>
            )}
          </div>
          <p className="form-hint">Lets your agents search the web (e.g. weather, prices, news) — free, no API key.</p>
        </FlowStep>

        {/* ---- STEP 3: Turn it on ----------------------------------------- */}
        <FlowStep
          n={3}
          title="Turn it on"
          state={st3}
          intro="Start OpenClaw and open its dashboard to chat and connect channels."
          lockedHint="Choose your AI in step 2 first."
          status={
            <Badge tone={s.gateway.running ? "ok" : "neutral"} dot>
              {s.gateway.running ? `Running · port ${s.gateway.port}` : "Stopped"}
            </Badge>
          }
        >
          <div className="form-actions">
            <Button variant="primary" onClick={() => gateway("start")} disabled={s.gateway.running || busy !== null}>
              {busy === "start" ? "Starting…" : "Start OpenClaw"}
            </Button>
            <Button onClick={() => gateway("stop")} disabled={!s.gateway.running || busy !== null}>
              {busy === "stop" ? "Stopping…" : "Stop"}
            </Button>
            <Button variant={s.gateway.running ? "primary" : undefined} onClick={() => navigate("openclaw-dashboard")}>
              Open dashboard →
            </Button>
            <Button onClick={() => navigate("channels")}>Connect channels</Button>
          </div>
          <p className="form-hint">✨ OpenClaw starts automatically every time you open Evano. The dashboard opens right inside Evano.</p>
        </FlowStep>

        {note ? <p className="settings-ok">{note}</p> : null}
      </>
    );
  };

  return (
    <div className="view oc-flow">
      <PageHeader
        icon="🦞"
        title="Welcome to Evano"
        subtitle="Your easy control panel for OpenClaw — install, configure, and run it without the terminal."
        badge={<Badge tone="alpha">Beta</Badge>}
      />
      {renderBody()}
    </div>
  );
}
