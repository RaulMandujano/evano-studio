"""Agentic tool-calling loop (the "brain").

This is the OpenClaw-style improvement, kept inside Evano's safety model: the
local model *decides* which tools to call (native Ollama function calling), the
backend *executes* them through the existing :class:`ToolService` — which is
deny-by-default and confined to the workspace — feeds the real results back, and
loops until the model produces a final answer.

Key safety properties (unchanged from the rest of the app):
- Only the agent's explicitly enabled tools are exposed to the model.
- Every call still goes through ToolService → workspace-confined, verified, logged.
- No shell, no arbitrary filesystem access, no network/computer control.

Returns ``None`` when the model can't do native tool calling, so the caller can
fall back to the deterministic regex router (works for small models like
gemma3:4b).
"""

from __future__ import annotations

import logging

from sqlmodel import Session

from ..core.errors import AppError
from ..db.models import PendingAction
from ..schemas.action import PendingActionRead
from ..schemas.agent import AgentChatResponse, ChatSource
from ..schemas.tool import ToolExecution
from ..tools.registry import ToolSpec, get_tool
from .ollama_service import OllamaService
from .tool_service import ToolService

logger = logging.getLogger("evano.agent_engine.agents")

# Bound the loop so a confused model can't spin forever.
_MAX_STEPS = 6

# Nudge so tool-enabled agents ACT instead of only describing or asking.
_TOOL_GUIDANCE = (
    "You can take real actions with the available tools (create folders, files, "
    "and documents in the user's workspace). When the user asks you to create, "
    "save, or make something, DO IT by calling the right tool — don't just "
    "explain how. If they ask for a document, report, or summary about a topic, "
    "WRITE the content yourself and pass it to the tool; only ask the user for "
    "content when they must provide specific text you cannot reasonably write. "
    "Reply in the user's language."
)
# Map our simple param types to JSON-schema types for the tool spec.
_JSON_TYPE = {"string": "string", "text": "string", "integer": "integer"}


