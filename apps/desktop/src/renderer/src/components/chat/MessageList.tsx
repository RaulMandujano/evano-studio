import { useEffect, useRef } from "react";
import { ChatLoadingState } from "./ChatLoadingState";

/** A file created by a tool during this reply (for the "Open folder" action). */
export interface UiToolFile {
  name: string;
  relativePath: string;
  absolutePath: string;
}

export interface UiMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  /** Knowledge-base sources used for this assistant reply (labels). */
  sources?: string[];
  /** Set when this reply was produced by a deterministic tool action. */
  tool?: string;
  /** Set when the tool created a file on disk. */
  toolFile?: UiToolFile;
}

interface MessageListProps {
  messages: UiMessage[];
  loading: boolean;
  emptyHint?: string;
  /** When provided, assistant bubbles show a "Save as document" action. */
  onSaveAssistant?: (message: UiMessage) => void;
  savedIds?: Set<string>;
  savingId?: string | null;
}

/** Scrollable list of chat bubbles, with an inline loading indicator. */
export function MessageList({
  messages,
  loading,
  emptyHint,
  onSaveAssistant,
  savedIds,
  savingId,
}: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  return (
    <div className="chat-messages">
      {messages.length === 0 && !loading ? (
        <p className="muted chat-empty">{emptyHint ?? "Send a message to start chatting."}</p>
      ) : (
        messages.map((message) => (
          <div key={message.id} className={`chat-msg-row chat-msg-row--${message.role}`}>
            {message.tool ? (
              <span className="chat-tool-badge">🛠️ Tool used: {message.tool}</span>
            ) : null}
            <div className={`chat-msg chat-msg--${message.role}`}>{message.content}</div>
            {message.toolFile ? (
              <div className="chat-file-card">
                <span className="chat-file-icon" aria-hidden="true">
                  📄
                </span>
                <div className="chat-file-info">
                  <span className="chat-file-name">{message.toolFile.name}</span>
                  <span className="chat-file-path mono">{message.toolFile.relativePath}</span>
                </div>
                <button
                  type="button"
                  className="chat-save-btn"
                  onClick={() =>
                    void window.evano?.documents?.revealPath?.(message.toolFile!.absolutePath)
                  }
                >
                  Open folder
                </button>
              </div>
            ) : null}
            {message.sources && message.sources.length > 0 ? (
              <span className="chat-sources">Sources: {message.sources.join(", ")}</span>
            ) : null}
            {message.role === "assistant" && onSaveAssistant ? (
              <button
                type="button"
                className="chat-save-btn"
                onClick={() => onSaveAssistant(message)}
                disabled={savingId === message.id || savedIds?.has(message.id)}
              >
                {savedIds?.has(message.id)
                  ? "Saved ✓"
                  : savingId === message.id
                    ? "Saving…"
                    : "Save as document"}
              </button>
            ) : null}
          </div>
        ))
      )}
      {loading ? <ChatLoadingState /> : null}
      <div ref={endRef} />
    </div>
  );
}
