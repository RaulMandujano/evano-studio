"""Schemas for the tools endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ToolParamRead(BaseModel):
    name: str
    type: str
    required: bool
    description: str


class ToolSpecRead(BaseModel):
    id: str
    name: str
    description: str
    category: str
    parameters: list[ToolParamRead] = Field(default_factory=list)
    requires_approval: bool = False


class ToolTestRequest(BaseModel):
    tool_id: str
    params: dict[str, Any] = Field(default_factory=dict)
    # Optional: run as a specific agent (enforces that agent's enabled tools).
    agent_id: Optional[int] = None


class ToolTestResponse(BaseModel):
    ok: bool
    result: Any = None
    message: Optional[str] = None


class AgentToolsUpdate(BaseModel):
    enabled_tools: list[str]


class ToolExecutionLogRead(BaseModel):
    """A single logged tool execution (metadata only — no file contents)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None
    tool_id: str
    tool_name: str
    source: str
    action: str
    status: str
    detail: Optional[str] = None
    created_at: datetime


class ToolExecution(BaseModel):
    """Summary of a tool the agent ran during a chat turn (returned to the UI)."""

    tool_id: str
    tool_name: str
    ok: bool
    summary: str
    result: Any = None
    message: Optional[str] = None
