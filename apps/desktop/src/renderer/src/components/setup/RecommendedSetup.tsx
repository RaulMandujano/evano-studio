import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { useModelPulls } from "../../hooks/useModelPulls";
import { formatBytes } from "../../lib/format";
import type { SetupStatus } from "../../lib/api/types";

const OLLAMA_DOWNLOAD = "https://ollama.com/download";

interface RecommendedSetupProps {
  status: SetupStatus;
  onChanged: () => void;
}

/**
 * One-click "recommended free setup": Ollama + Gemma 4. Designed for
 * non-technical users — it checks what's missing and installs the recommended
 * model in place (no terminal). Ollama itself must be installed by the user
 * (no silent installs), so we guide them to it when it isn't running.
 */
export function RecommendedSetup({ status, onChanged }: RecommendedSetupProps) {
  const { pulls, start } = useModelPulls(onChanged);
  const model = status.ollama.recommended_model || "gemma4";
  const pull = pulls[model];
  const installing = pull?.state === "pending" || pull?.state === "downloading";

  const openOllama = () => void window.evano?.services?.openExternal?.(OLLAMA_DOWNLOAD);

  // Step 1: Ollama not running → can't do anything until it's installed.
  if (!status.ollama.reachable) {
    return (
      <Card className="setup-progress-card">
        <div className="setup-progress-head">
          <div>
            <h3 className="setup-progress-title">⚡ Recommended setup (free)</h3>
            <p className="muted">
              First install <strong>Ollama</strong> — it runs the AI locally, for free. Once it&apos;s
              running, come back and refresh.
            </p>
          </div>
          <Badge tone="pending" dot>
            Ollama needed
          </Badge>
        </div>
        <div className="form-actions">
          <Button variant="primary" onClick={openOllama}>
            Download Ollama
          </Button>
          <Button onClick={onChanged}>I installed it — refresh</Button>
        </div>
      </Card>
    );
  }

  // Done: Ollama + a recommended model present.
  if (status.ollama.recommended_available) {
    return (
      <Card className="setup-progress-card">
        <div className="setup-progress-head">
          <div>
            <h3 className="setup-progress-title">✓ Free AI ready</h3>
            <p className="muted">
              Ollama is running and <strong>{model}</strong> is installed. Your agents run locally,
              for free.
            </p>
          </div>
          <Badge tone="ok" dot>
            Ready
          </Badge>
        </div>
      </Card>
    );
  }

  // Ollama is up but the recommended model isn't installed → one-click install.
  return (
    <Card className="setup-progress-card">
      <div className="setup-progress-head">
        <div>
          <h3 className="setup-progress-title">⚡ Recommended setup (free)</h3>
          <p className="muted">
            Install <strong>{model}</strong> — the recommended free model. One click, no terminal.
            It&apos;s a multi-GB download the first time.
          </p>
        </div>
        <Button variant="primary" onClick={() => void start(model)} disabled={installing}>
          {installing ? "Installing…" : `Install ${model} (free)`}
        </Button>
      </div>

      {pull ? (
        <div style={{ marginTop: 12 }}>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${Math.max(2, pull.percent)}%` }} />
          </div>
          <p className="form-hint">
            {pull.state === "error" ? (
              <span className="form-error">{pull.message ?? "Install failed."}</span>
            ) : pull.state === "success" ? (
              "Installed ✓"
            ) : (
              `${pull.percent}%${
                pull.total_bytes
                  ? ` · ${formatBytes(pull.completed_bytes)} / ${formatBytes(pull.total_bytes)}`
                  : ""
              }${pull.detail ? ` · ${pull.detail}` : ""}`
            )}
          </p>
        </div>
      ) : null}
    </Card>
  );
}
