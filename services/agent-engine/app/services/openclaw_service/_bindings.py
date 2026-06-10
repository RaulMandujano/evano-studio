"""Bindings mixin: give an agent its own Discord bot, the easy way.

OpenClaw routes incoming messages with bindings (channel[:accountId] → agent).
We give every agent its OWN Discord channel account ("agent-<id>") so several
agents can live in one Discord server as separate bots — the user's remote
"workspace" where the whole team is reachable.

One Evano click runs the three CLI steps a technical user would do by hand:
``channels add`` (register the bot token) + ``agents bind`` + gateway restart.
"""

from __future__ import annotations

import json
import logging
import re

from . import process

logger = logging.getLogger("evano.agent_engine.openclaw")

_AGENT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,60}$")


class BindingsMixin:
    @staticmethod
    def _discord_account_id(agent_id: str) -> str:
        """One Discord account per agent so each agent is its own bot."""
        return f"agent-{agent_id}"

    def _discord_binding(self, agent_id: str) -> dict | None:
        """Find this agent's Discord binding in OpenClaw's routing table."""
        code, out, _ = process._run(
            ["openclaw", "agents", "bindings", "--agent", agent_id, "--json"], timeout=30
        )
        if code != 0 or not out:
            return None
        try:
            data = json.loads(out)
        except Exception:  # noqa: BLE001
            return None
        rows = data if isinstance(data, list) else data.get("bindings") or []
        for row in rows:
            if not isinstance(row, dict):
                continue
            channel = (row.get("channel") or (row.get("match") or {}).get("channel") or "").lower()
            if channel == "discord":
                account = (
                    row.get("accountId")
                    or row.get("account_id")
                    or (row.get("match") or {}).get("accountId")
                    or ""
                )
                return {"channel": "discord", "account_id": account}
        return None

    def _restart_gateway_if_running(self) -> bool:
        """Channel/binding changes only take effect after a gateway restart."""
        if not process._port_open(self._gateway_port()):
            return False
        self.gateway_stop()
        result = self.gateway_start()
        return bool(result.get("running"))

    def agent_discord_status(self, agent_id: str) -> dict:
        if process._which("openclaw") is None:
            return {"ok": False, "connected": False, "account_id": "", "gateway_running": False,
                    "message": "Install OpenClaw first."}
        aid = (agent_id or "").strip()
        if not _AGENT_ID_RE.match(aid):
            return {"ok": False, "connected": False, "account_id": "", "gateway_running": False,
                    "message": "Invalid agent id."}
        binding = self._discord_binding(aid)
        return {
            "ok": True,
            "connected": binding is not None,
            "account_id": (binding or {}).get("account_id", ""),
            "gateway_running": process._port_open(self._gateway_port()),
            "message": "",
        }

    def connect_agent_discord(self, *, agent_id: str, bot_token: str) -> dict:
        """Register the agent's bot token and route its Discord messages to it."""
        if process._which("openclaw") is None:
            return {"ok": False, "message": "Install OpenClaw first."}
        aid = (agent_id or "").strip()
        if not _AGENT_ID_RE.match(aid):
            return {"ok": False, "message": "Invalid agent id."}
        token = (bot_token or "").strip()
        if not token:
            return {"ok": False, "message": "Paste the Discord bot token first."}

        account = self._discord_account_id(aid)
        # 1) Register (or update) the bot token as this agent's own account.
        code, out, err = process._run(
            ["openclaw", "channels", "add", "--channel", "discord",
             "--account", account, "--bot-token", token, "--name", aid],
            timeout=60,
        )
        if code != 0:
            logger.info("openclaw discord connect agent=%s step=channels-add ok=False", aid)
            return {"ok": False, "message": (err or out or "Couldn't save the bot token.")[-400:]}

        # 2) Route Discord messages on that account to this agent.
        code, out, err = process._run(
            ["openclaw", "agents", "bind", "--agent", aid, "--bind", f"discord:{account}", "--json"],
            timeout=30,
        )
        if code != 0:
            logger.info("openclaw discord connect agent=%s step=bind ok=False", aid)
            return {"ok": False, "message": (err or out or "Couldn't link the bot to the agent.")[-400:]}

        # 3) Reload the gateway so the bot actually comes online.
        restarted = self._restart_gateway_if_running()
        logger.info("openclaw discord connect agent=%s ok=True restarted=%s", aid, restarted)  # token never logged
        return {
            "ok": True,
            "message": "Connected! The bot comes online when the gateway runs."
            if not restarted
            else "Connected! Your agent is now live on Discord.",
        }

    def disconnect_agent_discord(self, agent_id: str) -> dict:
        if process._which("openclaw") is None:
            return {"ok": False, "message": "Install OpenClaw first."}
        aid = (agent_id or "").strip()
        if not _AGENT_ID_RE.match(aid):
            return {"ok": False, "message": "Invalid agent id."}
        account = self._discord_account_id(aid)

        code, out, err = process._run(
            ["openclaw", "agents", "unbind", "--agent", aid, "--bind", f"discord:{account}", "--json"],
            timeout=30,
        )
        if code != 0:
            return {"ok": False, "message": (err or out or "Couldn't unlink the agent.")[-400:]}
        # Remove the bot account too (and its stored token).
        process._run(
            ["openclaw", "channels", "remove", "--channel", "discord", "--account", account, "--delete"],
            timeout=30,
        )
        self._restart_gateway_if_running()
        logger.info("openclaw discord disconnect agent=%s ok=True", aid)
        return {"ok": True, "message": "Disconnected — the bot is no longer linked to this agent."}
