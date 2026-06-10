# Project Structure

This document explains how the Evano Studio repository is organized, why it's a monorepo, what each folder is for, and how to add new modules without breaking the project. It complements [ARCHITECTURE.md](ARCHITECTURE.md) (which covers system design) by focusing on the **repository layout and developer workflow**.

> Created in Phase 1 (monorepo setup) and kept up to date as the app grows. All
> major areas now contain real application code: the desktop app (views, API
> client, hooks, and CSS partials under `apps/desktop/src/renderer/src/`), the
> FastAPI backend (`services/agent-engine/app/{api,services,schemas,db}` with a
> full pytest suite in `tests/`), and the website.

---

## Why a monorepo?

Evano Studio ships several pieces that must stay consistent with each other: a desktop app, a website, a Python backend, and shared TypeScript code. A monorepo lets us:

- **Share types and constants** between the desktop app and website (and mirror them to the backend) from one source of truth (`packages/shared`, `packages/config`).
- **Make atomic changes** across boundaries (e.g., update an API contract and its consumer in one PR).
- **Keep one set of tooling and conventions** (lint, format, editorconfig) for the whole project.
- **Onboard contributors quickly** — everything is in one place with one structure.

We use **pnpm workspaces** because pnpm is fast, disk-efficient (shared content-addressed store), and has first-class monorepo support.

---

## Top-level layout

```
evano-studio/
├── apps/                  # End-user applications
│   ├── desktop/           # Electron + React + TS desktop app  (@evano/desktop)
│   └── website/           # Next.js website for evanostudio.com (@evano/website)
├── services/              # Backend services (non-JS)
│   └── agent-engine/      # Python + FastAPI local backend
├── packages/              # Shared JS/TS libraries
│   ├── shared/            # Types, API contracts, constants     (@evano/shared)
│   ├── ui/                # Shared React components              (@evano/ui)
│   └── config/            # Shared config constants             (@evano/config)
├── scripts/               # Project automation
│   ├── setup/             # Environment setup/check helpers
│   ├── dev/               # Development launchers
│   └── health-checks/     # Local service/environment checks
├── data/                  # Local development data (git-ignored contents)
│   ├── sqlite/            # Local app database
│   ├── chroma/            # Local ChromaDB persistent store
│   ├── workspace/         # Generated documents/images
│   └── logs/              # Local logs
├── docs/                  # Project documentation
├── .github/workflows/     # CI workflows (added when needed)
├── package.json           # Root workspace manifest (private)
├── pnpm-workspace.yaml     # Workspace globs (apps/*, packages/*)
├── .gitignore
├── .editorconfig
├── LICENSE                # GNU AGPL-3.0
└── README.md
```

---

## What each folder is for

### `apps/`
User-facing applications. Each app is its own workspace with its own `package.json`.

- **`apps/desktop`** — the Electron desktop app (the product itself). React + TypeScript renderer, secure Electron main + preload. Starts and supervises the local backend.
- **`apps/website`** — the Next.js marketing/documentation site for evanostudio.com. Ships independently of the desktop app.

### `services/`
Backend services that are **not** JavaScript/TypeScript and therefore not pnpm workspaces.

- **`services/agent-engine`** — the Python + FastAPI local backend. It owns all application logic, the SQLite data layer, and the Ollama / ChromaDB / ComfyUI integrations. Managed with Python tooling (venv + `pyproject.toml`), added when implementation begins.

### `packages/`
Shared JS/TS libraries consumed by `apps/*`. They must never import from `apps/*` or `services/*`.

- **`packages/shared`** — TypeScript types, API request/response contracts, shared constants. This is the source of truth for the TS↔Python contract (the backend mirrors these as Pydantic schemas).
- **`packages/ui`** — shared React components used by the desktop app and website where reuse makes sense.
- **`packages/config`** — shared configuration constants (defaults, enums, etc.).

### `scripts/`
Project automation, organized by intent: `setup/` (check/guide environment — never silent installs), `dev/` (launchers), `health-checks/` (verify Ollama/backend/ComfyUI). See [scripts/README.md](../scripts/README.md).

