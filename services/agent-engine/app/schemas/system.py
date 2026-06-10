"""Schemas for the meta/system endpoints (health, version, system info)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FeatureFlags(BaseModel):
    """Which optional subsystems are currently available.

    All are ``False`` for now — they are added in later phases. The desktop app
    can use these to drive its dashboard status cards.
    """

    database: bool = Field(default=False, description="Local SQLite database")
    ollama: bool = Field(default=False, description="Local Ollama runtime")
    chromadb: bool = Field(default=False, description="Local ChromaDB knowledge base")
    comfyui: bool = Field(default=False, description="Optional local ComfyUI image generation")


class HealthResponse(BaseModel):
    """Liveness/health response."""

    status: str = Field(default="ok", examples=["ok"])
    service: str
    version: str
    uptime_seconds: float


class VersionResponse(BaseModel):
    """Service version information."""

    name: str
    version: str
    environment: str


class SystemInfoResponse(BaseModel):
    """Non-sensitive runtime/system information for diagnostics."""

    service: str
    version: str
    environment: str
    python_version: str
    platform: str
    timestamp: datetime
    uptime_seconds: float
    features: FeatureFlags
    workspace_path: str
