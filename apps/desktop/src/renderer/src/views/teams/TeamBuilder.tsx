/** Team builder — create/edit a saved workflow (name + ordered agents with tasks). */
import { useState } from "react";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { backendApi } from "../../lib/api/client";
import type { OpenClawAgent, Team, TeamStep } from "../../lib/api/types";

export function TeamBuilder({
  initial,
  agents,
  onSaved,
  onCancel,
}: {
  initial: Team | null;
  agents: OpenClawAgent[];
  onSaved: (t: Team) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(initial?.name ?? "");
  const [steps, setSteps] = useState<TeamStep[]>(initial?.steps ?? []);
  const [workingFile, setWorkingFile] = useState(initial?.working_file ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const nameOf = (id: string) => agents.find((a) => a.id === id)?.name || id;

  const addAgent = (id: string) => setSteps((s) => [...s, { agent_id: id, instruction: "" }]);
  const setInstruction = (i: number, instruction: string) =>
    setSteps((s) => s.map((st, idx) => (idx === i ? { ...st, instruction } : st)));
  const move = (i: number, dir: -1 | 1) =>
    setSteps((s) => {
      const j = i + dir;
      if (j < 0 || j >= s.length) return s;
      const c = [...s];
      [c[i], c[j]] = [c[j], c[i]];
      return c;
    });
  const remove = (i: number) => setSteps((s) => s.filter((_, idx) => idx !== i));

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const body = { name: name.trim(), steps, working_file: workingFile.trim() || null };
      const saved = initial ? await backendApi.updateTeam(initial.id, body) : await backendApi.createTeam(body);
      onSaved(saved);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't save the team.");
    } finally {
      setSaving(false);
    }
  };

  const canSave = name.trim().length > 0 && steps.length >= 1 && !saving;

  return (
    <Card>
      <h3 className="settings-section-title">{initial ? "Edit team" : "New team"}</h3>

      <div className="form-row">
        <label htmlFor="t-name">Team name</label>
        <input id="t-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Weekly Sales Report" />
      </div>

      <p className="settings-section-title" style={{ marginTop: 14, marginBottom: 6 }}>Add agents in work order</p>
      <div className="team-pick">
        {agents.map((a) => (
          <button key={a.id} className="team-chip" onClick={() => addAgent(a.id)} disabled={saving}>
            <span>🤖 {a.name || a.id}</span>
            <span className="team-chip-x">+</span>
          </button>
        ))}
      </div>

      {steps.length > 0 ? (
        <ol className="team-flow">
          {steps.map((st, i) => (
            <li key={i} className="team-flow-step">
              <div className="team-flow-line">
                <span className="team-step-num">{i + 1}</span>
                <span className="team-flow-agent">🤖 {nameOf(st.agent_id)}</span>
                <div className="team-member-actions">
                  <button title="Move up" onClick={() => move(i, -1)} disabled={saving || i === 0}>↑</button>
                  <button title="Move down" onClick={() => move(i, 1)} disabled={saving || i === steps.length - 1}>↓</button>
                  <button title="Remove" onClick={() => remove(i)} disabled={saving}>✕</button>
                </div>
              </div>
              <textarea
                className="team-flow-task"
                rows={2}
                value={st.instruction}
                onChange={(e) => setInstruction(i, e.target.value)}
                placeholder={`What should ${nameOf(st.agent_id)} do?  e.g. ${i === 0 ? "Research our top 3 competitors and list key facts." : "Use the previous result to write a 1-paragraph summary."}`}
                disabled={saving}
              />
              {i < steps.length - 1 ? <div className="team-flow-arrow">↓ passes result to</div> : null}
            </li>
          ))}
        </ol>
      ) : (
        <p className="form-hint">Click agents above to add them to the workflow, in the order they should work.</p>
      )}

      <div className="form-row" style={{ marginTop: 14 }}>
        <label htmlFor="t-file">📎 Shared working file (optional)</label>
        <input
          id="t-file"
          value={workingFile}
          onChange={(e) => setWorkingFile(e.target.value)}
          placeholder="e.g. report.md — flows agent → agent, each one edits it"
          disabled={saving}
        />
      </div>
      <p className="form-hint">
        If set, each agent works on this file in its own folder and Evano passes it to the next agent.
        Tell each agent to read/edit <span className="mono">{workingFile.trim() || "the file"}</span>.
      </p>

      {steps.length === 1 ? <p className="form-hint">Add at least 2 agents so they can collaborate.</p> : null}
      {error ? <p className="form-error">{error}</p> : null}

      <div className="form-actions" style={{ marginTop: 14 }}>
        <Button variant="primary" onClick={save} disabled={!canSave}>
          {saving ? "Saving…" : initial ? "Save changes" : "Create team"}
        </Button>
        <Button variant="ghost" onClick={onCancel} disabled={saving}>Cancel</Button>
      </div>
    </Card>
  );
}

// --------------------------- Team runner ---------------------------------- //
