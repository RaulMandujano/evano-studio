# Discord channel (optional)

Evano Studio can talk to one of your agents from Discord. It's an **opt-in,
local** connector: your machine runs a Discord bot that routes incoming messages
to the same agent "brain" used by the desktop chat (see [TOOLS.md](TOOLS.md)).

## Safety model

- **Off by default.** Nothing connects until you enable it and provide a token.
- **Deny-by-default replies.** The bot only answers Discord users whose IDs are
  on your allowlist. Everyone else is ignored.
- **No extra power.** Over Discord the agent has the exact same, workspace-
  confined, permission-gated tools as in the app — no shell, no computer control.
- **Local.** The bot connection runs from your machine; messages go to your
  local agent. (Discord itself is a cloud service, so this is the one place
  Evano talks to the cloud — only because you opted in.)

## Architecture

| Piece | File |
| --- | --- |
| Config (DB-backed, runtime) | `app/core/discord.py` |
| Connector (own thread + asyncio) | `app/services/discord_connector.py` |
| Shared agent turn | `app/services/agent_runner.py` |
| Status endpoint | `GET /discord/status` |

The connector starts during backend startup if enabled+configured; `discord.py`
is imported lazily, so a missing library never breaks the rest of the app.

## Setup

1. Create a bot at the Discord Developer Portal, copy its **token**, and enable
   **Message Content Intent** (Bot → Privileged Gateway Intents). Invite the bot
   to a server or allow DMs.
2. In Discord, enable **Developer Mode** (Settings → Advanced), then right-click
   your user → **Copy User ID**.
3. In Evano Studio → **Settings → Discord channel**: tick *Enable*, paste the
   token, pick the agent, and add your user ID(s) to the allowlist. Save.
4. **Restart the backend** (the connector binds its config at startup).
5. DM the bot (or mention it). For example: *"crea una carpeta llamada Clientes"*.

Settings are stored as `app_settings` keys: `discord_enabled`,
`discord_bot_token`, `discord_agent_id`, `discord_allowed_user_ids`.

`pip install discord.py` is required (already in the backend dependencies).