### `data/`
Local development data. **Contents are git-ignored**; only the folder structure (via `.gitkeep`) and a README are tracked. See "Where local data lives" below.

### `docs/`
All project documentation (this file, architecture, roadmap, security, etc.).

### `.github/workflows/`
Continuous-integration workflows. Empty placeholder for now; CI is wired in as the project gains code to lint/test/build.

---

## How desktop, website, and backend relate

```
   apps/website  (independent — marketing & docs, ships on its own)

   apps/desktop  ──HTTP (127.0.0.1)──►  services/agent-engine (FastAPI)
        │                                      │
        │ imports                               ├─► Ollama        (local LLM)
        ▼                                       ├─► ChromaDB      (local RAG)
   packages/shared, packages/ui,                ├─► SQLite        (app data)
   packages/config                              └─► ComfyUI       (optional, local)
        ▲
        └── mirrored as Pydantic schemas in the backend
```

- The **desktop app** is the only piece that talks to the **backend**, over localhost HTTP. OS-level actions go through a small typed Electron IPC bridge (never direct filesystem access from the renderer).
- The **website** is standalone — it does not talk to the backend and shares only presentational packages.
- The **backend** is the single enforcer of permissions and filesystem boundaries, and the only component that talks to Ollama / ChromaDB / ComfyUI.

Details in [ARCHITECTURE.md](ARCHITECTURE.md) and the security model in [SECURITY.md](SECURITY.md).

---

## Where local data lives during development

During development, runtime data is written under `data/`:

- `data/sqlite/` — the app database.
- `data/chroma/` — the ChromaDB persistent vector store.
- `data/workspace/` — generated documents and images.
- `data/logs/` — logs.

In a **packaged app**, this data lives in the OS-appropriate per-user application data directory instead of inside the repo. The `data/` folder is a development convenience only.

### Why local user data must not be committed

- **Privacy.** This data can contain private documents, knowledge-base content, and chat-derived files. Committing it would leak personal/business data into version control — a direct violation of the privacy-first promise ([SECURITY.md](SECURITY.md)).
- **Repo health.** Databases, vectors, and logs are large, binary, and machine-specific. They would bloat history and cause constant noise.

The `.gitignore` ignores the *contents* of each `data/` subfolder while keeping the folders via `.gitkeep`, so a fresh clone has the right structure without any user data.

---

## How future contributors should add new modules

Follow these conventions so the repo stays clean and scalable (see also [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) and [CONTRIBUTING.md](CONTRIBUTING.md)).

### Adding a new shared package
1. Create `packages/<name>/` with a `package.json` named `@evano/<name>`, `"private": true`, `"version": "0.0.0"`.
2. It's automatically part of the workspace (matched by `packages/*`).
3. Depend on it from an app with the workspace protocol: `"@evano/<name>": "workspace:*"`.
4. **Never** import from `apps/*` or `services/*` inside a package.
5. Document its purpose in [packages/README.md](../packages/README.md).

### Adding code to an app
- Put renderer code under the app's feature-first structure (`features/<domain>/…`), not grouped by file type. Keep the Electron security rules intact for the desktop app.

### Adding a new backend domain
- In `services/agent-engine`, add a router in `api/`, business logic in `services/`, external calls in `adapters/`, and Pydantic models in `schemas/`. Respect the `api → services → adapters/db` layering. Mirror any shared contract from `packages/shared`.

### Adding a new service (non-JS)
- Create it under `services/<name>/` and keep it **out** of `pnpm-workspace.yaml`. Document how it's run.

### Adding a script
- Place it in the right `scripts/` subfolder and document it in [scripts/README.md](../scripts/README.md). Setup scripts may *check and guide* but must **never** install software silently or use `sudo`.

### General rules
- Don't add new **top-level** folders without updating this file and explaining why.
- Don't add dependencies you don't need.
- Don't rewrite or remove unrelated working code.
- Keep changes small, typed, and testable.
