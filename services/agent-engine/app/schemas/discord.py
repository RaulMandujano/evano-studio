"""Schemas for the Discord channel endpoints."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class DiscordStatusResponse(BaseModel):
    available: bool  # discord.py importable
    enabled: bool
    configured: bool  # token + agent + at least one allowed user
    state: str  # stopped | starting | running | error | disabled
    agent_id: Optional[int] = None
    allowed_count: int = 0
    message: Optional[str] = None
