/**
 * Org Chart — the chain of command between agents, like a company org chart.
 *
 * Not just a drawing: saving applies REAL delegation permissions to OpenClaw
 * (each manager may only command its direct reports), writes a "Your team"
 * note into every manager's AGENTS.md, and reloads the gateway. Message the
 * top agent on Discord and it gets the job done through its team.
 */
import { useMemo, useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useBackendResource } from "../hooks/useBackendResource";
import { backendApi } from "../lib/api/client";
import { useNavigate } from "../navigation-context";
import type { OrgAgent, OrgChartResponse } from "../lib/api/types";

/** parent map (child id → manager id) from the saved links. */
function toParentMap(res: OrgChartResponse | null): Record<string, string> {
  const map: Record<string, string> = {};
  for (const l of res?.links ?? []) {
    if (l.parent_agent_id) map[l.agent_id] = l.parent_agent_id;
  }
  return map;
}

/** every agent that sits under `id` (so the dropdown can forbid loops). */
function descendantsOf(id: string, parentOf: Record<string, string>): Set<string> {
  const out = new Set<string>();
  let added = true;
  while (added) {
    added = false;
    for (const [child, parent] of Object.entries(parentOf)) {
      if (!out.has(child) && (parent === id || out.has(parent))) {
        out.add(child);
        added = true;
      }
    }
  }
  return out;
}

function OrgNode({
  agent,
  agents,
  parentOf,
  onSetManager,
  disabled,
}: {
  agent: OrgAgent;
  agents: OrgAgent[];
  parentOf: Record<string, string>;
  onSetManager: (agentId: string, managerId: string) => void;
  disabled: boolean;
}) {
  const reports = agents.filter((a) => parentOf[a.id] === agent.id);
  const blocked = descendantsOf(agent.id, parentOf); // can't report to its own chain

  return (
    <li>
      <div className={`org-node ${reports.length > 0 ? "org-node--manager" : ""}`}>
        <span className="org-node-avatar" aria-hidden="true">{agent.emoji || "🤖"}</span>
        <span className="org-node-name">{agent.name}</span>
        <p className="org-node-model mono">{agent.model.replace(/^ollama\//, "") || "—"}</p>
        <div className="org-node-tags">
          {agent.is_default ? <Badge tone="info" dot>Default</Badge> : null}
          {reports.length > 0 ? (
            <Badge tone="ok" dot>
              Manages {reports.length}
            </Badge>
          ) : null}
        </div>
        <label className="org-node-boss">
          Reports to
          <select
            value={parentOf[agent.id] ?? ""}
            disabled={disabled}
            onChange={(e) => onSetManager(agent.id, e.target.value)}
          >
            <option value="">— nobody (top) —</option>
            {agents
              .filter((a) => a.id !== agent.id && !blocked.has(a.id))
              .map((a) => (
                <option key={a.id} value={a.id}>
                  {a.emoji ? `${a.emoji} ` : ""}{a.name}
                </option>
              ))}
          </select>
        </label>
      </div>
      {reports.length > 0 ? (
        <ul>
          {reports.map((r) => (
            <OrgNode
              key={r.id}
              agent={r}
              agents={agents}
              parentOf={parentOf}
              onSetManager={onSetManager}
              disabled={disabled}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export function OrgChartView() {
  const navigate = useNavigate();
  const res = useBackendResource<OrgChartResponse>(backendApi.getOrgChart);

  const saved = useMemo(() => toParentMap(res.data), [res.data]);
  const [draft, setDraft] = useState<Record<string, string> | null>(null);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [noteOk, setNoteOk] = useState(false);

  const parentOf = draft ?? saved;
  const dirty = draft !== null && JSON.stringify(draft) !== JSON.stringify(saved);

  const setManager = (agentId: string, managerId: string) => {
    const next = { ...parentOf };
    if (managerId) next[agentId] = managerId;
    else delete next[agentId];
    setDraft(next);
    setNote(null);
  };

  const save = async () => {
    setBusy(true);
    setNote(null);
    try {
      const links = Object.entries(parentOf).map(([agent_id, parent_agent_id]) => ({
        agent_id,
        parent_agent_id,
      }));
      const r = await backendApi.saveOrgChart(links);
      setNoteOk(r.ok);
      setNote(r.message);
      if (r.ok) {
        setDraft(null);
        res.refresh();
      }
    } catch (e) {
      setNoteOk(false);
      setNote(e instanceof Error ? e.message : "Couldn't save the org chart.");
    } finally {
      setBusy(false);
    }
  };

  const renderBody = () => {
    if (res.state === "checking") return <p className="muted">Loading the org chart…</p>;
    if (res.state !== "ready" || !res.data) {
      return (
        <Card className="notice-card">
          <h3>Can&apos;t reach the engine</h3>
          <p className="muted">Give it a moment, then retry.</p>
          <div className="form-actions"><Button variant="primary" onClick={res.refresh}>Retry</Button></div>
        </Card>
      );
    }
    if (!res.data.ok) {
      return (
        <Card className="notice-card">
          <h3>OpenClaw isn&apos;t ready yet</h3>
          <p className="muted">{res.data.message || "Finish the setup first."}</p>
          <div className="form-actions"><Button variant="primary" onClick={() => navigate("openclaw")}>Go to setup</Button></div>
        </Card>
      );
    }
    const agents = res.data.agents;
    if (agents.length < 2) {
      return (
        <Card className="notice-card">
          <h3>You need at least two agents</h3>
          <p className="muted">A chart needs a manager and a report. Create more agents first.</p>
          <div className="form-actions"><Button variant="primary" onClick={() => navigate("openclaw-agents")}>Go to Agents</Button></div>
        </Card>
      );
    }
    const roots = agents.filter((a) => !parentOf[a.id]);
    return (
      <>
        <div className="org-tree-wrap">
          <ul className="org-tree">
            {roots.map((a) => (
              <OrgNode
                key={a.id}
                agent={a}
                agents={agents}
                parentOf={parentOf}
                onSetManager={setManager}
                disabled={busy}
              />
            ))}
          </ul>
        </div>
        {dirty ? (
          <div className="org-savebar">
            <span>Unsaved changes — saving applies the permissions for real.</span>
            <div className="form-actions">
              <Button variant="ghost" onClick={() => { setDraft(null); setNote(null); }} disabled={busy}>
                Discard
              </Button>
              <Button variant="primary" onClick={save} disabled={busy}>
                {busy ? "Applying…" : "Save & apply"}
              </Button>
            </div>
          </div>
        ) : null}
      </>
    );
  };

  return (
    <div className="view">
      <PageHeader
        icon="🏛️"
        title="Org Chart"
        subtitle="Who commands whom. Pick a manager for each agent — managers can delegate work to their direct reports."
      />

      <Card className="card-spaced org-explainer">
        <p>
          💡 <strong>How it works:</strong> message a manager (in the Dashboard or on Discord if
          it&apos;s connected as a bot) and it can split the job across its team — their results
          come back to your chat. The chart is enforced: a manager can <em>only</em> command the
          agents directly under it.
        </p>
      </Card>

      {note ? <p className={noteOk ? "settings-ok" : "form-error"}>{note}</p> : null}
      {renderBody()}
    </div>
  );
}
