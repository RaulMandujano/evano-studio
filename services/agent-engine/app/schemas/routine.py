"""Schemas for routines and the calendar."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ScheduleType = Literal["manual", "once", "daily", "weekly"]


class RoutineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    agent_id: int = 0  # built-in agent (unused when openclaw_agent_id/team_id is set)
    openclaw_agent_id: Optional[str] = None
    team_id: Optional[int] = None  # run a whole Team workflow on schedule
    prompt: str = Field(min_length=1)
    schedule_type: ScheduleType
    schedule_value: str = ""
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    is_enabled: bool = True


class RoutineUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    agent_id: Optional[int] = None
    openclaw_agent_id: Optional[str] = None
    team_id: Optional[int] = None
    prompt: Optional[str] = Field(default=None, min_length=1)
    schedule_type: Optional[ScheduleType] = None
    schedule_value: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    is_enabled: Optional[bool] = None


class RoutineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    agent_id: int
    openclaw_agent_id: Optional[str] = None
    team_id: Optional[int] = None
    prompt: str
    schedule_type: str
    schedule_value: str
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    is_enabled: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime


class RoutineRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    routine_id: int
    trigger: str
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    output: str
    document_path: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime


class RoutineDetail(RoutineRead):
    recent_runs: list[RoutineRunRead] = Field(default_factory=list)


class DeleteResponse(BaseModel):
    ok: bool


class CalendarEvent(BaseModel):
    routine_id: int
    routine_name: str
    type: str  # "scheduled" | "success" | "error" | "missed"
    time: datetime
    status: str
    message: Optional[str] = None


class CalendarEventsResponse(BaseModel):
    events: list[CalendarEvent] = Field(default_factory=list)
