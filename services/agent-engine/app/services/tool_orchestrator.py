"""Agent Tool Orchestrator.

Decides — deterministically — whether a chat message is a request for a local
tool action and, if so, executes the approved tool through the existing
:class:`ToolService`. The language model is used ONLY to generate document
*content* when asked ("create a document about X"); the backend always decides
which tool runs and enforces permissions + the workspace boundary.

Flow for ``POST /agents/{id}/chat``:
1. Detect tool intent (English/Spanish, rule-based — see ``tools/intent.py``).
2. Enforce the agent's per-tool permission (deny-by-default).
3. Resolve any content directive (literal / model-generated / previous reply).
4. Execute via ToolService (which confines to the workspace and logs the run).
5. Return a response that states exactly what was done.

Returns ``None`` when the message is not a tool request, so the caller falls
back to a normal Ollama chat turn.
"""

from __future__ import annotations

import logging
from typing import Iterable

from ..core.errors import AppError
from ..schemas.agent import AgentChatResponse, ChatMessage
from ..schemas.tool import ToolExecution
from ..tools.intent import ContentDirective, ToolIntent, detect_tool_intent
from ..tools.registry import get_tool
from .ollama_service import OllamaService
from .tool_service import ToolService

logger = logging.getLogger("evano.agent_engine.agents")

_DOC_SYSTEM = (
    "You are a helpful writing assistant. Write clear, well-structured content "
    "for the user's document. Output ONLY the document body — no preamble, no "
    "explanations, no surrounding quotes."
)

# Tools whose content is produced/resolved by the orchestrator.
_CONTENT_TOOLS = {"create_markdown_document", "create_text_report", "create_text_file"}


