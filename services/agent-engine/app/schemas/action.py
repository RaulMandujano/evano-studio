"""Schemas for the approval (pending action) flow."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .tool import ToolExecution


class PendingActionRead(BaseModel):
    """A proposed computer-control action awaiting human approval."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None
    tool_id: str
    tool_name: str
    summary: str
    preview: str
    status: str
    created_at: datetime


class ActionResolveResponse(BaseModel):
    ok: bool
    status: str  # done | denied | error | not_found | already_resolved
    execution: Optional[ToolExecution] = None
    message: Optional[str] = None
