"""Schemas for the live agent activity feed (the Office view)."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ActivityRead(BaseModel):
    id: int
    agent_id: str  # "openclaw:<slug>" or "builtin:<id>"
    agent_name: str
    kind: str  # chat | team | routine
    task: str
    status: str  # working | done | error
    started_at: str
    finished_at: Optional[str] = None
    note: str = ""


class ActivitySnapshotResponse(BaseModel):
    active: list[ActivityRead]
    recent: list[ActivityRead]
    generated_at: str
