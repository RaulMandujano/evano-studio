"""Customer-service mixin: route a support agent to a customer channel.

The "Customer Service" tab is a guided setup: pick (or create) a support agent,
make sure it knows the business (knowledge base), connect a customer channel
(WhatsApp via QR login, Telegram/Discord/Slack via token), and bind the agent
to that channel so every incoming customer message is answered by it. Bindings
are OpenClaw's native routing — same mechanism as the per-agent Discord bots.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time

from . import metadata, process

logger = logging.getLogger("evano.agent_engine.openclaw")

# Customer-facing channels we offer in the guided setup (most businesses =
# WhatsApp; the rest are the popular alternatives).
SUPPORT_CHANNELS = ["whatsapp", "telegram", "discord", "slack", "signal"]

_AGENT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,60}$")

# `openclaw agents bindings` boots the Node CLI (~2s) — cache briefly, and
# invalidate whenever a binding changes (assign/unassign, Discord connect).
_BINDINGS_TTL = 15.0
_bindings_cache: dict = {"at": 0.0, "data": None}
_bindings_lock = threading.Lock()


def invalidate_bindings_cache() -> None:
    with _bindings_lock:
        _bindings_cache["at"] = 0.0
        _bindings_cache["data"] = None


class SupportMixin:
    def _all_bindings(self) -> list[dict]:
        """Every routing binding, normalized to {agent_id, channel, account_id}."""
        with _bindings_lock:
            fresh = _bindings_cache["data"] is not None and (time.monotonic() - _bindings_cache["at"]) < _BINDINGS_TTL
            if fresh:
                return list(_bindings_cache["data"])
        code, out, _ = process._run(["openclaw", "agents", "bindings", "--json"], timeout=30)
        rows: list[dict] = []
        if code == 0 and out:
            try:
                data = json.loads(out)
            except Exception:  # noqa: BLE001
                data = []
            entries = data if isinstance(data, list) else data.get("bindings") or []
            for row in entries:
                if not isinstance(row, dict):
                    continue
                match = row.get("match") or {}
                channel = (row.get("channel") or match.get("channel") or "").lower()
                if not channel:
                    continue
                rows.append({
                    "agent_id": row.get("agentId") or row.get("agent_id") or "",
                    "channel": channel,
                    "account_id": row.get("accountId") or row.get("account_id") or match.get("accountId") or "",
                })
            with _bindings_lock:
                _bindings_cache["at"] = time.monotonic()
                _bindings_cache["data"] = rows
        return list(rows)

    def customer_service_status(self) -> dict:
        """Everything the Customer Service tab needs, in one response."""
        agents_res = self.list_agents()
        if not agents_res.get("ok"):
            return {"ok": False, "message": agents_res.get("message") or "OpenClaw isn't ready.",
                    "gateway_running": False, "agents": [], "channels": [], "assignments": []}
        identities = self._config_identities()
        agents = [
            {
                "id": a["id"],
                "name": identities.get(a["id"], {}).get("name") or a.get("name") or a["id"],
                "emoji": identities.get(a["id"], {}).get("emoji") or "",
            }
            for a in agents_res.get("agents") or []
        ]

        channels_res = self.list_channels()
        by_slug = {c["slug"]: c for c in channels_res.get("channels") or []}
        channels = []
        for slug in SUPPORT_CHANNELS:
            info = by_slug.get(slug, {})
            channels.append({
                "slug": slug,
                "name": metadata._CHANNEL_NAMES.get(slug, slug.title()),
                "icon": metadata._CHANNEL_ICONS.get(slug, "💬"),
                # "login" = QR/in-app pairing (WhatsApp); "token" = paste a bot token.
                "connect": "login" if slug in metadata._LOGIN_CHANNELS else "token",
                "configured": bool(info.get("configured")),
            })

        support_slugs = set(SUPPORT_CHANNELS)
        assignments = [b for b in self._all_bindings() if b["channel"] in support_slugs]
        return {
            "ok": True,
            "message": "",
            "gateway_running": process._port_open(self._gateway_port()),
            "agents": agents,
            "channels": channels,
            "assignments": assignments,
        }

    def assign_support_agent(self, *, agent_id: str, channel: str) -> dict:
        """Route a channel's incoming messages to this agent (the CS activation)."""
        if process._which("openclaw") is None:
            return {"ok": False, "message": "Install OpenClaw first."}
        aid = (agent_id or "").strip()
        slug = (channel or "").strip().lower()
        if not _AGENT_ID_RE.match(aid):
            return {"ok": False, "message": "Invalid agent id."}
        if slug not in SUPPORT_CHANNELS:
            return {"ok": False, "message": f"'{channel}' isn't a supported customer channel."}

        code, out, err = process._run(
            ["openclaw", "agents", "bind", "--agent", aid, "--bind", slug, "--json"], timeout=30
        )
        if code != 0:
            return {"ok": False, "message": (err or out or "Couldn't route the channel to the agent.")[-400:]}
        invalidate_bindings_cache()
        from ._agents import invalidate_agents_cache

        invalidate_agents_cache()  # bindings count changed
        restarted = self._restart_gateway_if_running()
        logger.info("support assign agent=%s channel=%s restarted=%s", aid, slug, restarted)
        name = metadata._CHANNEL_NAMES.get(slug, slug)
        return {
            "ok": True,
            "message": f"Customer service is live — {name} messages now go to this agent."
            if restarted
            else f"{name} routed to this agent. It goes live when the gateway runs.",
        }

    def unassign_support_agent(self, *, agent_id: str, channel: str) -> dict:
        if process._which("openclaw") is None:
            return {"ok": False, "message": "Install OpenClaw first."}
        aid = (agent_id or "").strip()
        slug = (channel or "").strip().lower()
        if not _AGENT_ID_RE.match(aid) or not slug:
            return {"ok": False, "message": "Invalid agent or channel."}
        code, out, err = process._run(
            ["openclaw", "agents", "unbind", "--agent", aid, "--bind", slug, "--json"], timeout=30
        )
        if code != 0:
            return {"ok": False, "message": (err or out or "Couldn't remove the routing.")[-400:]}
        invalidate_bindings_cache()
        from ._agents import invalidate_agents_cache

        invalidate_agents_cache()
        self._restart_gateway_if_running()
        logger.info("support unassign agent=%s channel=%s", aid, slug)
        return {"ok": True, "message": "Routing removed — that channel no longer goes to this agent."}
