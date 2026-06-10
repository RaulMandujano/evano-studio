"""Schemas for the Ollama integration endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class OllamaModel(BaseModel):
    """A locally installed Ollama model (subset of Ollama's tag info)."""

    name: str
    size_bytes: Optional[int] = None
    modified_at: Optional[str] = None
    family: Optional[str] = None
    parameter_size: Optional[str] = None
    digest: Optional[str] = None


class OllamaStatusResponse(BaseModel):
    """Whether the local Ollama runtime is reachable and what it offers."""

    status: Literal["running", "offline", "error"]
    reachable: bool
    base_url: str
    version: Optional[str] = None
    model_count: int = 0
    recommended_model: str
    recommended_available: bool = False
    message: Optional[str] = None


class OllamaModelsResponse(BaseModel):
    """The list of locally installed models (empty when Ollama is unreachable)."""

    reachable: bool
    models: list[OllamaModel] = Field(default_factory=list)
    count: int = 0
    recommended_model: str
    recommended_available: bool = False
    message: Optional[str] = None


class ChatTestRequest(BaseModel):
    """Request body for a one-shot chat test against a local model."""

    model: Optional[str] = None
    prompt: str = "Reply with a short, friendly hello."


class ChatTestResponse(BaseModel):
    """Result of a chat test. ``ok`` is False (with a message) when it fails."""

    ok: bool
    model: Optional[str] = None
    reply: Optional[str] = None
    latency_ms: Optional[int] = None
    message: Optional[str] = None


class RecommendedModel(BaseModel):
    """A curated, free local model the user can choose to install."""

    model: str  # the tag to pull (e.g. "llama3.2:3b")
    name: str
    category: str
    notes: str
    family: Optional[str] = None
    size_estimate: Optional[str] = None  # best-effort, e.g. "~4.1 GB"
    min_ram: Optional[str] = None  # best-effort, e.g. "8 GB"
    min_ram_gb: Optional[float] = None  # numeric, drives fit scoring
    size_gb: Optional[float] = None  # download size, numeric
    recommended: bool = False
    installed: bool = False
    # How well it fits THIS machine: great | good | tight | too_big | unknown
    fit: str = "unknown"
    fit_reason: str = ""


class HardwareInfo(BaseModel):
    """What this machine can run (best-effort probe, never fails)."""

    platform: str = ""
    ram_gb: float = 0
    cpu_cores: int = 0
    chip: Optional[str] = None
    unified_memory: bool = False


class RecommendedModelsResponse(BaseModel):
    """Curated recommendations scored against this machine's hardware."""

    reachable: bool
    recommended_model: str
    models: list[RecommendedModel] = Field(default_factory=list)
    message: Optional[str] = None
    hardware: Optional[HardwareInfo] = None
    best_pick: Optional[str] = None  # the model tag that fits this machine best


class PullRequest(BaseModel):
    """Request to start pulling (installing) a model."""

    model: str


# pending  = accepted, thread starting
# downloading = in progress
# success  = installed
# error    = failed (see message)
# idle     = no pull tracked for this model
PullState = Literal["idle", "pending", "downloading", "success", "error"]


class PullStatusResponse(BaseModel):
    """Progress of a model pull. Polled by the desktop app."""

    model: str
    state: PullState
    percent: float = 0.0
    completed_bytes: int = 0
    total_bytes: int = 0
    detail: Optional[str] = None  # latest status text from Ollama
    message: Optional[str] = None  # error / info message
    updated_at: Optional[datetime] = None
