import { useState, type FormEvent, type KeyboardEvent } from "react";
import { Button } from "../ui/Button";

interface MessageInputProps {
  disabled?: boolean;
  placeholder?: string;
  onSend: (text: string) => void;
}

/** Multi-line message box. Enter sends; Shift+Enter inserts a newline. */
export function MessageInput({ disabled, placeholder, onSend }: MessageInputProps) {
  const [text, setText] = useState("");

  const submit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    submit();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <form className="message-input" onSubmit={handleSubmit}>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={2}
        disabled={disabled}
        placeholder={placeholder ?? "Type a message… (Enter to send, Shift+Enter for a new line)"}
      />
      <Button type="submit" variant="primary" disabled={disabled || !text.trim()}>
        Send
      </Button>
    </form>
  );
}
