import { useCallback, useEffect, useRef, useState } from "react";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { backendApi } from "../lib/api/client";
import { formatBytes } from "../lib/format";
import type { AgentFile, OpenClawAgent, SessionSummary } from "../lib/api/types";

interface ChatMsg {
  role: "user" | "agent" | "error";
  content: string;
}

/** Native agent panel: chat with the OpenClaw agent and edit its config files,
 *  all inside Evano (no embedded dashboard). */
export function OpenClawAgentDetail({ agent, onBack }: { agent: OpenClawAgent; onBack: () => void }) {
  const [tab, setTab] = useState<"chat" | "config">("chat");
  return (
    <div className="view">
      <div className="oc-detail-head">
        <Button onClick={onBack}>← Back</Button>
        <h2 className="oc-detail-title">🤖 {agent.name || agent.id}</h2>
        <Badge tone="info" dot>{agent.model || "gemma4"}</Badge>
        {agent.workspace ? (
          <Button onClick={() => void window.evano?.services?.openWorkspacePath?.(agent.workspace)}>
            📂 Open folder
          </Button>
        ) : null}
      </div>
      {agent.workspace ? (
        <p className="form-hint mono" style={{ marginTop: -6 }}>Work area: {agent.workspace}</p>
      ) : null}

      <div className="oc-detail-tabs">
        <button className={`oc-tab ${tab === "chat" ? "is-active" : ""}`} onClick={() => setTab("chat")}>
          💬 Chat
        </button>
        <button className={`oc-tab ${tab === "config" ? "is-active" : ""}`} onClick={() => setTab("config")}>
          ⚙️ Configuration
        </button>
      </div>

      {tab === "chat" ? <AgentChat agent={agent} /> : <AgentConfig agent={agent} />}
    </div>
  );
}

// --------------------------------- Chat ----------------------------------- //

function newSessionId(): string {
  const rand =
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : Math.random().toString(36).slice(2);
  return `evano-${rand}`;
}

function relativeTime(ms: number): string {
  if (!ms) return "";
  const s = Math.floor((Date.now() - ms) / 1000);
  if (s < 60) return "just now";
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d < 30) return `${d}d ago`;
  return `${Math.floor(d / 30)}mo ago`;
}

function AgentChat({ agent }: { agent: OpenClawAgent }) {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState<string>(() => newSessionId());
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [totalBytes, setTotalBytes] = useState(0);
  const [loadingSession, setLoadingSession] = useState(false);
  const logRef = useRef<HTMLDivElement | null>(null);

  const refreshSessions = useCallback(async () => {
    try {
      const r = await backendApi.getOpenClawSessions(agent.id);
      if (r.ok) {
        setSessions(r.sessions);
        setTotalBytes(r.total_bytes);
      }
    } catch {
      /* ignore — history is best-effort */
    }
  }, [agent.id]);

  useEffect(() => {
    void refreshSessions();
  }, [refreshSessions]);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
  }, [messages, sending]);

  const newChat = () => {
    setMessages([]);
    setInput("");
    setSessionId(newSessionId());
  };

  const openSession = async (sid: string) => {
    if (sid === sessionId || sending) return;
    setLoadingSession(true);
    try {
      const r = await backendApi.getOpenClawSession(agent.id, sid);
      setSessionId(sid);
      setMessages(
        r.ok
          ? r.messages.map((m) => ({ role: m.role === "assistant" ? "agent" : "user", content: m.content }) as ChatMsg)
          : [],
      );
    } catch {
      setMessages([]);
    } finally {
      setLoadingSession(false);
    }
  };

  const removeSession = async (sid: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm("Delete this conversation?")) return;
    try {
      await backendApi.deleteOpenClawSession(agent.id, sid);
      if (sid === sessionId) newChat();
      void refreshSessions();
    } catch {
      /* ignore */
    }
  };

  const clearAll = async () => {
    if (!window.confirm("Delete ALL saved conversations for this agent? This frees disk space and can't be undone.")) return;
    try {
      await backendApi.clearOpenClawSessions(agent.id);
      newChat();
      void refreshSessions();
    } catch {
      /* ignore */
    }
  };

  const send = async () => {
    const text = input.trim();
    if (!text || sending) return;
    setMessages((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setSending(true);
    try {
      const r = await backendApi.chatOpenClawAgent(agent.id, text, sessionId);
      if (r.session_id) setSessionId(r.session_id); // keep continuity
      setMessages((m) => [...m, r.ok ? { role: "agent", content: r.reply } : { role: "error", content: r.message || "No reply." }]);
      void refreshSessions(); // the conversation is now saved on disk
    } catch (e) {
      setMessages((m) => [...m, { role: "error", content: e instanceof Error ? e.message : "Chat failed." }]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="oc-chat-shell">
      <aside className="oc-history">
        <div className="oc-history-head">
          <span>Conversations</span>
          <Button onClick={newChat} disabled={sending}>+ New</Button>
        </div>
        <div className="oc-history-list">
          {sessions.length === 0 ? <p className="muted oc-history-empty">No saved chats yet.</p> : null}
          {sessions.map((s) => (
            <button
              key={s.session_id}
              className={`oc-history-item ${s.session_id === sessionId ? "is-active" : ""}`}
              onClick={() => openSession(s.session_id)}
            >
              <span className="oc-history-preview">{s.preview}</span>
              <span className="oc-history-meta">{relativeTime(s.updated_at)} · {s.message_count} msg</span>
              <span className="oc-history-del" title="Delete" onClick={(e) => removeSession(s.session_id, e)}>✕</span>
            </button>
          ))}
        </div>
        <div className="oc-history-foot">
          <span className="muted">{formatBytes(totalBytes)} on disk</span>
          {sessions.length > 0 ? (
            <button className="oc-clear-btn" onClick={clearAll}>Clear all</button>
          ) : null}
        </div>
      </aside>

      <Card className="oc-chat-card">
        <div className="oc-chat-bar">
          <span className="muted oc-chat-bar-note">💬 Saved automatically — the agent remembers this chat.</span>
        </div>
        <div className="oc-chat-log" ref={logRef}>
          {loadingSession ? <p className="muted oc-chat-empty">Loading conversation…</p> : null}
          {!loadingSession && messages.length === 0 && !sending ? (
            <p className="muted oc-chat-empty">Say hello to {agent.name || agent.id}. It runs on local Gemma 4.</p>
          ) : null}
          {messages.map((m, i) => (
            <div key={i} className={`oc-msg oc-msg--${m.role}`}>
              {m.content}
            </div>
          ))}
          {sending ? <div className="oc-msg oc-msg--agent oc-msg--thinking">Thinking… (local AI can take ~30–60s)</div> : null}
        </div>
        <div className="oc-chat-input">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void send();
              }
            }}
            rows={2}
            placeholder={`Message ${agent.name || agent.id}… (Enter to send)`}
            disabled={sending}
          />
          <Button variant="primary" onClick={send} disabled={sending || !input.trim()}>
            {sending ? "…" : "Send"}
          </Button>
        </div>
      </Card>
    </div>
  );
}

