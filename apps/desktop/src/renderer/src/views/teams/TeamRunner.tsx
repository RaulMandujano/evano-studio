/** Team runner — show a workflow, run it, schedule it, and see live progress. */
import { useEffect, useState } from "react";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { backendApi } from "../../lib/api/client";
import { teamsStore } from "../../lib/teamsStore";
import type { OpenClawAgent, Team } from "../../lib/api/types";
import { STATUS_META } from "./constants";
import { TeamSchedule } from "./TeamSchedule";

export function TeamRunner({
  team,
  agents,
  run,
  nameOf,
  onEdit,
  onDeleted,
}: {
  team: Team;
  agents: OpenClawAgent[];
  run: ReturnType<typeof teamsStore.getSnapshot>;
  nameOf: (id: string) => string;
  onEdit: () => void;
  onDeleted: () => void;
}) {
  const [input, setInput] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setInput("");
  }, [team.id]);

  const isThisRun = run.teamId === team.id && run.steps.length > 0;
  const running = run.running && run.teamId === team.id;
  const canRun = team.steps.length >= 2 && !run.running;

  const lastAgent = agents.find((a) => a.id === team.steps[team.steps.length - 1]?.agent_id);

  const start = () => {
    const names = Object.fromEntries(agents.map((a) => [a.id, a.name || a.id]));
    void teamsStore.run(
      { id: team.id, name: team.name, steps: team.steps, working_file: team.working_file },
      input,
      names,
    );
  };

  const openFinalFolder = () => {
    if (lastAgent?.workspace) void window.evano?.services?.openWorkspacePath?.(lastAgent.workspace);
  };

  const del = async () => {
    if (!window.confirm(`Delete team "${team.name}"?`)) return;
    try {
      await backendApi.deleteTeam(team.id);
      onDeleted();
    } catch {
      /* ignore */
    }
  };

  const copyFinal = (text: string) => {
    void navigator.clipboard?.writeText(text);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  };

  const finalStep = isThisRun ? [...run.steps].reverse().find((s) => s.status === "done") : undefined;

  return (
    <div className="routine-detail">
      <div className="agent-detail-head">
        <div>
          <h3>🤝 {team.name}</h3>
          <p className="muted">
            {team.steps.length}-agent workflow
            {team.working_file ? <> · 📎 file <span className="mono">{team.working_file}</span> flows agent→agent</> : null}
          </p>
        </div>
        <div className="agent-detail-actions">
          <Button onClick={onEdit} disabled={running}>Edit</Button>
          <Button variant="ghost" onClick={del} disabled={running}>Delete</Button>
        </div>
      </div>

      {/* The workflow definition */}
      <ol className="team-flow team-flow--readonly" style={{ marginTop: 8 }}>
        {team.steps.map((st, i) => (
          <li key={i} className="team-flow-step">
            <div className="team-flow-line">
              <span className="team-step-num">{i + 1}</span>
              <span className="team-flow-agent">🤖 {nameOf(st.agent_id)}</span>
            </div>
            <p className="team-flow-task-read">{st.instruction || <span className="muted">No task set</span>}</p>
            {i < team.steps.length - 1 ? <div className="team-flow-arrow">↓</div> : null}
          </li>
        ))}
      </ol>

      <div className="form-row" style={{ marginTop: 14 }}>
        <label htmlFor="t-input">Starting input (optional)</label>
        <textarea
          id="t-input"
          rows={2}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Anything the first agent should start from — data, a goal, context…"
          disabled={running}
        />
      </div>
      <div className="form-actions">
        <Button variant="primary" onClick={start} disabled={!canRun}>
          {running ? "Workflow running…" : "▶ Run workflow"}
        </Button>
      </div>
      {team.steps.length < 2 ? <p className="form-hint">Add at least 2 agents (Edit) to run this as a workflow.</p> : null}
      {running ? <p className="form-hint">💡 This keeps running if you switch tabs — come back any time.</p> : null}
      {isThisRun && run.note ? <p className={run.note.startsWith("✓") ? "settings-ok" : "form-error"}>{run.note}</p> : null}

      {team.steps.length >= 2 ? <TeamSchedule team={team} /> : null}

      {/* Live run progress */}
      {isThisRun ? (
        <>
          <h4 className="section-label">Run progress</h4>
          <div className="team-steps">
            {run.steps.map((st, i) => {
              const meta = STATUS_META[st.status];
              return (
                <div key={i} className={`team-step team-step--${st.status}`}>
                  <div className="team-step-head">
                    <span className="team-step-num">{i + 1}</span>
                    <span className="team-step-name">🤖 {st.agentName}</span>
                    {st.instruction ? <span className="team-step-role">{st.instruction.slice(0, 40)}</span> : null}
                    <Badge tone={meta.tone} dot>{meta.label}</Badge>
                  </div>
                  {st.output ? <p className="team-step-output">{st.output}</p> : null}
                </div>
              );
            })}
          </div>
        </>
      ) : null}

      {finalStep && !running ? (
        <Card className="team-final team-final--spaced">
          <div className="env-card-head">
            <h3 className="settings-section-title">✅ Final result</h3>
            <div className="oc-dash-actions">
              {team.working_file && lastAgent?.workspace ? (
                <Button onClick={openFinalFolder}>📂 Open {nameOf(lastAgent.id)}&apos;s folder</Button>
              ) : null}
              <Button onClick={() => copyFinal(finalStep.output)}>{copied ? "Copied ✓" : "Copy"}</Button>
              <Button variant="primary" onClick={start}>Re-run</Button>
            </div>
          </div>
          {team.working_file ? (
            <p className="form-hint">📎 The file <span className="mono">{team.working_file}</span> is in {nameOf(lastAgent?.id ?? "")}&apos;s folder.</p>
          ) : null}
          <p className="team-final-output">{finalStep.output}</p>
        </Card>
      ) : null}
    </div>
  );
}

// ----------------------- Automate (schedule) ----------------------------- //
