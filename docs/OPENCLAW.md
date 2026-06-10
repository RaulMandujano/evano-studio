# OpenClaw control (Evano as a front-end for OpenClaw)

Evano Studio can act as a friendly, click-based front-end for
[OpenClaw](https://github.com/openclaw/openclaw) — a mature open-source AI agent
gateway — so non-technical users can run local AI agents without the terminal.

Rather than reinventing the agent engine, Evano **installs, configures, and
operates OpenClaw** for the user, and recommends the free local setup (Gemma 4
via Ollama — no API key, no cost), with the option to use a paid API key.

## What Evano does

| Step | How |
| --- | --- |
| Detect prerequisites | `GET /openclaw/status` reports Node, Ollama, OpenClaw presence + versions, the config, the gateway (running + port), and an overall `ready` flag. |
| Install OpenClaw | `POST /openclaw/install` runs `npm install -g openclaw` in the background (`GET /openclaw/install/status` to poll). |
| Configure | `POST /openclaw/config` runs OpenClaw's own non-interactive onboarding (`openclaw onboard --non-interactive --auth-choice ollama --custom-model-id gemma4:latest --accept-risk`) to write a valid `~/.openclaw/openclaw.json` — free local Gemma 4 (no key) or a paid API key. |
| Start / stop gateway | `POST /openclaw/gateway/start` and `/stop` drive `openclaw gateway start/stop` (launchd service). |
| Open dashboard | `GET /openclaw/dashboard` runs `openclaw dashboard --no-open` and returns the token-authenticated Control UI URL; the desktop opens it. |

The real config is `~/.openclaw/openclaw.json` (JSON), e.g. for free local use:
`agents.defaults.model.primary = "ollama/gemma4:latest"`, `gateway.mode = "local"`,
`models.providers.ollama.baseUrl = "http://localhost:11434"`. Evano relies on
OpenClaw's own onboarding to write this correctly rather than hand-editing it.

The control panel lives on the desktop **OpenClaw** page
(`apps/desktop/src/renderer/src/views/OpenClawView.tsx`); the backend logic is in
`app/services/openclaw_service.py` (+ `app/api/openclaw.py`).

## Safety / honesty

- Evano runs a **fixed, known set of commands** (detect / `npm install -g
  openclaw`), never arbitrary input — a controlled installer, not a shell.
- **Node and Ollama** are system prerequisites: Evano detects them and links to
  the official downloads (it can't silently install system software). The
  OpenClaw npm package itself is installed for you.
- PATH is augmented when running `node`/`npm`/`openclaw` because GUI-launched
  apps inherit a minimal PATH.

## Free vs paid

- **Free (recommended):** `provider: ollama`, model `gemma4`. Runs entirely on
  the user's computer; no API key, no usage cost. Needs Ollama + a pulled model
  and enough RAM (OpenClaw recommends a large context window for local models).
- **Paid API:** set a provider (e.g. `anthropic`, `openai`), model, and API key.

## Status / roadmap

Done (verified live, OpenClaw 2026.6.1): detect, install, configure (free Gemma 4
via `openclaw onboard`), start/stop the gateway, and open the token-authenticated
dashboard. Next: a simple agent editor that writes OpenClaw's agent files, and
optional paid-API onboarding polish.

See: OpenClaw docs — https://docs.openclaw.ai/ , Ollama setup —
https://ollama.com/blog/openclaw-tutorial