def _tool_schema(spec: ToolSpec) -> dict:
    """Build an Ollama/OpenAI-style function schema from a ToolSpec."""
    properties: dict = {}
    required: list[str] = []
    for p in spec.parameters:
        properties[p.name] = {"type": _JSON_TYPE.get(p.type, "string"), "description": p.description}
        if p.required:
            required.append(p.name)
    return {
        "type": "function",
        "function": {
            "name": spec.id,
            "description": spec.description,
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }


class AgentLoop:
    def __init__(self, ollama: OllamaService, tools: ToolService, session: Session) -> None:
        self._ollama = ollama
        self._tools = tools
        self._session = session

    def run(
        self, agent, messages: list[dict], sources: list[ChatSource] | None
    ) -> AgentChatResponse | None:
        """Run the tool-calling loop. ``messages`` is the full conversation so
        far (system + RAG context + history + the new user turn).

        Returns ``None`` if the model doesn't support native tool calling.
        """
        specs = [get_tool(t) for t in (agent.enabled_tools or [])]
        tool_schemas = [_tool_schema(s) for s in specs if s is not None]
        if not tool_schemas:
            return None  # nothing to orchestrate; let the caller chat normally

        convo = list(messages)
        convo.insert(0, {"role": "system", "content": _TOOL_GUIDANCE})
        executions: list[ToolExecution] = []

        for step in range(_MAX_STEPS):
            turn = self._ollama.chat_agentic(
                agent.model_name, convo, tool_schemas, agent.temperature
            )

            if not turn.ok:
                # Couldn't start the agentic path (model lacks tool support, or
                # Ollama is offline) and nothing has run yet → fall back to the
                # deterministic router, which can still handle simple requests.
                if not executions:
                    logger.info(
                        "agent loop: cannot start (supports_tools=%s) → fallback: %s",
                        turn.supports_tools, turn.message,
                    )
                    return None
                # Failed mid-task → report what we actually accomplished.
                return AgentChatResponse(
                    ok=False, model=agent.model_name, message=turn.message,
                    reply=turn.message, tool_execution=executions[-1],
                    tool_executions=executions,
                )

            # No tool calls → this is the final natural-language answer.
            if not turn.tool_calls:
                reply = (turn.content or "").strip() or self._fallback_reply(executions)
                # Safety net: the model must NOT claim success when a tool failed.
                # Append the real failures so the user always sees the truth.
                failures = [e for e in executions if not e.ok]
                has_success = any(e.ok for e in executions)
                if failures:
                    notes = "; ".join(f"{e.tool_name}: {e.message}" for e in failures)
                    reply = f"{reply}\n\n⚠️ Some actions did not complete — {notes}".strip()
                ok = not (failures and not has_success)
                return AgentChatResponse(
                    ok=ok,
                    reply=reply,
                    model=agent.model_name,
                    sources=sources,
                    tool_execution=executions[-1] if executions else None,
                    tool_executions=executions or None,
                )

            # Append the assistant message (with its tool_calls) verbatim.
            convo.append(turn.raw_message or {"role": "assistant", "content": turn.content})

            # Execute each requested tool and feed the real result back.
            for call in turn.tool_calls:
                spec = get_tool(call["name"])
                # Human-in-the-loop: sensitive (computer-control) tools are NOT
                # run by the agent. Propose the action and wait for approval.
                if spec is not None and spec.requires_approval:
                    pending = self._create_pending(agent, spec, call.get("arguments") or {})
                    return AgentChatResponse(
                        ok=True,
                        reply=f"Approval needed — I'd like to {pending.summary}.",
                        model=agent.model_name,
                        sources=sources,
                        tool_execution=executions[-1] if executions else None,
                        tool_executions=executions or None,
                        pending_action=pending,
                    )
                execution, observation = self._run_tool(agent, call["name"], call["arguments"])
                executions.append(execution)
                convo.append({"role": "tool", "tool_name": call["name"], "content": observation})

        # Hit the step cap — return what we have rather than looping forever.
        logger.warning("agent loop hit step cap (%s) for agent=%s", _MAX_STEPS, agent.id)
        return AgentChatResponse(
            ok=True,
            reply=self._fallback_reply(executions),
            model=agent.model_name,
            sources=sources,
            tool_execution=executions[-1] if executions else None,
            tool_executions=executions or None,
        )

    @staticmethod
    def _fallback_reply(executions: list[ToolExecution]) -> str:
        """A human reply when the model returns no final text but tools ran."""
        done = [e.summary for e in executions if e.ok]
        if done:
            return "Done — " + "; ".join(done) + "."
        failed = [e.message or e.summary for e in executions if not e.ok]
        if failed:
            return "I couldn't finish: " + "; ".join(failed)
        return "Done."

    def _create_pending(self, agent, spec: ToolSpec, args: dict) -> PendingActionRead:
        """Record a proposed sensitive action awaiting human approval."""
        if not isinstance(args, dict):
            args = {}
        summary, preview = self._describe_pending(spec.id, args)
        pending = PendingAction(
            agent_id=agent.id, agent_name=agent.name, tool_id=spec.id, tool_name=spec.name,
            summary=summary, preview=preview, args=args, status="pending",
        )
        self._session.add(pending)
        self._session.commit()
        self._session.refresh(pending)
        logger.info("agent proposed action needing approval: agent=%s tool=%s", agent.id, spec.id)
        return PendingActionRead.model_validate(pending)

    @staticmethod
    def _describe_pending(tool_id: str, args: dict) -> tuple[str, str]:
        if tool_id == "open_application":
            app = str(args.get("app_name", "")).strip()
            return f'open the application "{app}"', app
        if tool_id == "open_url":
            url = str(args.get("url", "")).strip()
            return f"open {url} in your browser", url
        if tool_id == "run_command":
            cmd = str(args.get("command", "")).strip()
            return "run a command on your computer", cmd
        return f"run {tool_id}", str(args)

    def _run_tool(self, agent, name: str, args: dict) -> tuple[ToolExecution, str]:
        """Execute one tool call; return (execution record, observation string).

        The observation is what we feed back to the model — a real success result
        or a real error, so the model never has to guess what happened.
        """
        spec = get_tool(name)
        tool_name = spec.name if spec else name
        if not isinstance(args, dict):
            args = {}
        try:
            result = self._tools.execute(name, args, agent=agent, source="agent")
        except AppError as exc:
            logger.warning("agent loop tool failed: agent=%s tool=%s err=%s", agent.id, name, exc.message)
            execution = ToolExecution(
                tool_id=name, tool_name=tool_name, ok=False,
                summary=f"{tool_name} failed", message=exc.message,
            )
            return execution, f"ERROR: {exc.message}"
        except Exception as exc:  # noqa: BLE001
            logger.exception("agent loop tool crashed: agent=%s tool=%s", agent.id, name)
            execution = ToolExecution(
                tool_id=name, tool_name=tool_name, ok=False,
                summary=f"{tool_name} failed", message=str(exc),
            )
            return execution, f"ERROR: {exc}"

        summary = self._summarize(name, result)
        execution = ToolExecution(
            tool_id=name, tool_name=tool_name, ok=True, summary=summary, result=result,
        )
        return execution, f"SUCCESS: {summary}"

    @staticmethod
    def _summarize(tool_id: str, result) -> str:
        if isinstance(result, dict):
            if result.get("relative_path"):
                kind = "folder" if tool_id == "create_folder" else "file"
                return f"Created {kind} '{result['relative_path']}'"
            if "entries" in result:
                return f"Listed {result.get('count', 0)} item(s)"
            if "matches" in result:
                return f"Found {result.get('count', 0)} match(es)"
            if "content" in result:
                return "Read file contents"
        return "Done"
