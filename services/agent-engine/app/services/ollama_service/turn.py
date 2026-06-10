"""Result of one native tool-calling chat turn."""
from __future__ import annotations

from dataclasses import dataclass, field

@dataclass
class AgenticTurn:
    """One turn of a tool-calling chat (Ollama native function calling)."""

    ok: bool
    # False only when the model itself can't do tool calling (so the caller can
    # fall back to the deterministic router). True for normal errors.
    supports_tools: bool = True
    content: str = ""
    tool_calls: list[dict] = field(default_factory=list)  # [{name, arguments}]
    raw_message: dict | None = None  # the assistant message to append verbatim
    latency_ms: int | None = None
    message: str | None = None  # error text when ok is False
