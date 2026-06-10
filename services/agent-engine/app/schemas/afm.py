"""Schemas for AFM — Agent File Management."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class AfmAgent(BaseModel):
    agent_id: str
    name: str
    emoji: str = ""
    workspace: str = ""
    target: str = ""
    managed: bool = False


class AfmTeam(BaseModel):
    team_id: Optional[int] = None
    name: str
    folder: str
    exists: bool = False
    members: list[str] = []


class AfmStatusResponse(BaseModel):
    ok: bool
    message: str = ""
    root: str
    is_default: bool
    configured: bool
    agents: list[AfmAgent] = []
    teams: list[AfmTeam] = []


class AfmApplyRequest(BaseModel):
    root: Optional[str] = None  # None/empty → the Evano workspace default


class AfmApplyResult(BaseModel):
    ok: bool
    message: str = ""
    moved: list[str] = []
    skipped: list[str] = []


class AfmArchiveStep(BaseModel):
    agent_id: str = ""
    output: str = ""


class AfmArchiveRequest(BaseModel):
    team_name: str
    steps: list[AfmArchiveStep] = []
    final: str = ""


class AfmArchiveResult(BaseModel):
    ok: bool
    folder: str = ""
    message: str = ""
