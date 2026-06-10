# Architecture

This document describes the target architecture for Evano Studio. It is a planning document — **no code is implemented yet**. The goal is to lock down a clean, modular, maintainable design before any application code is written.

## Design principles

1. **Local-first.** Everything runs on the user's machine. The cloud is never required.
2. **Clear boundaries.** The desktop UI never touches the operating system directly. All privileged work goes through a backend over a well-defined API, and all OS-level access goes through safe Electron IPC.
3. **Modular.** Each app/service/package has one responsibility and a stable contract with its neighbors.
4. **Replaceable parts.** Ollama, ChromaDB, and ComfyUI are integrated through thin adapters so they can be upgraded or swapped without rewrites.
5. **Safe by default.** Permissions, filesystem boundaries, and privacy rules are enforced in the backend, not assumed in the UI.

---

## 1. Monorepo architecture

Evano Studio is a monorepo so that shared types, config, and UI stay consistent across the desktop app, the website, and the backend.

```
evano-studio/
├── apps/
│   ├── desktop/          # Electron + React + TypeScript
│   └── website/          # Next.js + React + TypeScript
├── services/
│   └── agent-engine/     # Python + FastAPI
├── packages/
│   ├── shared/           # Shared TS types, API contracts, constants
│   ├── ui/               # Shared React UI components (optional)
│   └── config/           # Shared config constants
├── data/                 # Local runtime data (git-ignored)
└── docs/
```

**Boundaries between workspaces:**

- `apps/desktop` depends on `packages/shared`, `packages/ui`, `packages/config`. It talks to `services/agent-engine` over local HTTP.
- `apps/website` depends only on `packages/ui` and `packages/config`. It never imports backend code.
- `services/agent-engine` (Python) is independent. The TypeScript/Python contract is defined as types in `packages/shared` and mirrored as Pydantic schemas in the backend. The two are kept in sync by hand for V1 (codegen can come later).
- `packages/*` never depend on `apps/*` or `services/*`.

This separation means the website can ship independently of the desktop app, and the backend can be tested independently of the UI.

---

## 2. Desktop app architecture (Electron + React + TypeScript)

The desktop app has three layers, with strict separation enforced by Electron's security model.

```
┌──────────────────────────────────────────────────────────┐
│ Renderer process (React + TypeScript)                      │
│  - All UI: agents, chat, documents, knowledge base,        │
│    routines, calendar, settings, logs                      │
│  - NO node integration, NO direct filesystem access        │
│  - Talks to backend via a typed API client (local HTTP)    │
│  - Talks to OS-level features ONLY via preload IPC          │
└───────────────▲───────────────────────▲──────────────────┘
                │ contextBridge (IPC)    │ HTTP (localhost)
┌───────────────┴───────────┐  ┌─────────┴──────────────────┐
│ Preload script             │  │ services/agent-engine       │
│  - contextIsolation: ON    │  │ (FastAPI, started by main)  │
│  - Exposes a small, safe    │  │                             │
│    typed IPC surface only   │  │                             │
└───────────────▲────────────┘  └────────────────────────────┘
                │ ipcMain handlers
┌───────────────┴────────────────────────────────────────────┐
│ Main process (Electron)                                      │
│  - Window lifecycle                                          │
│  - Spawns & supervises the local Python backend             │
│  - Owns the only path to OS actions (open folder, etc.)      │
│  - No arbitrary shell execution exposed to the renderer      │
└──────────────────────────────────────────────────────────────┘
```

**Key decisions:**

- `contextIsolation` is **always enabled**; `nodeIntegration` is **always disabled** (see [SECURITY.md](SECURITY.md)).
- The preload script exposes a **small, explicit, typed** IPC API via `contextBridge` — never the raw `ipcRenderer`, never `require`, never `fs`.
- The renderer reaches application logic (agents, RAG, routines) through the **backend HTTP API**, not through IPC. IPC is reserved for things only Electron can do (window controls, "open this folder in the OS file manager", app lifecycle).
- The **main process owns the backend lifecycle**: it starts the Python `agent-engine` on app launch, monitors health, and shuts it down on quit.

**Renderer folder structure (planned):**

```
apps/desktop/src/
├── main/                 # Electron main process
├── preload/              # Preload + typed IPC bridge
└── renderer/
    ├── app/              # App shell, routing, providers
    ├── features/         # agents, chat, documents, kb, routines, calendar, settings, logs
    ├── lib/              # API client, hooks, utilities
    └── components/       # Reusable presentational components
```

---

## 3. Backend architecture (Python + FastAPI)

