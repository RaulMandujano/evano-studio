/** Automate a team — schedule the whole workflow to run on its own. */
import { useCallback, useEffect, useState } from "react";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { backendApi } from "../../lib/api/client";
import { scheduleSummary, statusTone } from "../../lib/routines";
import type { Routine, ScheduleType, Team } from "../../lib/api/types";
import { DAYS } from "./constants";

export function TeamSchedule({ team }: { team: Team }) {
  const [routines, setRoutines] = useState<Routine[]>([]);
  const [open, setOpen] = useState(false);
  const [type, setType] = useState<ScheduleType>("daily");
  const [time, setTime] = useState("09:00");
  const [day, setDay] = useState("mon");
  const [startAt, setStartAt] = useState("");
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const all = await backendApi.getRoutines();
      setRoutines(all.filter((r) => r.team_id === team.id));
    } catch {
      /* ignore */
    }
  }, [team.id]);

  useEffect(() => {
    void load();
  }, [load]);

  const create = async () => {
    setBusy(true);
    setErr(null);
    try {
      await backendApi.createRoutine({
        name: `${team.name} (auto)`,
        team_id: team.id,
        prompt: input.trim() || team.name,
        schedule_type: type,
        schedule_value: type === "daily" ? time : type === "weekly" ? `${day} ${time}` : "",
        start_at: type === "once" ? startAt || null : null,
      });
      setInput("");
      setOpen(false);
      void load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Couldn't schedule the workflow.");
    } finally {
      setBusy(false);
    }
  };

  const toggle = async (r: Routine) => {
    await backendApi.updateRoutine(r.id, { is_enabled: !r.is_enabled });
    void load();
  };
  const runNow = async (r: Routine) => {
    setBusy(true);
    try {
      await backendApi.runRoutineNow(r.id);
    } finally {
      setBusy(false);
      void load();
    }
  };
  const del = async (r: Routine) => {
    if (!window.confirm("Remove this schedule?")) return;
    await backendApi.deleteRoutine(r.id);
    void load();
  };

  const recurring = type === "daily" || type === "weekly";

  return (
    <div className="team-automate">
      <h4 className="section-label">⏰ Automate this workflow</h4>
      <p className="muted form-hint">Run this team on a schedule — it works on its own, no person needed (while Evano is open).</p>

      {routines.length > 0 ? (
        <ul className="run-list" style={{ marginBottom: 10 }}>
          {routines.map((r) => (
            <li key={r.id} className="run-item">
              <div className="run-head">
                <Badge tone={statusTone(r.status)} dot>{r.is_enabled ? scheduleSummary(r) : "Paused"}</Badge>
                <span className="muted mono">{r.status}</span>
              </div>
              <div className="form-actions" style={{ marginTop: 6 }}>
                <Button onClick={() => runNow(r)} disabled={busy}>▶ Run now</Button>
                <Button onClick={() => toggle(r)} disabled={busy}>{r.is_enabled ? "Pause" : "Resume"}</Button>
                <Button variant="ghost" onClick={() => del(r)} disabled={busy}>Remove</Button>
              </div>
            </li>
          ))}
        </ul>
      ) : null}

      {open ? (
        <div className="team-automate-form">
          <div className="form-row">
            <label>Schedule</label>
            <select className="select" value={type} onChange={(e) => setType(e.target.value as ScheduleType)}>
              <option value="daily">Every day</option>
              <option value="weekly">Every week</option>
              <option value="once">Once</option>
            </select>
          </div>
          {type === "weekly" ? (
            <div className="form-row">
              <label>Day</label>
              <select className="select" value={day} onChange={(e) => setDay(e.target.value)}>
                {DAYS.map((d) => <option key={d.value} value={d.value}>{d.label}</option>)}
              </select>
            </div>
          ) : null}
          {recurring ? (
            <div className="form-row">
              <label>Time</label>
              <input type="time" value={time} onChange={(e) => setTime(e.target.value)} />
            </div>
          ) : (
            <div className="form-row">
              <label>Run at</label>
              <input type="datetime-local" value={startAt} onChange={(e) => setStartAt(e.target.value)} />
            </div>
          )}
          <div className="form-row">
            <label>Starting input (optional)</label>
            <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="What the first agent starts from" />
          </div>
          {err ? <p className="form-error">{err}</p> : null}
          <div className="form-actions">
            <Button variant="primary" onClick={create} disabled={busy || (type === "once" && !startAt)}>
              {busy ? "Saving…" : "Add schedule"}
            </Button>
            <Button variant="ghost" onClick={() => setOpen(false)} disabled={busy}>Cancel</Button>
          </div>
        </div>
      ) : (
        <Button onClick={() => setOpen(true)}>+ Add a schedule</Button>
      )}
    </div>
  );
}
