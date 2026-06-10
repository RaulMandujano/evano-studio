/**
 * Chats — every conversation with every agent, in one place.
 *
 * Organized like a session browser: agents as group headers, their chats
 * underneath, each labeled with where it happened (Evano, Discord, a team
 * run, the dashboard…). Click a chat to read it and keep talking in the
 * same session — the agent remembers.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useBackendResource } from "../hooks/useBackendResource";
import { backendApi } from "../lib/api/client";
import { useNavigate } from "../navigation-context";
import { timeAgo } from "../lib/office";
import type { AgentChats, AllChatsResponse, ChatOrigin, SessionSummary } from "../lib/api/types";

const ORIGIN_META: Record<ChatOrigin, { icon: string; label: string }> = {
  evano: { icon: "🖥️", label: "Evano Studio" },
  team: { icon: "🤝", label: "Team run" },
  discord: { icon: "🟣", label: "Discord" },
  telegram: { icon: "✈️", label: "Telegram" },
  whatsapp: { icon: "🟢", label: "WhatsApp" },
  slack: { icon: "🧩", label: "Slack" },
  signal: { icon: "🔵", label: "Signal" },
  imessage: { icon: "💬", label: "iMessage" },
  dashboard: { icon: "🦞", label: "Dashboard" },
  subagent: { icon: "🧑‍💼", label: "Delegated task" },
  cron: { icon: "⏰", label: "Scheduled" },
  other: { icon: "💬", label: "OpenClaw" },
};

interface Selected {
  agent: AgentChats;
  session: SessionSummary;
}

interface UiMsg {
  role: "user" | "assistant";
  content: string;
}

function ChatRow({ agent, session, active, onOpen }: {
  agent: AgentChats;
  session: SessionSummary;
  active: boolean;
  onOpen: () => void;
}) {
  const meta = ORIGIN_META[session.origin] ?? ORIGIN_META.other;
  return (
    <button type="button" className={`chat-row ${active ? "is-active" : ""}`} onClick={onOpen}>
      <span className="chat-row-dot" aria-hidden="true" />
      <span className="chat-row-body">
        <span className="chat-row-title">{session.preview || "(no preview)"}</span>
        <span className="chat-row-meta">
          <span className="chat-row-origin">{meta.icon} {meta.label}</span>
          <span>·</span>
          <span>{timeAgo(new Date(session.updated_at).toISOString())}</span>
          <span>·</span>
          <span>{session.message_count} msgs</span>
        </span>
      </span>
    </button>
  );
}

export function ChatsView() {
  const navigate = useNavigate();
  const res = useBackendResource<AllChatsResponse>(backendApi.getAllChats);

  const [selected, setSelected] = useState<Selected | null>(null);
  const [messages, setMessages] = useState<UiMsg[]>([]);
  const [loadingConvo, setLoadingConvo] = useState(false);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [convoError, setConvoError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const openChat = useCallback(async (agent: AgentChats, session: SessionSummary) => {
    setSelected({ agent, session });
    setMessages([]);
    setConvoError(null);
    setLoadingConvo(true);
    try {
      const detail = await backendApi.getOpenClawSession(agent.agent_id, session.session_id);
      setMessages(detail.ok ? detail.messages : []);
      if (!detail.ok) setConvoError(detail.message || "Couldn't load this conversation.");
    } catch (e) {
      setConvoError(e instanceof Error ? e.message : "Couldn't load this conversation.");
    } finally {
      setLoadingConvo(false);
    }
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, loadingConvo]);

  const send = async () => {
    if (!selected || !draft.trim() || sending) return;
    const text = draft.trim();
    setDraft("");
    setSending(true);
    setConvoError(null);
    setMessages((m) => [...m, { role: "user", content: text }]);
    try {
      const r = await backendApi.chatOpenClawAgent(selected.agent.agent_id, text, selected.session.session_id);
      if (r.ok) setMessages((m) => [...m, { role: "assistant", content: r.reply }]);
      else setConvoError(r.message || "The agent didn't reply.");
    } catch (e) {
      setConvoError(e instanceof Error ? e.message : "Couldn't send the message.");
    } finally {
      setSending(false);
    }
  };

  const deleteChat = async () => {
    if (!selected) return;
    if (!window.confirm("Delete this conversation? This can't be undone.")) return;
    try {
      await backendApi.deleteOpenClawSession(selected.agent.agent_id, selected.session.session_id);
      setSelected(null);
      setMessages([]);
      res.refresh();
    } catch {
      /* the list refresh will tell the truth */
    }
  };

  const renderList = () => {
    if (res.state === "checking") return <p className="muted">Loading chats…</p>;
    if (res.state !== "ready" || !res.data) {
      return (
        <div className="chats-notice">
          <p className="muted">Can&apos;t reach the engine.</p>
          <Button onClick={res.refresh}>Retry</Button>
        </div>
      );
    }
    if (!res.data.ok) {
      return (
        <div className="chats-notice">
          <p className="muted">{res.data.message || "OpenClaw isn't ready yet."}</p>
          <Button variant="primary" onClick={() => navigate("openclaw")}>Go to setup</Button>
        </div>
      );
    }
    const groups = res.data.agents;
    const total = groups.reduce((n, g) => n + g.sessions.length, 0);
    if (total === 0) {
      return (
        <div className="chats-notice">
          <p className="muted">No conversations yet — talk to an agent and it shows up here.</p>
          <Button variant="primary" onClick={() => navigate("openclaw-agents")}>Open Agents</Button>
        </div>
      );
    }
    return groups
      .filter((g) => g.sessions.length > 0)
      .map((g) => (
        <div key={g.agent_id} className="chat-group">
          <p className="chat-group-name">
            <span aria-hidden="true">{g.emoji || "🤖"}</span> {g.name}
          </p>
          {g.sessions.map((s) => (
            <ChatRow
              key={s.session_id}
              agent={g}
              session={s}
              active={selected?.session.session_id === s.session_id}
              onOpen={() => void openChat(g, s)}
            />
          ))}
        </div>
      ));
  };

  const originMeta = selected ? ORIGIN_META[selected.session.origin] ?? ORIGIN_META.other : null;

  return (
    <div className="view">
      <PageHeader
        icon="💬"
        title="Chats"
        subtitle="Every conversation with your agents — from this app, Discord, teams, and more."
      />
      <div className="chats-layout">
        <aside className="chats-list">
          <div className="chats-list-head">
            <span className="section-label">Conversations</span>
            <Button variant="ghost" onClick={res.refresh}>↻</Button>
          </div>
          {renderList()}
        </aside>

        <section className="chats-convo">
          {!selected ? (
            <Card className="chats-empty">
              <span className="chats-empty-icon">💬</span>
              <h3>Pick a conversation</h3>
              <p className="muted">Choose a chat on the left to read it — and keep talking right here.</p>
            </Card>
          ) : (
            <>
              <div className="chats-convo-head">
                <div>
                  <h3>
                    {selected.agent.emoji || "🤖"} {selected.agent.name}
                  </h3>
                  <p className="muted chats-convo-sub">
                    {originMeta!.icon} {originMeta!.label} · {selected.session.message_count} messages
                  </p>
                </div>
                <div className="form-actions">
                  <Button variant="ghost" onClick={deleteChat}>Delete</Button>
                </div>
              </div>

              <div className="chats-msgs" ref={scrollRef}>
                {loadingConvo ? <p className="muted">Loading conversation…</p> : null}
                {messages.map((m, i) => (
                  <div key={i} className={`chats-bubble chats-bubble--${m.role}`}>
                    {m.content}
                  </div>
                ))}
                {sending ? <div className="chats-bubble chats-bubble--assistant chats-bubble--pending">…</div> : null}
              </div>

              {convoError ? <p className="form-error">{convoError}</p> : null}

              <div className="chats-input">
                <textarea
                  rows={2}
                  value={draft}
                  placeholder={`Message ${selected.agent.name}… (same conversation — it remembers)`}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      void send();
                    }
                  }}
                  disabled={sending}
                />
                <Button variant="primary" onClick={() => void send()} disabled={sending || !draft.trim()}>
                  {sending ? "Sending…" : "Send"}
                </Button>
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
