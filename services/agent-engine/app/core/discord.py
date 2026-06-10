"""Discord channel configuration (stored in the local DB, runtime-editable).

Off by default. All values live in ``app_settings`` so they can be set from the
desktop without code changes. Privacy/safety: the bot only replies to users on
an explicit allowlist (deny-by-default, matching the rest of Evano).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlmodel import Session

# app_settings keys
KEY_ENABLED = "discord_enabled"
KEY_TOKEN = "discord_bot_token"
KEY_AGENT_ID = "discord_agent_id"
KEY_ALLOWED_USERS = "discord_allowed_user_ids"

_TRUE = {"1", "true", "yes", "on"}


@dataclass
class DiscordConfig:
    enabled: bool = False
    token: str = ""
    agent_id: int | None = None
    allowed_user_ids: list[str] = field(default_factory=list)

    @property
    def configured(self) -> bool:
        """True when there is enough to actually run (token + agent + allowlist)."""
        return bool(self.token and self.agent_id is not None and self.allowed_user_ids)

    def is_allowed(self, user_id: str) -> bool:
        return str(user_id) in self.allowed_user_ids


def get_discord_config(session: Session) -> DiscordConfig:
    from ..db.models import AppSetting

    def value(key: str) -> str:
        row = session.get(AppSetting, key)
        return row.value.strip() if row and row.value else ""

    raw_agent = value(KEY_AGENT_ID)
    raw_ids = value(KEY_ALLOWED_USERS).replace(";", ",")
    return DiscordConfig(
        enabled=value(KEY_ENABLED).lower() in _TRUE,
        token=value(KEY_TOKEN),
        agent_id=int(raw_agent) if raw_agent.isdigit() else None,
        allowed_user_ids=[x.strip() for x in raw_ids.split(",") if x.strip()],
    )
