# Evano Studio

> Create local AI agents for your business — without paid APIs, without cloud lock-in, and without touching the terminal.

[![Total downloads](https://img.shields.io/github/downloads/RaulMandujano/evano-studio/total?label=downloads&color=2ea043)](https://github.com/RaulMandujano/evano-studio/releases)
[![Latest release downloads](https://img.shields.io/github/downloads/RaulMandujano/evano-studio/latest/total?label=latest%20release&color=2ea043)](https://github.com/RaulMandujano/evano-studio/releases/latest)
[![Latest version](https://img.shields.io/github/v/release/RaulMandujano/evano-studio?label=version&color=8957e5)](https://github.com/RaulMandujano/evano-studio/releases/latest)
[![License: AGPL-3.0](https://img.shields.io/badge/license-AGPL--3.0-blue)](LICENSE)

**Status:** 🚧 **Alpha** — the core features are built and run locally from source, but the project is **not production-ready**: there's no signed installer yet, and you currently run it from source. Expect rough edges. See the [roadmap](docs/ROADMAP.md).

**License:** [AGPL-3.0](LICENSE) · **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md) · **Security:** [SECURITY.md](SECURITY.md)

---

## What is Evano Studio?

Evano Studio is a **free, open-source, local-first desktop application** that lets normal people — creators, startups, and small businesses — create, run, and manage local AI agents on their own computer.

It is designed to feel like a simple desktop **control center**, not a developer tool. You don't install Python packages by hand, you don't memorize Ollama commands, and you don't paste API keys from a cloud dashboard. You open the app and build AI "employees" for your business.

The product is built on three promises:

- **Free by default** — no paid APIs, no cloud subscriptions, no metered usage.
- **Local-first** — your models, documents, and data live on your machine.
- **Privacy-first** — nothing is uploaded to the cloud unless you explicitly choose to.

## Who is it for?

- **Non-technical users** who want AI helpers without learning to code.
- **Creators** who want a private assistant for writing, research, and image prompts.
- **Startups and small businesses** that want local AI agents for repeatable work (drafting documents, answering from a knowledge base, generating image prompts, running routines).
- **Developers and contributors** who want a clean, maintainable, open-source AI desktop platform to build on.

## The free / local mission

Evano Studio does not sell "terminal commands" or "Ollama setup." It packages a professional experience around free, local, open tools so that anyone can run real AI agents without recurring cost or cloud dependency.

Read the full philosophy in [docs/FREE_BY_DEFAULT.md](docs/FREE_BY_DEFAULT.md).

## High-level features

Evano Studio is a friendly control center for [OpenClaw](https://docs.openclaw.ai) agents:

- **Agents** — create OpenClaw agents from templates (name, emoji, mission) without touching the terminal.
- **Chats** — every conversation in one place (from the app, Discord, team runs…) and continue any of them.
- **Teams** — multi-agent relay workflows: each agent does its part and hands the work to the next.
- **Org Chart** — a real chain of command: managers can delegate work to their direct reports (enforced as OpenClaw permissions, not just a drawing).
- **Office** — watch your agents work live: at their desk when busy, in the break room when idle.
- **AFM (Agent File Management)** — one tidy folder for everything your agents create (`Agents/<name>`, `Teams/<team>/<member>`).
- **Discord bots** — connect each agent to Discord as its own bot with a guided, non-technical flow.
- **Knowledge base (RAG)** — import documents locally (ChromaDB); agents use them in chats *and* on Discord (memory sync).
- **Documents** — every file your agents write, grouped by agent, with preview.
- **Local image generation** — agents craft prompts and generate images via a local ComfyUI instance.
- **Routines & calendar** — schedule single agents or whole team workflows.
- **Logs & support bundle** — diagnose problems with privacy-respecting logs.

Full scope and boundaries are in [docs/ROADMAP.md](docs/ROADMAP.md).

## Tech stack

| Layer | Technology |
| --- | --- |
| Desktop shell | Electron |
| Desktop UI | React + TypeScript |
| Local backend | Python + FastAPI |
| Local AI runtime | [Ollama](https://ollama.com) |
| Recommended model | Gemma (3/4 class) — falls back to other supported models |
| Other models | Qwen, Llama, Mistral, DeepSeek distill |
| App database | SQLite |
| Knowledge base / RAG | ChromaDB (local persistent, no cloud) |
| Image generation | ComfyUI (optional, local, external service) |
| Website | Next.js + React + TypeScript |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full picture.

## Repository layout

A **pnpm** monorepo:

```
evano-studio/
├── apps/
│   ├── desktop/          # Electron + React + TypeScript desktop app
│   └── website/          # Next.js website (evanostudio.com)
├── services/
│   └── agent-engine/     # Python FastAPI local backend
├── packages/
│   ├── shared/           # Shared types/config
│   ├── ui/               # Shared UI components (if useful)
│   └── config/           # Shared config constants
├── scripts/              # Setup, dev, and health-check scripts
├── data/                 # Local-only runtime data (git-ignored contents)
│   ├── sqlite/           # Local dev database
│   ├── chroma/           # Local ChromaDB persistent storage
│   ├── workspace/        # Generated documents/images
│   └── logs/             # Local logs
└── docs/                 # Project documentation
```

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for what each folder is for and how to add modules.

## Local dependencies (you provide these)

Evano Studio is free and local; a couple of local tools are installed by **you** —
the app guides you and never installs software silently:

- **Ollama** (required) — the local AI runtime. Install from [ollama.com](https://ollama.com), then install a model from the app's Models page. See [docs/OLLAMA.md](docs/OLLAMA.md).
- **ComfyUI** (optional) — only for local image generation; you install and run it yourself. See [docs/COMFYUI_INTEGRATION.md](docs/COMFYUI_INTEGRATION.md).
- **ChromaDB** (bundled) — the local knowledge base is a Python dependency of the backend; no separate install. See [docs/SQLITE.md](docs/SQLITE.md) and [docs/RAG_WITH_CHROMADB.md](docs/RAG_WITH_CHROMADB.md).

## Setup & development

Prerequisites: **Node.js ≥ 20**, **pnpm ≥ 9**, **Python ≥ 3.10**.

```bash
# 1. Install JS workspace dependencies
pnpm install

# 2. Backend (local FastAPI agent engine)
cd services/agent-engine
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --host 127.0.0.1 --port 8765    # http://127.0.0.1:8765/docs

# 3. Desktop app (in another terminal, from the repo root)
pnpm dev:desktop

# Optional: the website
pnpm dev:website                                     # http://localhost:3000
```

Then in the app: install Ollama + a model (Models page), create an agent, and chat.

**Useful commands**

```bash
pnpm dev:desktop        # run the desktop app (Electron + React)
pnpm dev:website        # run the website (Next.js)
pnpm --filter @evano/desktop typecheck
pnpm --filter @evano/website typecheck
# backend tests:
cd services/agent-engine && source .venv/bin/activate && pytest
```

New here? Start with [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Documentation

| Document | Purpose |
| --- | --- |
Start at the docs index: **[docs/README.md](docs/README.md)**. Key documents:

| Document | Purpose |
| --- | --- |
| [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | Repository layout and how to add modules |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System and monorepo architecture |
| [docs/DESKTOP_APP.md](docs/DESKTOP_APP.md) | The Electron desktop app |
| [docs/AGENT_ENGINE.md](docs/AGENT_ENGINE.md) | The local Python/FastAPI backend |
| [docs/OLLAMA.md](docs/OLLAMA.md) | Local AI runtime & models |
| [docs/SQLITE.md](docs/SQLITE.md) | Local database |
| [docs/RAG_WITH_CHROMADB.md](docs/RAG_WITH_CHROMADB.md) | Local knowledge base (ChromaDB) |
| [docs/COMFYUI_INTEGRATION.md](docs/COMFYUI_INTEGRATION.md) | Local image generation |
| [docs/ROUTINES_AND_CALENDAR.md](docs/ROUTINES_AND_CALENDAR.md) | Routines & calendar |
| [docs/DOCUMENTS.md](docs/DOCUMENTS.md) | Documents & workspace |
| [docs/EASY_START.md](docs/EASY_START.md) | Onboarding wizard & setup status |
| [docs/TOOLS.md](docs/TOOLS.md) | Safe local tools & agent tool calling |
| [docs/DISCORD.md](docs/DISCORD.md) | Optional Discord channel for agents |
| [docs/OPENCLAW.md](docs/OPENCLAW.md) | Evano as an easy front-end for OpenClaw |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues & support bundle |
| [docs/FREE_BY_DEFAULT.md](docs/FREE_BY_DEFAULT.md) | Free/local philosophy |
| [docs/SECURITY.md](docs/SECURITY.md) | Security model |
| [docs/PACKAGING.md](docs/PACKAGING.md) | Desktop packaging |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Scope and phases |

## ⚠️ Important: alpha status

Evano Studio is in **public alpha**.

- The core features are **built and working locally from source** — not a mockup.
- There is **no signed installer yet**; you run it from source for now.
- It is **not production-ready** — expect rough edges, bugs, and changes.
- Results and speed depend on **your hardware** and the **local models** you choose.

## Contributing

Contributions are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md) and the
engineering standards in [docs/DEVELOPMENT_RULES.md](docs/DEVELOPMENT_RULES.md).
Use the issue templates for bugs and feature requests.

## Security

Please report vulnerabilities privately — see [SECURITY.md](SECURITY.md). The
local-first security model is documented in [docs/SECURITY.md](docs/SECURITY.md).

## License

Evano Studio is open source under the **[GNU AGPL-3.0 License](LICENSE)**. By
contributing, you agree your contributions are licensed under AGPL-3.0. In short:
you can use, study, modify, and share this software freely — but if you offer a
modified version as a service, you must share your changes under the same license.
