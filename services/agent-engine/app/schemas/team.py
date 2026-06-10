"""Schemas for saved agent teams (multi-agent workflows)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TeamStepInput(BaseModel):
    agent_id: str
    instruction: str = ""


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    steps: list[TeamStepInput] = Field(default_factory=list)
    working_file: Optional[str] = Field(default=None, max_length=120)


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    steps: Optional[list[TeamStepInput]] = None
    working_file: Optional[str] = Field(default=None, max_length=120)


class TeamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    steps: list[TeamStepInput] = Field(default_factory=list)
    working_file: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DeleteResponse(BaseModel):
    ok: bool
