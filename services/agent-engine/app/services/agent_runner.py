"""One place that runs an agent turn — shared by every channel.

Both the desktop HTTP chat and external channels (e.g. Discord) call
:func:`run_agent_turn`, so the agent behaves identically everywhere ("multi-
channel, one brain"). The turn:

1. builds the conversation (system prompt + optional RAG context + history + user),
2. runs the native tool-calling loop when the agent has tools (the model drives
   workspace-confined tools), falling back to the deterministic keyword router
   for models without tool support, and
3. otherwise replies with a plain chat completion.

All tool use stays deny-by-default and confined to the workspace.
"""

from __future__ import annotations

from sqlmodel import Session

from ..core.config import Settings
from ..schemas.agent import AgentChatResponse, ChatMessage, ChatSource
from .agent_loop import AgentLoop
from .chroma_service import ChromaService
from .knowledge_service import KnowledgeService
from .ollama_service import OllamaService
from .tool_orchestrator import AgentToolOrchestrator
from .tool_service import ToolService


def run_agent_turn(
    session: Session,
    settings: Settings,
    agent,
    message: str,
    history: list[ChatMessage] | None = None,
) -> AgentChatResponse:
    """Run a full agent turn and return the response. Never raises for normal
    failures (offline model, denied tool) — those become ok=False responses."""
    history = history or []
    ollama = OllamaService(settings)
    tools = ToolService(session=session, settings=settings)
    knowledge = KnowledgeService(session, settings, ChromaService(settings))

    messages, sources = build_chat_messages(agent, message, history, knowledge, settings)

    if agent.enabled_tools:
        looped = AgentLoop(ollama, tools, session).run(agent, messages, sources)
        if looped is not None:
            return looped

    orchestrated = AgentToolOrchestrator(ollama, tools).handle(agent, message, history)
    if orchestrated is not None:
        return orchestrated

    result = ollama.chat(agent.model_name, messages, agent.temperature)
    return AgentChatResponse(
        ok=result.ok,
        reply=result.reply,
        model=agent.model_name,
        latency_ms=result.latency_ms,
        message=result.message,
        sources=sources,
    )


def build_chat_messages(
    agent, message: str, history: list[ChatMessage], knowledge: KnowledgeService, settings: Settings
):
    """Build (messages, sources): system prompt + RAG context + history + user."""
    messages: list[dict] = []
    if agent.system_prompt:
        messages.append({"role": "system", "content": agent.system_prompt})

    sources: list[ChatSource] | None = None
    if agent.knowledge_enabled:
        sources = _augment_with_knowledge(messages, message, knowledge, settings)

    messages.extend({"role": m.role, "content": m.content} for m in history)
    messages.append({"role": "user", "content": message})
    return messages, sources


def _augment_with_knowledge(
    messages: list[dict], query: str, knowledge: KnowledgeService, settings: Settings
) -> list[ChatSource] | None:
    """Search the KB and append a bounded context message. Never raises."""
    try:
        hits = knowledge.search(query, top_k=settings.rag_top_k)
    except Exception:  # noqa: BLE001 - RAG must never break chat
        return None
    if not hits:
        return None

    context_parts: list[str] = []
    sources: list[ChatSource] = []
    total = 0
    budget = settings.rag_max_context_chars
    for hit in hits:
        text = (hit.text or "").strip()
        if not text:
            continue
        remaining = budget - total
        if remaining <= 0:
            break
        snippet = text[:remaining]
        label = hit.title or hit.file_name or "source"
        context_parts.append(f"[{label}]\n{snippet}")
        sources.append(
            ChatSource(
                title=hit.title, file_name=hit.file_name, snippet=text[:200], distance=hit.distance
            )
        )
        total += len(snippet)

    if not context_parts:
        return None

    context = "\n\n".join(context_parts)
    messages.append(
        {
            "role": "system",
            "content": (
                "Use the following local knowledge base context to help answer the "
                "user's question. If it isn't relevant, answer normally.\n\n"
                f"{context}"
            ),
        }
    )
    return sources
