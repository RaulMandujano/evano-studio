"""Static channel + agent-file catalog metadata (display only)."""
from __future__ import annotations

import re

_LOGIN_CHANNELS = {"whatsapp", "signal", "imessage", "zalouser"}
# Slugs accepted by `openclaw channels add --channel` (from the CLI help).
_ADD_ALLOWED = {
    "telegram", "whatsapp", "discord", "irc", "googlechat", "slack", "signal",
    "imessage", "feishu", "nostr", "msteams", "mattermost", "nextcloud-talk",
    "matrix", "line", "zalo", "clickclack", "zalouser", "sms", "synology-chat",
    "tlon", "qa-channel", "qqbot", "twitch",
}
_CHANNEL_NAMES = {
    "whatsapp": "WhatsApp", "telegram": "Telegram", "discord": "Discord",
    "slack": "Slack", "signal": "Signal", "imessage": "iMessage", "sms": "SMS",
    "matrix": "Matrix", "msteams": "Microsoft Teams", "mattermost": "Mattermost",
    "googlechat": "Google Chat", "line": "LINE", "irc": "IRC", "twitch": "Twitch",
    "qqbot": "QQ Bot", "nostr": "Nostr", "feishu": "Feishu", "wecom": "WeCom",
    "nextcloud-talk": "Nextcloud Talk", "zalo": "Zalo", "zalouser": "Zalo Personal",
    "clickclack": "ClickClack", "yuanbao": "Yuanbao", "openclaw-weixin": "Weixin",
    "synology-chat": "Synology Chat", "tlon": "Tlon",
}
_CHANNEL_ICONS = {
    "whatsapp": "💬", "telegram": "✈️", "discord": "🎮", "slack": "💼",
    "signal": "🔒", "imessage": "💌", "sms": "📱", "matrix": "🔷",
    "msteams": "🟦", "twitch": "🟣", "googlechat": "🗨️", "line": "💚",
}
_POPULAR_CHANNELS = ["whatsapp", "telegram", "discord", "slack", "signal"]

# ---- Agent workspace config files (OpenClaw scaffolds these markdown files) -- #
_AGENT_FILE_LABELS = {
    "IDENTITY.md": "Identity",
    "AGENTS.md": "Instructions",
    "SOUL.md": "Personality",
    "USER.md": "About you",
    "TOOLS.md": "Tools",
    "MEMORY.md": "Memory",
    "HEARTBEAT.md": "Heartbeat",
    "BOOTSTRAP.md": "First-run",
}
_AGENT_FILE_ORDER = list(_AGENT_FILE_LABELS.keys())
_AGENT_FILE_RE = re.compile(r"^[A-Za-z0-9_-]+\.md$")
