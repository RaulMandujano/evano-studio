"""Schemas for the logs and support-bundle endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LogEntry(BaseModel):
    # Ignore extra fields (the store also carries a numeric levelno).
    model_config = ConfigDict(extra="ignore")

    timestamp: str
    level: str
    area: str
    logger: str
    message: str


class LogsResponse(BaseModel):
    entries: list[LogEntry] = Field(default_factory=list)


class SupportBundleResponse(BaseModel):
    path: str
    bundle: dict[str, Any]
