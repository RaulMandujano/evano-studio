"""Discord channel connector — bridges Discord messages to a local agent.

This is one "channel" in front of the shared agent brain (see agent_runner).
Design and safety:
- Off by default; runs only when configured + enabled in settings.
- Runs in its own thread with its own asyncio loop, so it never blocks the API.
- ``discord.py`` is imported lazily; if it isn't installed the connector reports
  ``available=False`` and the rest of the app is unaffected.
- Deny-by-default: replies ONLY to users on the configured allowlist.
- The agent's tools remain workspace-confined and permission-gated — Discord
  does NOT grant any extra power. No shell, no computer control.
"""

from __future__ import annotations

import asyncio
import logging
import threading

from sqlmodel import Session

from ..core.config import Settings
from ..core.discord import DiscordConfig, get_discord_config
from .agent_runner import run_agent_turn

logger = logging.getLogger("evano.agent_engine.discord")

_MAX_DISCORD_LEN = 1900  # Discord hard limit is 2000; leave headroom.


def discord_available() -> tuple[bool, str | None]:
    """Whether the discord.py library can be imported."""
    try:
        import discord  # noqa: F401

        return True, None
    except Exception as exc:  # noqa: BLE001
        return False, f"discord.py is not installed ({exc}). Install it with: pip install discord.py"


def _chunks(text: str) -> list[str]:
    text = text or "(no reply)"
    return [text[i : i + _MAX_DISCORD_LEN] for i in range(0, len(text), _MAX_DISCORD_LEN)] or ["(no reply)"]


class DiscordConnector:
    """Manages the lifecycle of a Discord client bound to one agent."""

    def __init__(self, engine, settings: Settings) -> None:
        self._engine = engine
        self._settings = settings
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._client = None
        self._config: DiscordConfig | None = None
        self.state = "stopped"  # stopped | starting | running | error | disabled
        self.error: str | None = None

    # ---- lifecycle ------------------------------------------------------- #

    def start(self) -> None:
        """Start the connector if it's enabled and configured. Never raises."""
        with Session(self._engine) as session:
            config = get_discord_config(session)

        if not config.enabled:
            self.state = "disabled"
            return
        if not config.configured:
            self.state = "error"
            self.error = "Discord is enabled but not fully configured (token, agent, and allowed users)."
            logger.warning("discord: %s", self.error)
            return
        ok, msg = discord_available()
        if not ok:
            self.state = "error"
            self.error = msg
            logger.warning("discord: %s", msg)
            return

        self._config = config
        self.state = "starting"
        self.error = None
        self._thread = threading.Thread(target=self._run, name="evano-discord", daemon=True)
        self._thread.start()
        logger.info("discord: connector starting (agent=%s, allow=%d users)",
                    config.agent_id, len(config.allowed_user_ids))

    def stop(self) -> None:
        client, loop = self._client, self._loop
        if client is not None and loop is not None:
            try:
                asyncio.run_coroutine_threadsafe(client.close(), loop)
            except Exception:  # noqa: BLE001
                pass
        self.state = "stopped"

    # ---- worker thread --------------------------------------------------- #

    def _run(self) -> None:
        import discord

        config = self._config
        assert config is not None

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop

        intents = discord.Intents.default()
        intents.message_content = True  # needs "Message Content Intent" enabled in the dev portal
        client = discord.Client(intents=intents)
        self._client = client

        @client.event
        async def on_ready() -> None:  # noqa: ANN202
            self.state = "running"
            logger.info("discord: connected as %s", client.user)

        @client.event
        async def on_message(message) -> None:  # noqa: ANN001, ANN202
            if client.user is not None and message.author.id == client.user.id:
                return  # ignore our own messages
            if not config.is_allowed(message.author.id):
                logger.info("discord: ignored message from non-allowlisted user %s", message.author.id)
                return
            content = (message.content or "").strip()
            if not content:
                return
            try:
                reply = await asyncio.to_thread(self._handle, content)
            except Exception as exc:  # noqa: BLE001
                logger.exception("discord: turn failed")
                reply = f"Error: {exc}"
            try:
                async with message.channel.typing():
                    for chunk in _chunks(reply):
                        await message.channel.send(chunk)
            except Exception:  # noqa: BLE001
                logger.exception("discord: failed to send reply")

        try:
            loop.run_until_complete(client.start(config.token))
        except Exception as exc:  # noqa: BLE001
            self.state = "error"
            self.error = str(exc)
            logger.warning("discord: client stopped: %s", exc)
        finally:
            try:
                loop.run_until_complete(client.close())
            except Exception:  # noqa: BLE001
                pass
            loop.close()
            if self.state not in ("error",):
                self.state = "stopped"

    def _handle(self, content: str) -> str:
        """Run one agent turn for a Discord message (own DB session)."""
        from ..db.models import Agent

        assert self._config is not None
        with Session(self._engine) as session:
            agent = session.get(Agent, self._config.agent_id)
            if agent is None:
                return "The configured agent no longer exists. Pick another in Settings."
            if not agent.is_enabled:
                return "That agent is disabled. Enable it in Evano Studio."
            response = run_agent_turn(session, self._settings, agent, content)
            return response.reply or response.message or "(no reply)"
