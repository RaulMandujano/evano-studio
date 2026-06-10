import { Badge, type BadgeTone } from "../ui/Badge";
import { Button } from "../ui/Button";
import type { AgentEngineState, EngineStatus } from "../../hooks/useAgentEngineStatus";

const STATUS_META: Record<EngineStatus, { tone: BadgeTone; label: string }> = {
  checking: { tone: "info", label: "Checking…" },
  running: { tone: "ok", label: "Running" },
  offline: { tone: "pending", label: "Offline" },
  error: { tone: "danger", label: "Error" },
};

const HELP_TEXT: Record<EngineStatus, string> = {
  checking: "Contacting the local Agent Engine…",
  running: "The local backend is reachable and healthy.",
  offline: "The local backend isn't running. Start it, then refresh.",
  error: "The backend responded, but something was wrong.",
};

/**
 * Presentational dashboard panel for the Agent Engine connection. It takes the
 * status state as props (logic lives in `useAgentEngineStatus`) so it stays a
 * pure, easy-to-read UI component.
 */
export function AgentEngineStatusCard({
  status,
  health,
  message,
  lastCheckedAt,
  baseUrl,
  isChecking,
  refresh,
}: AgentEngineState) {
  const meta = STATUS_META[status];

  return (
    <section className="engine-panel" aria-live="polite">
      <div className="engine-panel-head">
        <div className="engine-panel-title">
          <span className="engine-panel-icon" aria-hidden="true">
            🧩
          </span>
          <div>
            <h3>Agent Engine</h3>
            <p className="engine-panel-help">{HELP_TEXT[status]}</p>
          </div>
        </div>
        <div className="engine-panel-actions">
          <Badge tone={meta.tone} dot>
            {meta.label}
          </Badge>
          <Button onClick={refresh} disabled={isChecking}>
            {isChecking ? "Checking…" : "↻ Refresh"}
          </Button>
        </div>
      </div>

      <dl className="engine-grid">
        <div>
          <dt>Endpoint</dt>
          <dd className="mono">{baseUrl}</dd>
        </div>
        <div>
          <dt>Version</dt>
          <dd className="mono">{health ? `v${health.version}` : "—"}</dd>
        </div>
        <div>
          <dt>Uptime</dt>
          <dd className="mono">
            {health ? `${Math.round(health.uptime_seconds)}s` : "—"}
          </dd>
        </div>
        <div>
          <dt>Last checked</dt>
          <dd className="mono">
            {lastCheckedAt ? lastCheckedAt.toLocaleTimeString() : "—"}
          </dd>
        </div>
      </dl>

      {message && status !== "running" ? (
        <p className="engine-message">{message}</p>
      ) : null}
    </section>
  );
}