// ------------------------------ Configuration ----------------------------- //

function AgentConfig({ agent }: { agent: OpenClawAgent }) {
  const [files, setFiles] = useState<AgentFile[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeName, setActiveName] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [saving, setSaving] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    void (async () => {
      try {
        const r = await backendApi.getOpenClawAgentFiles(agent.id);
        if (!alive) return;
        if (r.ok) {
          setFiles(r.files);
          const first = r.files.find((f) => f.exists) ?? r.files[0];
          if (first) {
            setActiveName(first.name);
            setDraft(first.content);
          }
        } else {
          setError(r.message || "Couldn't load the agent's files.");
        }
      } catch (e) {
        if (alive) setError(e instanceof Error ? e.message : "Couldn't load files.");
      }
    })();
    return () => {
      alive = false;
    };
  }, [agent.id]);

  const select = (f: AgentFile) => {
    setActiveName(f.name);
    setDraft(f.content);
    setNote(null);
  };

  const save = async () => {
    if (!activeName) return;
    setSaving(true);
    setNote(null);
    try {
      const r = await backendApi.saveOpenClawAgentFile(agent.id, activeName, draft);
      setNote(r.ok ? "Saved ✓" : r.message);
      if (r.ok) {
        setFiles((fs) => fs?.map((f) => (f.name === activeName ? { ...f, content: draft, exists: true } : f)) ?? fs);
      }
    } catch (e) {
      setNote(e instanceof Error ? e.message : "Couldn't save.");
    } finally {
      setSaving(false);
    }
  };

  if (error) {
    return (
      <Card className="notice-card">
        <h3>Couldn&apos;t open the configuration</h3>
        <p className="muted">{error}</p>
      </Card>
    );
  }
  if (!files) return <p className="muted">Loading configuration…</p>;

  return (
    <Card className="oc-config-card">
      <p className="muted form-hint">
        These are the files OpenClaw uses to define this agent. Edit them here and save — changes apply next time it runs.
      </p>
      <div className="oc-config-layout">
        <div className="oc-file-list">
          {files.map((f) => (
            <button
              key={f.name}
              className={`oc-file-item ${activeName === f.name ? "is-active" : ""}`}
              onClick={() => select(f)}
            >
              <span className="oc-file-label">{f.label}</span>
              <span className="oc-file-name mono">{f.name}{!f.exists ? " · new" : ""}</span>
            </button>
          ))}
        </div>
        <div className="oc-file-editor">
          <textarea value={draft} onChange={(e) => setDraft(e.target.value)} spellCheck={false} />
          <div className="form-actions">
            <Button variant="primary" onClick={save} disabled={saving}>
              {saving ? "Saving…" : "Save"}
            </Button>
            {note ? <span className={note.includes("✓") ? "settings-ok" : "form-error"}>{note}</span> : null}
          </div>
        </div>
      </div>
    </Card>
  );
}
