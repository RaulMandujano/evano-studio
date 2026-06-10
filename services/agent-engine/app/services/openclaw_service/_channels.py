"""Channels mixin: list and connect OpenClaw messaging channels."""
from __future__ import annotations

import json
import logging

from . import metadata, process

logger = logging.getLogger("evano.agent_engine.openclaw")


class ChannelsMixin:
    def list_channels(self) -> dict:
        """List OpenClaw's installable/configured chat channels (WhatsApp, Discord,
        Telegram, …) with their connection state."""
        if process._which("openclaw") is None:
            return {"ok": False, "message": "Install OpenClaw first.", "channels": []}
        code, out, err = process._run(["openclaw", "channels", "list", "--all", "--json"], timeout=30)
        if code != 0:
            return {"ok": False, "message": (err or out or "Couldn't list channels.")[-300:], "channels": []}
        try:
            data = json.loads(out)
        except Exception:  # noqa: BLE001
            return {"ok": False, "message": "Couldn't read the channel list.", "channels": []}
        chat = data.get("chat") or {}
        channels = []
        for slug, info in chat.items():
            accounts = info.get("accounts") or []
            channels.append({
                "slug": slug,
                "name": metadata._CHANNEL_NAMES.get(slug, slug.replace("-", " ").title()),
                "icon": metadata._CHANNEL_ICONS.get(slug, "💬"),
                "connect": "login" if slug in metadata._LOGIN_CHANNELS else "token",
                "can_add": slug in metadata._ADD_ALLOWED,
                "installed": bool(info.get("installed")),
                "configured": len(accounts) > 0,
                "popular": slug in metadata._POPULAR_CHANNELS,
            })
        channels.sort(key=lambda c: (not c["popular"], not c["configured"], c["name"].lower()))
        return {"ok": True, "message": "", "channels": channels}

    def add_channel(self, *, channel: str, token: str) -> dict:
        """Connect a channel non-interactively with a token / bot token. The token
        is passed straight to OpenClaw and never logged."""
        if process._which("openclaw") is None:
            return {"ok": False, "message": "Install OpenClaw first."}
        slug = (channel or "").strip().lower()
        if slug not in metadata._ADD_ALLOWED:
            return {"ok": False, "message": f"'{channel}' can't be connected with a token here."}
        if slug in metadata._LOGIN_CHANNELS:
            return {"ok": False, "message": f"{metadata._CHANNEL_NAMES.get(slug, slug)} needs an in-app login — open the Dashboard to connect it."}
        if not token or not token.strip():
            return {"ok": False, "message": "Paste the channel token to connect."}
        code, out, err = process._run(
            ["openclaw", "channels", "add", "--channel", slug, "--token", token.strip()],
            timeout=60,
        )
        ok = code == 0
        logger.info("openclaw channels add channel=%s ok=%s", slug, ok)  # never logs the token
        return {"ok": ok, "message": "Channel connected." if ok else (err or out or "Couldn't connect.")[-400:]}