class AgentToolOrchestrator:
    def __init__(self, ollama: OllamaService, tools: ToolService) -> None:
        self._ollama = ollama
        self._tools = tools

    def handle(
        self, agent, message: str, history: Iterable[ChatMessage]
    ) -> AgentChatResponse | None:
        # Detect a tool request FIRST. If the message clearly asks for a tool
        # action, we handle it here — even when the agent has the tool disabled —
        # so the model can never just *claim* it did something it can't do. Only
        # genuinely non-tool messages fall through to a normal chat turn.
        intent = detect_tool_intent(message)
        if intent is None:
            return None

        spec = get_tool(intent.tool_id)
        tool_name = spec.name if spec else intent.tool_id

        # Permission check (deny-by-default). Run it through ToolService so the
        # denial is logged, but with no params so no content is generated.
        if intent.tool_id not in (agent.enabled_tools or []):
            try:
                self._tools.execute(intent.tool_id, {}, agent=agent, source="agent")
            except AppError as exc:
                return self._failure(agent, intent.tool_id, tool_name, exc.message, kind="permission")
            return self._failure(agent, intent.tool_id, tool_name, "Not permitted.", kind="permission")

        # Resolve content for document/file tools (may call the model).
        params = dict(intent.params)
        if intent.tool_id in _CONTENT_TOOLS:
            try:
                params = self._build_content_params(agent, intent, list(history))
            except _ContentError as exc:
                return self._failure(agent, intent.tool_id, tool_name, str(exc), kind="content")

        # Execute the tool (workspace-confined, logged by ToolService).
        try:
            result = self._tools.execute(intent.tool_id, params, agent=agent, source="agent")
        except Exception as exc:  # noqa: BLE001 - any tool failure becomes a clean reply
            reason = exc.message if isinstance(exc, AppError) else "The tool failed unexpectedly."
            logger.warning("agent tool failed: agent=%s tool=%s reason=%s", agent.id, intent.tool_id, reason)
            return self._failure(agent, intent.tool_id, tool_name, reason, kind="error")

        reply = self._describe(intent.tool_id, params, result)
        logger.info("agent tool ok: agent=%s tool=%s", agent.id, intent.tool_id)
        return AgentChatResponse(
            ok=True,
            reply=reply,
            model=agent.model_name,
            tool_execution=ToolExecution(
                tool_id=intent.tool_id, tool_name=tool_name, ok=True, summary=reply, result=result
            ),
        )

    # ---- content resolution -------------------------------------------- #

    def _build_content_params(self, agent, intent: ToolIntent, history: list[ChatMessage]) -> dict:
        content = self._resolve_content(agent, intent, history)
        if not content.strip():
            raise _ContentError("There was no content to save.")

        if intent.tool_id == "create_text_file":
            file_name = intent.name or "note.txt"
            return {"file_name": file_name, "content": content}

        # markdown document / text report
        title = self._derive_title(intent, content)
        return {"title": title, "content": content}

    def _resolve_content(self, agent, intent: ToolIntent, history: list[ChatMessage]) -> str:
        directive = intent.content or ContentDirective(mode="generate", topic=intent.name)
        if directive.mode == "literal":
            return directive.text
        if directive.mode == "from_history":
            for msg in reversed(history):
                if msg.role == "assistant" and msg.content.strip():
                    return msg.content
            raise _ContentError("There's no previous reply to save yet.")
        # generate
        topic = directive.topic or intent.name
        if not topic:
            raise _ContentError("Tell me what the document should be about.")
        result = self._ollama.chat(
            agent.model_name,
            [
                {"role": "system", "content": _DOC_SYSTEM},
                {"role": "user", "content": f"Write a document about: {topic}."},
            ],
            agent.temperature,
        )
        if not result.ok or not (result.reply or "").strip():
            raise _ContentError(
                result.message or "I couldn't generate the content (is the model available?)."
            )
        return result.reply.strip()

    @staticmethod
    def _derive_title(intent: ToolIntent, content: str) -> str:
        from ..tools.intent import _DOC_EXT  # local import: same module concern

        if intent.name:
            return _DOC_EXT.sub("", intent.name)
        if intent.content and intent.content.topic:
            return intent.content.topic[:80]
        first_line = content.strip().splitlines()[0] if content.strip() else ""
        return (first_line[:80] or "Document").lstrip("# ").strip() or "Document"

    # ---- responses ----------------------------------------------------- #

    def _failure(self, agent, tool_id: str, tool_name: str, reason: str, *, kind: str) -> AgentChatResponse:
        if kind == "permission":
            reply = (
                f"This agent can't use \"{tool_name}\" yet — enable it under the agent's "
                "Tool Permissions, then try again.\n"
                f"Este agente no tiene activada la herramienta \"{tool_name}\". "
                "Actívala en los permisos del agente y vuelve a intentarlo."
            )
        elif kind == "content":
            reply = reason
        else:
            reply = f"I couldn't do that: {reason}"
        return AgentChatResponse(
            ok=False,
            reply=reply,
            model=agent.model_name,
            message=reply,
            tool_execution=ToolExecution(
                tool_id=tool_id, tool_name=tool_name, ok=False, summary=reply, message=reason
            ),
        )

    @staticmethod
    def _describe(tool_id: str, params: dict, result) -> str:
        if tool_id == "create_folder":
            return f'Done — I created the folder "{result.get("relative_path")}" in your workspace.'
        if tool_id in ("create_markdown_document", "create_text_report", "create_text_file"):
            rel = result.get("relative_path")
            size = result.get("bytes_written")
            suffix = f" ({size} bytes)" if size is not None else ""
            label = "file" if tool_id == "create_text_file" else "document"
            return f'Done — I created the {label} "{rel}"{suffix} in your workspace.'
        if tool_id == "list_files":
            entries = result.get("entries", [])
            where = params.get("path") or "your workspace"
            if not entries:
                return f"There are no files in {where} yet."
            lines = [f"- {e['name']}" + ("/" if e["type"] == "folder" else "") for e in entries]
            return f"Here's what's in {where} ({len(entries)} item(s)):\n" + "\n".join(lines)
        if tool_id == "search_workspace":
            matches = result.get("matches", [])
            if not matches:
                return f'I didn\'t find anything matching "{params.get("query")}" in your workspace.'
            lines = [f"- {m['file']}" + (f": …{m['snippet']}…" if m.get("snippet") else "") for m in matches]
            return f'Found {len(matches)} match(es) for "{params.get("query")}":\n' + "\n".join(lines)
        if tool_id == "read_text_file":
            return f"Contents of {params.get('path')}:\n\n{result.get('content', '')}"
        return "Done."


class _ContentError(Exception):
    """Raised when the document content can't be determined (user-facing message)."""
