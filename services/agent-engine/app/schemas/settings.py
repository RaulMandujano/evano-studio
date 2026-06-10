"""Schemas for the settings endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SettingsResponse(BaseModel):
    """All application settings as a flat key/value map."""

    settings: dict[str, str] = Field(default_factory=dict)


class SettingsUpdateRequest(BaseModel):
    """A set of settings to create or update (merged into existing settings)."""

    settings: dict[str, str]
