import { useCallback, useEffect, useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useAgentEngineStatus } from "../hooks/useAgentEngineStatus";
import { backendApi } from "../lib/api/client";
import type { LogEntry } from "../lib/api/types";

const AREAS = [
  "All",
  "System",
  "Backend",
  "Ollama",
  "Models",
  "Agents",
  "Documents",
  "Knowledge",
  "Images",
  "Routines",
  "Errors",
];

function levelClass(level: string): string {
  if (level === "ERROR" || level === "CRITICAL") return "log-level--error";
  if (level === "WARNING") return "log-level--warn";
  return "log-level--info";
}

export function LogsView() {
  const engine = useAgentEngineStatus();
  const [area, setArea] = useState("All");
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [bundlePath, setBundlePath] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await backendApi.getLogs({
        limit: 300,
        area: area === "All" ? undefined : area,
      });
      // Newest first for display.
      setEntries([...res.entries].reverse());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't load logs.");
    } finally {
      setLoading(false);
    }
  }, [area]);

  useEffect(() => {
    void load();
  }, [load]);

  const exportBundle = async () => {
    setExporting(true);
    setError(null);
    setBundlePath(null);
    try {
      const result = await backendApi.createSupportBundle();
      setBundlePath(result.path);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't export the support bundle.");
    } finally {
      setExporting(false);
    }
  };

  const openLocation = async (path: string) => {
    const reveal = window.evano?.documents?.revealPath;
    if (reveal) await reveal(path);
  };

  return (
    <div className="view view--wide">
      <PageHeader
        icon="📋"
        title="Logs"
        subtitle="Local diagnostics. Logs never include chat messages, document contents, or secrets."
        badge={<Badge tone="alpha">Live</Badge>}
      />

      <section className="engine-panel">
        <div className="engine-panel-head">
          <div className="engine-panel-title">
            <span className="engine-panel-icon" aria-hidden="true">📋</span>
            <div>
              <h3>Backend health</h3>
              <p className="engine-panel-help">
                {engine.status === "running"
                  ? "Agent Engine is running."
                  : "Agent Engine is not reachable."}
              </p>
            </div>
          </div>
          <div className="engine-panel-actions">
            <Badge tone={engine.status === "running" ? "ok" : "pending"} dot>
              {engine.status === "running" ? "Running" : "Offline"}
            </Badge>
            <Button onClick={() => void load()}>↻ Refresh</Button>
            <Button variant="primary" onClick={exportBundle} disabled={exporting}>
              {exporting ? "Exporting…" : "Export support bundle"}
            </Button>
          </div>
        </div>
        {bundlePath ? (
          <p className="settings-ok">
            Saved support bundle to <span className="mono">{bundlePath}</span>{" "}
            <button type="button" className="chat-save-btn" onClick={() => openLocation(bundlePath)}>
              Open location
            </button>
          </p>
        ) : null}
        {error ? <p className="form-error">{error}</p> : null}
      </section>

      <div className="log-filters">
        {AREAS.map((a) => (
          <button
            key={a}
            type="button"
            className={`log-chip${area === a ? " is-active" : ""}`}
            onClick={() => setArea(a)}
          >
            {a}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="muted">Loading logs…</p>
      ) : entries.length === 0 ? (
        <p className="muted">No log entries{area === "All" ? "" : ` for ${area}`} yet.</p>
      ) : (
        <ul className="log-list">
          {entries.map((entry, i) => (
            <li key={i} className="log-row">
              <span className={`log-level ${levelClass(entry.level)}`}>{entry.level}</span>
              <span className="log-area">{entry.area}</span>
              <span className="log-time mono">
                {new Date(entry.timestamp).toLocaleTimeString()}
              </span>
              <span className="log-message">{entry.message}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
