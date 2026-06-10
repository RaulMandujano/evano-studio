import { Badge, type BadgeTone } from "../ui/Badge";
import { Button } from "../ui/Button";
import type { BackendResource } from "../../hooks/useBackendResource";
import type { OllamaStatus } from "../../lib/api/types";

type Display = { tone: BadgeTone; label: string; help: string };

function describe(resource: BackendResource<OllamaStatus>): Display {
  // Backend itself unreachable — we can't determine Ollama's status.
  if (resource.state === "checking") {
    return { tone: "info", label: "Checking…", help: "Contacting the backend…" };
  }
  if (resource.state === "offline" || resource.state === "error" || !resource.data) {
    return {
      tone: "pending",
      label: "Unknown",
      help: "Can't reach the local backend, so Ollama status is unavailable.",
    };
  }

  // Backend responded — use the reported Ollama status.
  switch (resource.data.status) {
    case "running":
      return { tone: "ok", label: "Running", help: "Ollama is installed and running." };
    case "offline":
      return {
        tone: "pending",
        label: "Not running",
        help: "Ollama isn't running. Install it from ollama.com, then start it.",
      };
    default:
      return { tone: "danger", label: "Error", help: "Ollama responded with an error." };
  }
}

/** Presentational dashboard panel for the local Ollama runtime. */
export function OllamaStatusCard(resource: BackendResource<OllamaStatus>) {
  const { data, message, isLoading, refresh } = resource;
  const display = describe(resource);
  const friendlyMessage = data?.status === "running" ? null : (data?.message ?? message);

  return (
    <section className="engine-panel" aria-live="polite">
      <div className="engine-panel-head">
        <div className="engine-panel-title">
          <span className="engine-panel-icon" aria-hidden="true">
            🦙
          </span>
          <div>
            <h3>Ollama</h3>
            <p className="engine-panel-help">{display.help}</p>
          </div>
        </div>
        <div className="engine-panel-actions">
          <Badge tone={display.tone} dot>
            {display.label}
          </Badge>
          <Button onClick={refresh} disabled={isLoading}>
            {isLoading ? "Checking…" : "↻ Refresh"}
          </Button>
        </div>
      </div>

      <dl className="engine-grid">
        <div>
          <dt>Endpoint</dt>
          <dd className="mono">{data?.base_url ?? "—"}</dd>
        </div>
        <div>
          <dt>Version</dt>
          <dd className="mono">{data?.version ? `v${data.version}` : "—"}</dd>
        </div>
        <div>
          <dt>Models</dt>
          <dd className="mono">{data ? data.model_count : "—"}</dd>
        </div>
        <div>
          <dt>Recommended</dt>
          <dd className="mono">
            {data
              ? `${data.recommended_model}${data.recommended_available ? " ✓" : " (not installed)"}`
              : "—"}
          </dd>
        </div>
      </dl>

      {friendlyMessage ? <p className="engine-message">{friendlyMessage}</p> : null}
    </section>
  );
}