The backend is the brain. It owns all application logic, all data, and all integrations with external local services (Ollama, ChromaDB, ComfyUI). It listens **only on localhost**.

```
services/agent-engine/
├── app/
│   ├── main.py               # FastAPI app factory, startup/shutdown
│   ├── api/                  # HTTP routers (one per domain)
│   │   ├── agents.py
│   │   ├── chat.py
│   │   ├── documents.py
│   │   ├── knowledge.py      # RAG import/search
│   │   ├── images.py         # ComfyUI integration
│   │   ├── routines.py
│   │   └── system.py         # health, logs, support bundle
│   ├── core/                 # config, security, paths, errors
│   ├── services/             # business logic (no HTTP here)
│   │   ├── agent_service.py
│   │   ├── permission_service.py
│   │   ├── routine_runner.py
│   │   └── ...
│   ├── adapters/             # thin wrappers around external systems
│   │   ├── ollama.py
│   │   ├── chroma.py
│   │   └── comfyui.py
│   ├── db/                   # SQLite access, migrations, models
│   └── schemas/              # Pydantic request/response models
└── tests/
```

**Layering rule:** `api → services → adapters/db`. HTTP concerns stay in `api/`. Business rules stay in `services/`. External-system details stay in `adapters/`. This keeps the integrations replaceable and the logic testable.

**Security responsibilities of the backend:**

- Enforces agent permissions and tool permissions on every request.
- Enforces filesystem boundaries (workspace-only access, no directory traversal).
- Binds to `127.0.0.1` only.
- Never logs secrets or private content.

---

## 4. Website architecture (Next.js + React + TypeScript)

The website (`evanostudio.com`) is a separate, mostly-static marketing and documentation site. It shares nothing sensitive with the desktop app.

```
apps/website/
├── app/                  # Next.js App Router
│   ├── (marketing)/      # landing page
│   ├── download/         # download page
│   ├── docs/             # documentation
│   └── faq/              # FAQ
├── components/
└── content/              # MDX / content for docs & FAQ
```

- Statically rendered where possible for speed and cheap hosting.
- No telemetry by default. No tracking that conflicts with the privacy-first promise.
- Honest marketing only — see [WEBSITE.md](WEBSITE.md).

---

## 5. Local data architecture

All runtime data lives under `data/` (git-ignored in development) or, in a packaged app, under the OS-appropriate per-user application data directory. Nothing leaves the machine.

```
data/
├── sqlite/      # app database: agents, routines, runs, metadata
├── chroma/      # ChromaDB persistent vector store (knowledge base)
├── workspace/   # user-facing generated files (documents, images)
└── logs/        # application logs
```

**SQLite holds:**

- Agent definitions and their permission/tool config.
- Knowledge base collection metadata (the vectors themselves live in ChromaDB).
- Routine definitions and schedules.
- Routine run history and statuses.
- App settings.

**SQLite does NOT hold** raw embeddings (ChromaDB owns those) or large binary files (the workspace owns those).

**Path safety:** the backend resolves every file path against an allow-listed workspace root and rejects anything that escapes it (see [SECURITY.md](SECURITY.md)).

---

## 6. Ollama integration architecture

Ollama is the local AI runtime. Evano Studio treats it as an **external local service** reached through a thin adapter.

```
agent-engine ──HTTP──► Ollama (http://127.0.0.1:11434)
   adapters/ollama.py
```

- The backend never bundles or reimplements Ollama; it calls Ollama's local HTTP API.
- On startup the backend **detects** whether Ollama is running and which models are installed.
- **Recommended model:** Gemma (3/4 class) when available; otherwise the app suggests another installed supported model (Qwen, Llama, Mistral, DeepSeek distill).
- Model selection is per-agent, validated against the list of locally installed models.
- If Ollama is not running or no model is installed, the app shows clear, non-technical guidance instead of failing silently.

The adapter exposes a small internal interface (`generate`, `chat`, `list_models`, `embeddings`) so the rest of the backend is decoupled from Ollama's specifics.

---

## 7. ChromaDB local RAG architecture

The knowledge base uses ChromaDB in **local persistent mode only**. There is no Chroma Cloud and no paid vector database (see [RAG_WITH_CHROMADB.md](RAG_WITH_CHROMADB.md)).

```
Document ──► extract text ──► chunk ──► embed (local) ──► store in ChromaDB
Query   ──► embed (local) ──► similarity search ──► top-k chunks ──► agent context
```

- ChromaDB runs **embedded in the backend process**, persisting to `data/chroma/`.
- Embeddings are generated locally (via Ollama or a local embedding model) — never via a paid API.
- Collection metadata is mirrored in SQLite so the UI can list/manage knowledge bases without scanning the vector store.
- The `adapters/chroma.py` wrapper isolates ChromaDB so it can be upgraded independently.

