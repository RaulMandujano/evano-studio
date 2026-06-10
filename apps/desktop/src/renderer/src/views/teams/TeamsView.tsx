/** Teams — saved multi-agent workflows: list, build, run, and automate them. */
import { useState, useSyncExternalStore } from "react";
import { PageHeader } from "../../components/ui/PageHeader";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { useBackendResource } from "../../hooks/useBackendResource";
import { backendApi } from "../../lib/api/client";
import { useNavigate } from "../../navigation-context";
import { teamsStore } from "../../lib/teamsStore";
import type { OpenClawAgentsResponse, Team } from "../../lib/api/types";
import { TeamBuilder } from "./TeamBuilder";
import { TeamRunner } from "./TeamRunner";

type Mode = "view" | "create" | "edit";

export function TeamsView() {
  const teamsRes = useBackendResource<Team[]>(backendApi.getTeams, "teams");
  const agentsRes = useBackendResource<OpenClawAgentsResponse>(backendApi.getOpenClawAgents, "oc-agents");
  const navigate = useNavigate();
  const run = useSyncExternalStore(teamsStore.subscribe, teamsStore.getSnapshot);

  const teams = teamsRes.data ?? [];
  const agents = agentsRes.data?.agents ?? [];
  const nameOf = (id: string) => agents.find((a) => a.id === id)?.name || id;

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [mode, setMode] = useState<Mode>("view");

  const selected = teams.find((t) => t.id === selectedId) ?? null;

  const startCreate = () => {
    setSelectedId(null);
    setMode("create");
  };
  const startEdit = () => setMode("edit");
  const afterSave = (team: Team) => {
    teamsRes.refresh();
    setSelectedId(team.id);
    setMode("view");
  };
  const onDeleted = () => {
    setSelectedId(null);
    setMode("view");
    teamsRes.refresh();
  };

  const renderList = () => {
    if (teamsRes.state === "checking") return <p className="muted">Loading teams…</p>;
    if (teamsRes.state !== "ready") return <p className="muted">Backend offline — start the engine and refresh.</p>;
    if (teams.length === 0) return <p className="muted">No teams yet. Create your first workflow.</p>;
    return (
      <ul className="agent-list">
        {teams.map((t) => (
          <li key={t.id}>
            <button
              className={`agent-list-item${t.id === selectedId && mode === "view" ? " is-active" : ""}`}
              onClick={() => { setSelectedId(t.id); setMode("view"); }}
            >
              <span className="agent-list-name">🤝 {t.name}</span>
              <span className="agent-list-model">{t.steps.length} agent{t.steps.length === 1 ? "" : "s"}</span>
            </button>
          </li>
        ))}
      </ul>
    );
  };

  const renderDetail = () => {
    if (agentsRes.state === "ready" && agentsRes.data && (!agentsRes.data.ok || agents.length < 2) && mode !== "view") {
      return (
        <Card className="notice-card">
          <h3>You need at least 2 agents</h3>
          <p className="muted">A team is a workflow of agents handing work to each other. Create a couple first.</p>
          <div className="form-actions"><Button variant="primary" onClick={() => navigate("openclaw-agents")}>Go to Agents</Button></div>
        </Card>
      );
    }
    if (mode === "create" || mode === "edit") {
      return (
        <TeamBuilder
          key={mode === "edit" ? `edit-${selected?.id}` : "create"}
          initial={mode === "edit" ? selected : null}
          agents={agents}
          onSaved={afterSave}
          onCancel={() => setMode("view")}
        />
      );
    }
    if (selected) {
      return (
        <TeamRunner
          team={selected}
          agents={agents}
          run={run}
          nameOf={nameOf}
          onEdit={startEdit}
          onDeleted={onDeleted}
        />
      );
    }
    return (
      <Card className="notice-card">
        <h3>Build a team workflow</h3>
        <p className="muted">
          A team is a line of agents that pass work to each other — e.g. <strong>Researcher → Writer → Reviewer</strong>.
          Each agent does its task using the previous one&apos;s result, so the team completes a real job together.
        </p>
        <div className="form-actions"><Button variant="primary" onClick={startCreate}>+ New team</Button></div>
      </Card>
    );
  };

  return (
    <div className="view">
      <PageHeader
        icon="🤝"
        title="Teams"
        subtitle="Build a workflow of agents that hand work to each other to complete real company tasks."
        badge={<Badge tone="alpha">Beta</Badge>}
      />
      <div className="toolbar">
        <span className="muted">{teamsRes.state === "ready" ? `${teams.length} team(s)` : "—"}</span>
        <div className="toolbar-actions">
          <Button onClick={() => teamsRes.refresh()}>↻ Refresh</Button>
          <Button variant="primary" onClick={startCreate}>+ New team</Button>
        </div>
      </div>
      <div className="agents-layout">
        <aside className="agents-sidebar">{renderList()}</aside>
        <section className="agents-detail">{renderDetail()}</section>
      </div>
    </div>
  );
}

// --------------------------- Team builder --------------------------------- //
