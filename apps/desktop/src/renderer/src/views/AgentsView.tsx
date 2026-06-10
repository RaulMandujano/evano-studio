import { useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { AgentForm } from "../components/agents/AgentForm";
import { AgentChatPanel } from "../components/agents/AgentChatPanel";
import { useBackendResource } from "../hooks/useBackendResource";
import { useOllamaModels } from "../hooks/useOllama";
import { backendApi } from "../lib/api/client";
import type { Agent, AgentCreate, AgentTemplate, AgentUpdate, ToolSpec } from "../lib/api/types";

type Mode = "idle" | "create" | "edit";

export function AgentsView() {
  const agentsRes = useBackendResource<Agent[]>(backendApi.getAgents);
  const modelsRes = useOllamaModels();
  const toolsRes = useBackendResource<ToolSpec[]>(backendApi.getTools);
  const templatesRes = useBackendResource<AgentTemplate[]>(backendApi.getAgentTemplates);

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [mode, setMode] = useState<Mode>("idle");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [draft, setDraft] = useState<Partial<Agent> | null>(null);

  const agents = agentsRes.data ?? [];
  const selected = agents.find((a) => a.id === selectedId) ?? null;

  const installedModels = modelsRes.data?.models.map((m) => m.name) ?? [];
  const defaultModel = installedModels[0] ?? modelsRes.data?.recommended_model ?? "";
  const tools = toolsRes.data ?? [];

  const handleCreate = async (data: AgentCreate) => {
    setSubmitting(true);
    setFormError(null);
    try {
      const created = await backendApi.createAgent(data);
      agentsRes.refresh();
      setSelectedId(created.id);
      setMode("idle");
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Couldn't create the agent.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdate = async (data: AgentUpdate) => {
    if (selected == null) return;
    setSubmitting(true);
    setFormError(null);
    try {
      await backendApi.updateAgent(selected.id, data);
      agentsRes.refresh();
      setMode("idle");
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Couldn't save changes.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (agent: Agent) => {
    if (!window.confirm(`Delete agent "${agent.name}"? This can't be undone.`)) return;
    try {
      await backendApi.deleteAgent(agent.id);
      if (selectedId === agent.id) setSelectedId(null);
      agentsRes.refresh();
    } catch {
      /* The list will simply stay as-is; user can retry. */
    }
  };

  const toggleEnabled = async (agent: Agent) => {
    try {
      await backendApi.updateAgent(agent.id, { is_enabled: !agent.is_enabled });
      agentsRes.refresh();
    } catch {
      /* ignore */
    }
  };

  const startCreate = () => {
    setDraft(null);
    setSelectedId(null);
    setMode("create");
    setFormError(null);
  };

  const useTemplate = (t: AgentTemplate) => {
    setDraft({
      name: t.name,
      description: t.description,
      system_prompt: t.system_prompt,
      temperature: t.temperature,
      knowledge_enabled: t.knowledge_enabled,
      enabled_tools: t.enabled_tools,
      model_name: t.model_name ?? undefined,
    });
    setSelectedId(null);
    setMode("create");
    setFormError(null);
  };

  const templates = templatesRes.data ?? [];

  const renderList = () => {
    if (agentsRes.state === "checking") return <p className="muted">Loading agents…</p>;
    if (agentsRes.state !== "ready") {
      return <p className="muted">Backend offline — start the Agent Engine and refresh.</p>;
    }
    if (agents.length === 0) {
      return <p className="muted">No agents yet. Create your first one.</p>;
    }
    return (
      <ul className="agent-list">
        {agents.map((agent) => (
          <li key={agent.id}>
            <button
              type="button"
              className={`agent-list-item${
                agent.id === selectedId && mode === "idle" ? " is-active" : ""
              }`}
              onClick={() => {
                setSelectedId(agent.id);
                setMode("idle");
              }}
            >
              <span
                className={`status-dot ${agent.is_enabled ? "is-on" : "is-off"}`}
                aria-hidden="true"
              />
              <span className="agent-list-name">{agent.name}</span>
              <span className="agent-list-model mono">{agent.model_name}</span>
            </button>
          </li>
        ))}
      </ul>
    );
  };

  const renderDetail = () => {
    if (mode === "create") {
      return (
        <Card>
          <AgentForm
            key={draft ? `tpl:${draft.name}` : "blank"}
            prefill={draft}
            models={installedModels}
            defaultModel={defaultModel}
            tools={tools}
            submitting={submitting}
            error={formError}
            onSubmit={handleCreate}
            onCancel={() => {
              setDraft(null);
              setMode("idle");
            }}
          />
        </Card>
      );
    }
    if (mode === "edit" && selected) {
      return (
        <Card>
          <AgentForm
            initial={selected}
            models={installedModels}
            defaultModel={defaultModel}
            tools={tools}
            submitting={submitting}
            error={formError}
            onSubmit={handleUpdate}
            onCancel={() => setMode("idle")}
          />
        </Card>
      );
    }
    if (selected) {
      return (
        <Card>
          <div className="agent-detail-head">
            <div>
              <h3>{selected.name}</h3>
              <p className="muted">
                {selected.description || "No description."}{" "}
                <span className="mono">· {selected.model_name}</span>
              </p>
            </div>
            <div className="agent-detail-actions">
              <Badge tone={selected.is_enabled ? "ok" : "neutral"} dot>
                {selected.is_enabled ? "Enabled" : "Disabled"}
              </Badge>
              <Button onClick={() => toggleEnabled(selected)}>
                {selected.is_enabled ? "Disable" : "Enable"}
              </Button>
              <Button onClick={() => { setMode("edit"); setFormError(null); }}>Edit</Button>
              <Button variant="ghost" onClick={() => handleDelete(selected)}>
                Delete
              </Button>
            </div>
          </div>
          <AgentChatPanel agent={selected} />
        </Card>
      );
    }
    return (
      <Card className="notice-card">
        <h3>No agent selected</h3>
        <p className="muted">Select an agent on the left, or create a new one.</p>
      </Card>
    );
  };

  return (
    <div className="view">
      <PageHeader
        icon="🤖"
        title="Agents"
        subtitle="Create local AI agents powered by Ollama, then chat with them to test."
        badge={<Badge tone="alpha">Live</Badge>}
      />

      <div className="toolbar">
        <span className="muted">
          {agentsRes.state === "ready" ? `${agents.length} agent(s)` : "—"}
        </span>
        <div className="toolbar-actions">
          <Button onClick={() => agentsRes.refresh()}>↻ Refresh</Button>
          <Button variant="primary" onClick={startCreate}>
            + New Agent
          </Button>
        </div>
      </div>

      {mode === "idle" && templates.length > 0 ? (
        <div className="templates-strip">
          <p className="templates-strip-label">Plantillas — empieza rápido</p>
          <div className="templates-grid">
            {templates.map((t) => (
              <button
                key={t.id}
                type="button"
                className="template-card"
                onClick={() => useTemplate(t)}
                title={`Crear "${t.name}"`}
              >
                <span className="template-icon" aria-hidden="true">{t.icon}</span>
                <span className="template-name">{t.name}</span>
                <span className="template-desc">{t.description}</span>
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <div className="agents-layout">
        <aside className="agents-sidebar">{renderList()}</aside>
        <section className="agents-detail">{renderDetail()}</section>
      </div>
    </div>
  );
}
