import { useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useBackendResource } from "../hooks/useBackendResource";
import { backendApi } from "../lib/api/client";
import { useNavigate } from "../navigation-context";
import { OpenClawAgentDetail } from "./OpenClawAgentDetail";
import { AgentDiscordPanel } from "../components/openclaw/AgentDiscordPanel";
import type { OpenClawAgent, OpenClawAgentsResponse } from "../lib/api/types";

const DEFAULT_MODEL = "ollama/gemma4:latest";

interface Template {
  emoji: string;
  name: string;
  instructions: string;
}

const TEMPLATES: Template[] = [
  {
    emoji: "💼",
    name: "Office Assistant",
    instructions:
      "You are a helpful office assistant. Help write documents, organize files, and answer questions clearly and concisely.",
  },
  {
    emoji: "💬",
    name: "Customer Support",
    instructions:
      "You are a friendly customer support agent. Answer questions politely, help resolve issues, and keep replies short and warm.",
  },
  {
    emoji: "🔎",
    name: "Researcher",
    instructions:
      "You are a research assistant. Find information, summarize it clearly, and highlight the key points.",
  },
];

/**
 * OpenClaw Agents — create AI assistants that run INSIDE OpenClaw, powered by
 * free local Gemma 4. This is the bridge: from Evano you describe the agent, and
 * Evano writes it as a real OpenClaw agent (its own workspace + model + mission).
 */
export function OpenClawAgentsView() {
  const res = useBackendResource<OpenClawAgentsResponse>(backendApi.getOpenClawAgents, "oc-agents");
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [emoji, setEmoji] = useState("🤖");
  const [model, setModel] = useState(DEFAULT_MODEL);
  const [instructions, setInstructions] = useState("");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [noteOk, setNoteOk] = useState(false);
  const [openAgent, setOpenAgent] = useState<OpenClawAgent | null>(null);
  const [discordAgent, setDiscordAgent] = useState<OpenClawAgent | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  const applyTemplate = (t: Template) => {
    setName(t.name);
    setEmoji(t.emoji);
    setInstructions(t.instructions);
  };

  const create = async () => {
    setBusy(true);
    setNote(null);
    try {
      const r = await backendApi.createOpenClawAgent({ name, model, instructions, emoji });
      setNoteOk(r.ok);
      setNote(r.ok ? `Agent “${r.agent?.name ?? name}” created — chat with it in the Dashboard.` : r.message);
      if (r.ok) {
        setName("");
        setInstructions("");
        setEmoji("🤖");
        setModel(DEFAULT_MODEL);
        setShowCreate(false); // back to the agents — they're the main thing here
        res.refresh();
      }
    } catch (e) {
      setNoteOk(false);
      setNote(e instanceof Error ? e.message : "Couldn't create the agent.");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (agent: OpenClawAgent) => {
    if (!window.confirm(`Delete agent “${agent.name || agent.id}”? This removes its workspace.`)) return;
    setNote(null);
    try {
      const r = await backendApi.deleteOpenClawAgent(agent.id);
      setNoteOk(r.ok);
      setNote(r.message);
      if (r.ok) res.refresh();
    } catch (e) {
      setNoteOk(false);
      setNote(e instanceof Error ? e.message : "Couldn't delete the agent.");
    }
  };

  const renderList = () => {
    if (res.state === "checking") return <p className="muted">Loading agents…</p>;
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
    if (res.data.agents.length === 0) {
      return (
        <Card className="notice-card">
          <h3>No agents yet</h3>
          <p className="muted">Create your first one — it takes a name and a mission.</p>
          <div className="form-actions">
            <Button variant="primary" onClick={() => setShowCreate(true)}>➕ Create your first agent</Button>
          </div>
        </Card>
      );
    }
    return (
      <div className="channels-grid">
        {res.data.agents.map((a) => (
          <Card key={a.id} className="channel-card">
            <div className="channel-head">
              <span className="channel-icon" aria-hidden="true">🤖</span>
              <span className="channel-name">{a.name || a.id}</span>
              {a.is_default ? <Badge tone="info" dot>Default</Badge> : null}
              {a.bindings > 0 ? <Badge tone="ok" dot>Discord</Badge> : null}
            </div>
            <p className="channel-hint muted mono">{a.model || "—"}</p>
            <div className="form-actions">
              <Button variant="primary" onClick={() => setOpenAgent(a)}>Open</Button>
              <Button onClick={() => setDiscordAgent(a)}>💬 Discord</Button>
              {!a.is_default ? (
                <Button variant="ghost" onClick={() => remove(a)}>Delete</Button>
              ) : null}
            </div>
          </Card>
        ))}
      </div>
    );
  };

  if (openAgent) {
    return <OpenClawAgentDetail agent={openAgent} onBack={() => { setOpenAgent(null); res.refresh(); }} />;
  }

  if (discordAgent) {
    return (
      <AgentDiscordPanel agent={discordAgent} onBack={() => { setDiscordAgent(null); res.refresh(); }} />
    );
  }

  return (
    <div className="view">
      <PageHeader
        icon="🤖"
        title="Agents"
        subtitle="Your AI assistants, running inside OpenClaw — free, with local Gemma 4."
        badge={<Badge tone="alpha">Beta</Badge>}
      />

      <div className="agents-toolbar">
        <p className="section-label">Your agents</p>
        <Button variant={showCreate ? "ghost" : "primary"} onClick={() => setShowCreate(!showCreate)}>
          {showCreate ? "✕ Cancel" : "➕ New agent"}
        </Button>
      </div>

      {note ? <p className={noteOk ? "settings-ok" : "form-error"}>{note}</p> : null}

      {showCreate ? (
      <Card className="card-spaced">
        <h3 className="settings-section-title">Create an agent</h3>
        <p className="muted form-hint">Start from a template, or describe your own. It runs on free local Gemma 4.</p>

        <div className="templates-grid" style={{ marginBottom: 14 }}>
          {TEMPLATES.map((t) => (
            <button key={t.name} type="button" className="template-card" onClick={() => applyTemplate(t)}>
              <span className="template-icon">{t.emoji}</span>
              <span className="template-name">{t.name}</span>
              <span className="template-desc">{t.instructions.slice(0, 60)}…</span>
            </button>
          ))}
        </div>

        <div className="form-row" style={{ display: "flex", gap: 10 }}>
          <div style={{ width: 70 }}>
            <label htmlFor="oca-emoji">Emoji</label>
            <input id="oca-emoji" value={emoji} onChange={(e) => setEmoji(e.target.value)} maxLength={4} />
          </div>
          <div style={{ flex: 1 }}>
            <label htmlFor="oca-name">Name</label>
            <input id="oca-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Sales Helper" />
          </div>
        </div>
        <div className="form-row">
          <label htmlFor="oca-model">Model</label>
          <input id="oca-model" value={model} onChange={(e) => setModel(e.target.value)} placeholder={DEFAULT_MODEL} />
        </div>
        <div className="form-row">
          <label htmlFor="oca-inst">What should it do? (instructions)</label>
          <textarea
            id="oca-inst"
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            rows={4}
            placeholder="Describe the agent's job and how it should behave…"
          />
        </div>
        <div className="form-actions">
          <Button variant="primary" onClick={create} disabled={busy || !name.trim()}>
            {busy ? "Creating…" : "Create agent"}
          </Button>
        </div>
      </Card>
      ) : null}

      {renderList()}
    </div>
  );
}
