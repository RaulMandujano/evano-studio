"""Schemas for the agent endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .action import PendingActionRead
from .tool import ToolExecution


class AgentBase(BaseModel):
    # Allow the `model_name` field (avoids pydantic's protected "model_" warning)
    # and let read models validate from ORM objects.
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    system_prompt: str = ""
    model_name: str = Field(min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    is_enabled: bool = True
    knowledge_enabled: bool = False
    image_enabled: bool = False
    enabled_tools: list[str] = Field(default_factory=list)


class AgentCreate(AgentBase):
    """Fields required to create an agent."""


class AgentUpdate(BaseModel):
    """Partial update — only provided fields are changed."""

    model_config = ConfigDict(protected_namespaces=())

    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_name: Optional[str] = Field(default=None, min_length=1)
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    is_enabled: Optional[bool] = None
    knowledge_enabled: Optional[bool] = None
    image_enabled: Optional[bool] = None
    enabled_tools: Optional[list[str]] = None


class AgentRead(AgentBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1)
    # Optional prior turns so the chat panel can keep context. No tools/RAG yet.
    history: list[ChatMessage] = Field(default_factory=list)


class ChatSource(BaseModel):
    """A knowledge-base snippet used to ground a response (RAG)."""

    title: Optional[str] = None
    file_name: Optional[str] = None
    snippet: str
    distance: Optional[float] = None


class AgentChatResponse(BaseModel):
    ok: bool
    reply: Optional[str] = None
    model: str
    latency_ms: Optional[int] = None
    message: Optional[str] = None
    # Knowledge-base snippets used (when the agent has knowledge_enabled).
    sources: Optional[list[ChatSource]] = None
    # Set when the message was handled by a deterministic tool action (instead
    # of the language model). The reply describes the action's result.
    tool_execution: Optional[ToolExecution] = None
    # All tool actions run during this turn (the agentic loop may run several).
    tool_executions: Optional[list[ToolExecution]] = None
    # Set when the agent proposed a sensitive action that needs your approval
    # before it will run (computer control). Approve/deny via /actions/{id}.
    pending_action: Optional[PendingActionRead] = None


class AgentImagePromptRequest(BaseModel):
    """Ask an agent to craft an image-generation prompt from an idea."""

    idea: str = Field(min_length=1)
    style: str = ""
    details: str = ""


class AgentImagePromptResponse(BaseModel):
    ok: bool
    prompt: str = ""
    model: str
    latency_ms: Optional[int] = None
    message: Optional[str] = None


class AgentGenerateImageRequest(BaseModel):
    """Send a (user-approved) prompt to ComfyUI via an image-enabled agent."""

    prompt: str = Field(min_length=1)
    negative_prompt: str = ""
    workflow_name: Optional[str] = None


class AgentTemplate(BaseModel):
    """A ready-made starting point for creating an agent (for non-tech users)."""

    model_config = ConfigDict(protected_namespaces=())

    id: str
    name: str
    icon: str = ""
    description: str = ""
    system_prompt: str = ""
    temperature: float = 0.7
    knowledge_enabled: bool = False
    enabled_tools: list[str] = Field(default_factory=list)
    # Optional suggested model; when omitted the UI uses the installed default.
    model_name: Optional[str] = None


class DeleteResponse(BaseModel):
    ok: bool