---

## 8. ComfyUI local integration architecture

ComfyUI is an **optional external local service** for image generation. Evano Studio **does not copy or bundle ComfyUI source** (see [COMFYUI_INTEGRATION.md](COMFYUI_INTEGRATION.md)).

```
agent-engine ──HTTP──► ComfyUI (user-configured local URL, e.g. http://127.0.0.1:8188)
   adapters/comfyui.py
```

- The user installs and runs ComfyUI themselves and configures its local URL in settings.
- If no URL is configured, image generation features are simply disabled (the rest of the app works fine).
- The backend sends a prompt/workflow to ComfyUI, polls for completion, and saves the resulting image into `data/workspace/`.
- No paid image API is ever used.

---

## 9. Routine / calendar architecture

Routines let agents run repeatable tasks on a schedule. The calendar is the visual front end for routines (see [ROUTINES_AND_CALENDAR.md](ROUTINES_AND_CALENDAR.md)).

```
Calendar UI (renderer)
      │  create/edit routine (HTTP)
      ▼
routines API ──► routine_runner (scheduler in backend)
      │                 │ when due, and only if backend is running
      ▼                 ▼
   SQLite          executes agent task ──► writes run record + logs
 (definitions,
  run history)
```

- Routine definitions and run history live in SQLite.
- The **scheduler runs inside the backend process**. If the backend (i.e. the app) is closed, scheduled routines **do not run** — by design, this is a local-first app, not a background daemon for V1.
- Missed runs while the app was closed are recorded as "missed," not silently retried.
- Every run produces a log entry for transparency.

---

## 10. Text architecture diagram (whole system)

```
                         ┌──────────────────────────────┐
                         │        evanostudio.com        │
                         │   apps/website (Next.js)      │
                         │   landing · download · docs   │
                         └──────────────────────────────┘
                                  (independent)

  ┌───────────────────────── Desktop app (Electron) ─────────────────────────┐
  │                                                                            │
  │   ┌──────────────┐    contextBridge IPC    ┌───────────────────────┐      │
  │   │  Renderer    │◄──────────────────────►│  Main process          │      │
  │   │  React + TS  │   (window/OS actions)   │  - window lifecycle    │      │
  │   │  features:   │                         │  - spawns backend      │      │
  │   │  agents/chat │                         │  - supervises health   │      │
  │   │  docs/kb/    │                         └──────────┬─────────────┘      │
  │   │  routines/   │                                    │ spawn             │
  │   │  calendar    │                                    ▼                   │
  │   └──────┬───────┘                         ┌────────────────────────┐    │
  │          │  HTTP (127.0.0.1)               │  agent-engine          │    │
  │          └────────────────────────────────►  FastAPI (Python)      │    │
  │                                            │  api → services →      │    │
  │                                            │  adapters/db           │    │
  │                                            └───┬─────┬─────┬─────┬──┘    │
  └────────────────────────────────────────────────┼─────┼─────┼─────┼───────┘
                                                    │     │     │     │
                          ┌─────────────────────────┘     │     │     └───────────────┐
                          ▼                                ▼     ▼                     ▼
                  ┌──────────────┐               ┌──────────────┐ ┌───────────┐ ┌──────────────┐
                  │   Ollama     │               │  ChromaDB    │ │  SQLite   │ │   ComfyUI    │
                  │ local LLM    │               │ local vector │ │ app data  │ │ optional,    │
                  │ 127.0.0.1    │               │ data/chroma  │ │ data/     │ │ external,    │
                  │ :11434       │               │ (embedded)   │ │ sqlite    │ │ user-run     │
                  └──────────────┘               └──────────────┘ └───────────┘ └──────────────┘

                  Local workspace files (documents, images): data/workspace
                  Logs: data/logs        Everything stays on the user's machine.
```

---

## Cross-cutting decisions summary

| Concern | Decision |
| --- | --- |
| UI ↔ logic | Renderer talks to backend over localhost HTTP; never touches OS directly |
| OS actions | Only via small typed Electron IPC bridge |
| Backend binding | `127.0.0.1` only |
| External services | Ollama, ChromaDB, ComfyUI behind thin adapters |
| Data location | Local only, under `data/` (dev) or per-user app dir (packaged) |
| Schedules | Run only while the app is open (V1) |
| Cloud | Never required; nothing uploaded by default |

See [ROADMAP.md](ROADMAP.md) for the order in which these pieces will be built.
