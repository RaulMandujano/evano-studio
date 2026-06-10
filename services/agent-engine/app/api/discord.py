"""Discord channel status endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from ..core.discord import get_discord_config
from ..db.session import get_session
from ..schemas.discord import DiscordStatusResponse
from ..services.discord_connector import discord_available

router = APIRouter(prefix="/discord", tags=["discord"])


@router.get("/status", response_model=DiscordStatusResponse, summary="Discord channel status")
def discord_status(
    request: Request,
    session: Session = Depends(get_session),
) -> DiscordStatusResponse:
    available, avail_msg = discord_available()
    config = get_discord_config(session)
    connector = getattr(request.app.state, "discord", None)
    state = getattr(connector, "state", "stopped") if connector is not None else "stopped"
    error = getattr(connector, "error", None) if connector is not None else None

    message = error or avail_msg
    if available and config.enabled and not config.configured:
        message = "Set the bot token, pick an agent, and add at least one allowed Discord user ID."
    elif available and config.enabled and config.configured and state in ("disabled", "stopped"):
        message = "Settings saved. Restart the backend to connect Discord."

    return DiscordStatusResponse(
        available=available,
        enabled=config.enabled,
        configured=config.configured,
        state=state,
        agent_id=config.agent_id,
        allowed_count=len(config.allowed_user_ids),
        message=message,
    )
