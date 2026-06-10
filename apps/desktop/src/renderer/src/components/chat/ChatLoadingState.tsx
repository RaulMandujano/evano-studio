/** Inline "assistant is thinking" indicator shown while a reply is pending. */
export function ChatLoadingState() {
  return (
    <div className="chat-msg chat-msg--assistant chat-loading" aria-live="polite">
      <span className="chat-loading-dots" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>
      <span className="muted">Thinking…</span>
    </div>
  );
}
