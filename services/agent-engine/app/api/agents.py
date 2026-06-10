"""Agent CRUD and chat endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from ..core.config import Settings
from ..core.errors import AppError
from ..agent_templates import list_templates
from ..schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    AgentCreate,
    AgentGenerateImageRequest,
    AgentImagePromptRequest,
    AgentImagePromptResponse,
    AgentRead,
    AgentTemplate,
    AgentUpdate,
    DeleteResponse,
)
from ..schemas.image import ImageGenerateRequest, ImageGenerationRead
from ..schemas.tool import AgentToolsUpdate
from ..services.activity_service import track
from ..services.agent_runner import run_agent_turn
from ..services.agent_service import AgentService
from ..services.image_service import ImageService
from ..services.ollama_service import OllamaService
from ..tools.registry import tool_exists
from ..db.session import get_session
from .deps import (
    get_agent_service,
    get_app_settings,
    get_image_service,
    get_ollama_service,
)

router = APIRouter(prefix="/agents", tags=["agents"])
logger = logging.getLogger("evano.agent_engine.agents")


def _get_or_404(service: AgentService, agent_id: int):
    agent = service.get_agent(agent_id)
    if agent is None:
        raise AppError("Agent not found.", status_code=status.HTTP_404_NOT_FOUND, code="not_found")
    return agent


@router.get("", response_model=list[AgentRead], summary="List agents")
def list_agents(service: AgentService = Depends(get_agent_service)) -> list[AgentRead]:
    return [AgentRead.model_validate(a) for a in service.list_agents()]


# NOTE: declared before "/{agent_id}" so "templates" isn't read as an agent id.
@router.get("/templates", response_model=list[AgentTemplate], summary="Ready-made agent templates")
def get_agent_templates() -> list[AgentTemplate]:
    return list_templates()


@router.post(
    "",
    response_model=AgentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an agent",
)
def create_agent(
    payload: AgentCreate,
    service: AgentService = Depends(get_agent_service),
) -> AgentRead:
    return AgentRead.model_validate(service.create_agent(payload))


@router.get("/{agent_id}", response_model=AgentRead, summary="Get an agent")
def get_agent(
    agent_id: int,
    service: AgentService = Depends(get_agent_service),
) -> AgentRead:
    return AgentRead.model_validate(_get_or_404(service, agent_id))


@router.put("/{agent_id}", response_model=AgentRead, summary="Update an agent")
def update_agent(
    agent_id: int,
    payload: AgentUpdate,
    service: AgentService = Depends(get_agent_service),
) -> AgentRead:
    _get_or_404(service, agent_id)
    updated = service.update_agent(agent_id, payload)
    assert updated is not None  # guaranteed by the 404 check above
    return AgentRead.model_validate(updated)


@router.delete("/{agent_id}", response_model=DeleteResponse, summary="Delete an agent")
def delete_agent(
    agent_id: int,
    service: AgentService = Depends(get_agent_service),
) -> DeleteResponse:
    if not service.delete_agent(agent_id):
        raise AppError("Agent not found.", status_code=status.HTTP_404_NOT_FOUND, code="not_found")
    return DeleteResponse(ok=True)


@router.put("/{agent_id}/tools", response_model=AgentRead, summary="Set an agent's enabled tools")
def set_agent_tools(
    agent_id: int,
    payload: AgentToolsUpdate,
    service: AgentService = Depends(get_agent_service),
) -> AgentRead:
    _get_or_404(service, agent_id)
    unknown = [t for t in payload.enabled_tools if not tool_exists(t)]
    if unknown:
        raise AppError(f"Unknown tools: {', '.join(unknown)}", status_code=400, code="unknown_tool")
    updated = service.update_agent(agent_id, AgentUpdate(enabled_tools=payload.enabled_tools))
    assert updated is not None
    return AgentRead.model_validate(updated)


_IMAGE_PROMPT_SYSTEM = (
    "You are an expert prompt engineer for text-to-image models. Turn the user's "
    "idea into ONE vivid, detailed image prompt covering subject, style, lighting, "
    "composition, and mood. Output ONLY the prompt text — no quotes, no preamble, "
    "no explanation."
)


@router.post(
    "/{agent_id}/image-prompt",
    response_model=AgentImagePromptResponse,
    summary="Have an agent craft an image prompt",
)
def agent_image_prompt(
    agent_id: int,
    payload: AgentImagePromptRequest,
    service: AgentService = Depends(get_agent_service),
    ollama: OllamaService = Depends(get_ollama_service),
) -> AgentImagePromptResponse:
    """Use the agent's local model to write a strong image prompt. Text only —
    this does not generate an image."""
    agent = _get_or_404(service, agent_id)
    if not agent.is_enabled:
        return AgentImagePromptResponse(
            ok=False, model=agent.model_name, message="This agent is disabled."
        )

    idea = payload.idea.strip()
    if payload.style.strip():
        idea += f"\nStyle: {payload.style.strip()}."
    if payload.details.strip():
        idea += f"\nDetails: {payload.details.strip()}."

    messages = [
        {"role": "system", "content": _IMAGE_PROMPT_SYSTEM},
        {"role": "user", "content": idea},
    ]
    result = ollama.chat(agent.model_name, messages, agent.temperature)
    if not result.ok:
        return AgentImagePromptResponse(
            ok=False, model=agent.model_name, latency_ms=result.latency_ms, message=result.message
        )
    return AgentImagePromptResponse(
        ok=True,
        prompt=(result.reply or "").strip(),
        model=agent.model_name,
        latency_ms=result.latency_ms,
    )


@router.post(
    "/{agent_id}/generate-image",
    response_model=ImageGenerationRead,
    summary="Generate an image via an image-enabled agent (local ComfyUI)",
)
def agent_generate_image(
    agent_id: int,
    payload: AgentGenerateImageRequest,
    service: AgentService = Depends(get_agent_service),
    image_service: ImageService = Depends(get_image_service),
) -> ImageGenerationRead:
    """Generate an image from a user-approved prompt. Requires the agent to be
    image-enabled; ComfyUI being disabled/unreachable is reported as a failed
    record (not an exception). Nothing generates without this explicit call."""
    agent = _get_or_404(service, agent_id)
    if not agent.is_enabled:
        raise AppError("This agent is disabled.", status_code=409, code="agent_disabled")
    if not agent.image_enabled:
        raise AppError(
            "This agent isn't allowed to generate images. Enable image generation in the agent settings.",
            status_code=403,
            code="image_not_enabled",
        )
    record = image_service.generate(
        ImageGenerateRequest(
            prompt=payload.prompt,
            negative_prompt=payload.negative_prompt,
            workflow_name=payload.workflow_name,
            agent_id=agent.id,
        )
    )
    return ImageGenerationRead.model_validate(record)


@router.post("/{agent_id}/chat", response_model=AgentChatResponse, summary="Chat with an agent")
def chat_with_agent(
    agent_id: int,
    payload: AgentChatRequest,
    service: AgentService = Depends(get_agent_service),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> AgentChatResponse:
    """Run an agent turn. The shared runner handles the native tool-calling loop,
    the deterministic fallback, RAG, and plain chat (see services/agent_runner)."""
    agent = _get_or_404(service, agent_id)
    if not agent.is_enabled:
        return AgentChatResponse(
            ok=False,
            model=agent.model_name,
            message="This agent is disabled. Enable it to chat.",
        )
    with track(
        agent_id=f"builtin:{agent.id}", agent_name=agent.name, kind="chat", task="Answering a chat"
    ) as outcome:
        result = run_agent_turn(session, settings, agent, payload.message, payload.history)
        outcome["ok"] = result.ok
        if not result.ok:
            outcome["note"] = result.message or ""
    return result
