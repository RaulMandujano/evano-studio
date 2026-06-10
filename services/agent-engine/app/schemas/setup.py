"""Schemas for the Easy Start setup-status endpoint.

A single aggregated view of every subsystem the onboarding wizard checks, so the
desktop can render the setup checklist from one request. Each sub-object mirrors
the dedicated per-subsystem endpoints; this is a convenience aggregator.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SetupBackend(BaseModel):
    running: bool = True
    version: str
    uptime_seconds: float


class SetupOllama(BaseModel):
    status: str  # running | offline | error
    reachable: bool
    version: Optional[str] = None
    recommended_model: str
    recommended_available: bool


class SetupModels(BaseModel):
    count: int = 0
    installed: list[str] = Field(default_factory=list)  # names only (not sensitive)


class SetupSqlite(BaseModel):
    connected: bool
    file_exists: bool
    table_count: int = 0
    path: Optional[str] = None


class SetupWorkspace(BaseModel):
    configured: bool
    path: str
    exists: bool
    ready: bool
    missing_subdirs: list[str] = Field(default_factory=list)


class SetupChroma(BaseModel):
    available: bool
    document_count: int = 0
    message: Optional[str] = None


class SetupComfyUI(BaseModel):
    enabled: bool
    reachable: bool
    message: Optional[str] = None


class SetupAgents(BaseModel):
    count: int = 0
    with_tools: int = 0  # agents that have at least one tool enabled


class SetupStatusResponse(BaseModel):
    backend: SetupBackend
    ollama: SetupOllama
    models: SetupModels
    sqlite: SetupSqlite
    workspace: SetupWorkspace
    chromadb: SetupChroma
    comfyui: SetupComfyUI
    agents: SetupAgents
