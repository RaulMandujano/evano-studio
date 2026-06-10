interface ChatErrorProps {
  message: string;
  onDismiss?: () => void;
}

/** Dismissible error banner shown when a chat request fails. */
export function ChatError({ message, onDismiss }: ChatErrorProps) {
  return (
    <div className="chat-error" role="alert">
      <span>{message}</span>
      {onDismiss ? (
        <button type="button" className="chat-error-dismiss" onClick={onDismiss} aria-label="Dismiss">
          ✕
        </button>
      ) : null}
    </div>
  );
}
