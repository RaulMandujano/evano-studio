import { useCallback, useEffect, useState } from "react";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { backendApi } from "../../lib/api/client";
import { formatDateTime, scheduleSummary, statusTone } from "../../lib/routines";
import type { OpenClawAgent, Routine, RoutineDetail } from "../../lib/api/types";

interface RoutineDetailPanelProps {
  routineId: number;
  agents: OpenClawAgent[];
  /** Bumped by the parent to force a reload (e.g. after external changes). */
  reloadKey?: number;
  onEdit: (routine: Routine) => void;
  onChanged: () => void;
  onDeleted: () => void;
}

export function RoutineDetailPanel({
  routineId,
  agents,
  reloadKey,
  onEdit,
  onChanged,
  onDeleted,
}: RoutineDetailPanelProps) {
  const [detail, setDetail] = useState<RoutineDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [tick, setTick] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setDetail(await backendApi.getRoutineDetail(routineId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't load the routine.");
    } finally {
      setLoading(false);
    }
  }, [routineId]);

  useEffect(() => {
    void load();
  }, [load, reloadKey, tick]);

  const reload = () => setTick((t) => t + 1);

  const runNow = async () => {
    setBusy(true);
    setError(null);
    try {
      await backendApi.runRoutineNow(routineId);
      reload();
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Run failed.");
    } finally {
      setBusy(false);
    }
  };

  const toggle = async () => {
    if (!detail) return;
    setBusy(true);
    try {
      await backendApi.updateRoutine(routineId, { is_enabled: !detail.is_enabled });
      reload();
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (!detail) return;
    if (!window.confirm(`Delete routine "${detail.name}"?`)) return;
    setBusy(true);
    try {
      await backendApi.deleteRoutine(routineId);
      onDeleted();
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed.");
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <p className="muted">Loading routine…</p>;
  if (error && !detail) return <p className="form-error">{error}</p>;
  if (!detail) return null;

  const agentName =
    detail.team_id != null
      ? "🤝 Team workflow"
      : detail.openclaw_agent_id
        ? agents.find((a) => a.id === detail.openclaw_agent_id)?.name ?? detail.openclaw_agent_id
        : `Built-in #${detail.agent_id}`;

  return (
    <div className="routine-detail">
      <div className="agent-detail-head">
        <div>
          <h3>{detail.name}</h3>
          <p className="muted">
            {scheduleSummary(detail)} · <span className="mono">{agentName}</span>
          </p>
        </div>
        <Badge tone={statusTone(detail.status)} dot>
          {detail.status}
        </Badge>
      </div>

      <div className="agent-detail-actions" style={{ marginBottom: 14 }}>
        <Button variant="primary" onClick={runNow} disabled={busy}>
          {busy ? "Running…" : "▶ Run now"}
        </Button>
        <Button onClick={toggle} disabled={busy}>
          {detail.is_enabled ? "Disable" : "Enable"}
        </Button>
        {detail.team_id == null ? (
          <Button onClick={() => onEdit(detail)} disabled={busy}>
            Edit
          </Button>
        ) : null}
        <Button variant="ghost" onClick={remove} disabled={busy}>
          Delete
        </Button>
      </div>

      <dl className="engine-grid">
        <div>
          <dt>Next run</dt>
          <dd className="mono">{formatDateTime(detail.next_run_at)}</dd>
        </div>
        <div>
          <dt>Last run</dt>
          <dd className="mono">{formatDateTime(detail.last_run_at)}</dd>
        </div>
      </dl>

      <p className="muted" style={{ marginTop: 12 }}>
        <strong style={{ color: "var(--text)" }}>Prompt:</strong> {detail.prompt}
      </p>

      {error ? <p className="form-error">{error}</p> : null}

      <h4 className="section-label">Recent runs</h4>
      {detail.recent_runs.length === 0 ? (
        <p className="muted">No runs yet.</p>
      ) : (
        <ul className="run-list">
          {detail.recent_runs.map((run) => (
            <li key={run.id} className="run-item">
              <div className="run-head">
                <Badge tone={statusTone(run.status)}>{run.status}</Badge>
                <span className="muted mono">
                  {run.trigger} · {formatDateTime(run.started_at ?? run.created_at)}
                </span>
              </div>
              {run.output ? <p className="run-output">{run.output}</p> : null}
              {run.document_path ? (
                <p className="muted mono run-doc">Saved: {run.document_path}</p>
              ) : null}
              {run.error ? <p className="pull-error">{run.error}</p> : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
