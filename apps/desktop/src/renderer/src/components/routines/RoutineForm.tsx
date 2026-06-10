import { useState, type FormEvent } from "react";
import { Button } from "../ui/Button";
import type { OpenClawAgent, Routine, RoutineCreate, ScheduleType } from "../../lib/api/types";

interface RoutineFormProps {
  initial?: Routine | null;
  agents: OpenClawAgent[];
  submitting?: boolean;
  error?: string | null;
  onSubmit: (data: RoutineCreate) => void;
  onCancel: () => void;
}

const DAYS = [
  { value: "mon", label: "Monday" },
  { value: "tue", label: "Tuesday" },
  { value: "wed", label: "Wednesday" },
  { value: "thu", label: "Thursday" },
  { value: "fri", label: "Friday" },
  { value: "sat", label: "Saturday" },
  { value: "sun", label: "Sunday" },
];

function parseInitial(initial?: Routine | null) {
  const type = initial?.schedule_type ?? "manual";
  let time = "09:00";
  let day = "mon";
  if (initial && type === "daily") time = initial.schedule_value || "09:00";
  if (initial && type === "weekly") {
    const [d, t] = initial.schedule_value.split(" ");
    day = d || "mon";
    time = t || "09:00";
  }
  return { type, time, day };
}

export function RoutineForm({
  initial,
  agents,
  submitting,
  error,
  onSubmit,
  onCancel,
}: RoutineFormProps) {
  const parsed = parseInitial(initial);
  const [name, setName] = useState(initial?.name ?? "");
  const [agentId, setAgentId] = useState<string>(initial?.openclaw_agent_id ?? agents[0]?.id ?? "");
  const [prompt, setPrompt] = useState(initial?.prompt ?? "");
  const [scheduleType, setScheduleType] = useState<ScheduleType>(parsed.type);
  const [time, setTime] = useState(parsed.time);
  const [day, setDay] = useState(parsed.day);
  const [startAt, setStartAt] = useState((initial?.start_at ?? "").slice(0, 16));
  const [endAt, setEndAt] = useState((initial?.end_at ?? "").slice(0, 16));
  const [isEnabled, setIsEnabled] = useState(initial?.is_enabled ?? true);

  const recurring = scheduleType === "daily" || scheduleType === "weekly";

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (agentId === "") return;
    onSubmit({
      name: name.trim(),
      openclaw_agent_id: agentId,
      prompt: prompt.trim(),
      schedule_type: scheduleType,
      schedule_value:
        scheduleType === "daily" ? time : scheduleType === "weekly" ? `${day} ${time}` : "",
      start_at: scheduleType === "once" ? startAt || null : null,
      end_at: recurring && endAt ? endAt : null,
      is_enabled: isEnabled,
    });
  };

  const canSubmit =
    name.trim().length > 0 &&
    prompt.trim().length > 0 &&
    agentId !== "" &&
    (scheduleType !== "once" || startAt !== "") &&
    !submitting;

  return (
    <form className="agent-form" onSubmit={handleSubmit}>
      <h3>{initial ? "Edit routine" : "New routine"}</h3>

      {agents.length === 0 ? (
        <p className="form-error">Create an OpenClaw agent first — routines run an agent task on a schedule.</p>
      ) : null}

      <div className="form-row">
        <label htmlFor="r-name">Name</label>
        <input
          id="r-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Daily summary"
          required
        />
      </div>

      <div className="form-row">
        <label htmlFor="r-agent">Agent</label>
        <select
          id="r-agent"
          className="select"
          value={agentId}
          onChange={(e) => setAgentId(e.target.value)}
        >
          {agents.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name || a.id} · {a.model || "gemma4"}
            </option>
          ))}
        </select>
      </div>

      <div className="form-row">
        <label htmlFor="r-prompt">Task prompt</label>
        <textarea
          id="r-prompt"
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="What should the agent do each run?"
        />
      </div>

      <div className="form-row">
        <label htmlFor="r-type">Schedule</label>
        <select
          id="r-type"
          className="select"
          value={scheduleType}
          onChange={(e) => setScheduleType(e.target.value as ScheduleType)}
        >
          <option value="manual">Manual (run only on demand)</option>
          <option value="once">Once</option>
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
        </select>
      </div>

      {scheduleType === "once" ? (
        <div className="form-row">
          <label htmlFor="r-start">Run at</label>
          <input
            id="r-start"
            type="datetime-local"
            value={startAt}
            onChange={(e) => setStartAt(e.target.value)}
          />
        </div>
      ) : null}

      {scheduleType === "weekly" ? (
        <div className="form-row">
          <label htmlFor="r-day">Day</label>
          <select id="r-day" className="select" value={day} onChange={(e) => setDay(e.target.value)}>
            {DAYS.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>
        </div>
      ) : null}

      {scheduleType === "daily" || scheduleType === "weekly" ? (
        <>
          <div className="form-row">
            <label htmlFor="r-time">Time</label>
            <input id="r-time" type="time" value={time} onChange={(e) => setTime(e.target.value)} />
          </div>
          <div className="form-row">
            <label htmlFor="r-end">End date (optional)</label>
            <input
              id="r-end"
              type="datetime-local"
              value={endAt}
              onChange={(e) => setEndAt(e.target.value)}
            />
          </div>
        </>
      ) : null}

      <div className="form-checks">
        <label>
          <input
            type="checkbox"
            checked={isEnabled}
            onChange={(e) => setIsEnabled(e.target.checked)}
          />
          Enabled
        </label>
      </div>

      {error ? <p className="form-error">{error}</p> : null}

      <div className="form-actions">
        <Button type="submit" variant="primary" disabled={!canSubmit}>
          {submitting ? "Saving…" : initial ? "Save changes" : "Create routine"}
        </Button>
        <Button type="button" variant="ghost" onClick={onCancel} disabled={submitting}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
