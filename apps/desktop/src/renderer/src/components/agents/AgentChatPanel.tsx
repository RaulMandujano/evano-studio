import { useRef, useState, type FormEvent } from "react";
import { Button } from "../ui/Button";
import { backendApi } from "../../lib/api/client";
import type { Agent, AgentChatMessage } from "../../lib/api/types";

interface ChatEntry {
  role: "user" | "assistant" | "error";
  content: string;
}

/** A basic test chat panel for a single agent. Keeps short-term context. */
export function AgentChatPanel({ agent }: { agent: Agent }) {
  const [entries, setEntries] = useState<ChatEntry[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToEnd = () => {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
    });
  };

  const send = async (event: FormEvent) => {
    event.preventDefault();
    const message = input.trim();
    if (!message || sending) return;

    // History = prior successful turns (exclude error notes).
    const history: AgentChatMessage[] = entries
      .filter((e): e is ChatEntry & { role: "user" | "assistant" } => e.role !== "error")
      .map((e) => ({ role: e.role, content: e.content }));

    setEntries((prev) => [...prev, { role: "user", content: message }]);
    setInput("");
    setSending(true);
    scrollToEnd();

    try {
      const result = await backendApi.chatWithAgent(agent.id, message, history);
      if (result.ok && result.reply) {
        setEntries((prev) => [...prev, { role: "assistant", content: result.reply as string }]);
      } else {
        setEntries((prev) => [
          ...prev,
          { role: "error", content: result.message ?? "No response from the model." },
        ]);
      }
    } catch (error) {
      const message_ = error instanceof Error ? error.message : "Request failed.";
      setEntries((prev) => [...prev, { role: "error", content: message_ }]);
    } finally {
      setSending(false);
      scrollToEnd();
    }
  };

  return (
    <div className="chat-panel">
      {!agent.is_enabled ? (
        <div className="callout-box">This agent is disabled. Enable it to chat.</div>
      ) : null}

      <div className="chat-messages" ref={scrollRef}>
        {entries.length === 0 ? (
          <p className="muted chat-empty">
            Send a message to test this agent. Responses come from the local model
            <span className="mono"> {agent.model_name}</span>.
          </p>
        ) : (
          entries.map((entry, index) => (
            <div key={index} className={`chat-msg chat-msg--${entry.role}`}>
              {entry.content}
            </div>
          ))
        )}
        {sending ? <div className="chat-msg chat-msg--assistant muted">Thinking…</div> : null}
      </div>

      <form className="chat-input-row" onSubmit={send}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message…"
          disabled={sending}
        />
        <Button type="submit" variant="primary" disabled={sending || !input.trim()}>
          Send
        </Button>
      </form>
    </div>
  );
}
