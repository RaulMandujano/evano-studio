# agent-engine

The Evano Studio local backend — **Python + FastAPI**.

> 🚧 **Alpha.** This service exposes health/version/system endpoints plus a local **SQLite** data layer (settings + status logs). There is **no Ollama, no ChromaDB, and no ComfyUI** yet — those arrive in later phases. It is intentionally a clean, secure, local-only foundation. No agents yet.

## What's here

- A FastAPI app with a clean, layered structure (`api → services → db`, plus `core`, `schemas`, `utils`).
- Endpoints: `GET /health`, `GET /version`, `GET /system/info`, `GET/PUT /settings`,
  `GET /database/status`, `GET /ollama/status`, `GET /ollama/models`,
  `POST /ollama/chat/test`, `GET /ollama/models/recommended`,
  `POST /ollama/models/pull`, `GET /ollama/models/pull/status`,
  `GET/POST /agents`, `GET/PUT/DELETE /agents/{id}`, `POST /agents/{id}/chat`,
  `POST /agents/{id}/image-prompt`, `POST /agents/{id}/generate-image`,
  `GET/POST /documents`, `GET/DELETE /documents/{id}`,
  `POST /documents/from-agent-response`,
  `GET /knowledge/status`, `GET/POST /knowledge/documents`(+`/import`),
  `GET/DELETE /knowledge/documents/{id}`, `POST /knowledge/search`,
  `GET /tools`, `POST /tools/test`, `PUT /agents/{id}/tools`,
  `GET/POST /routines`, `GET/PUT/DELETE /routines/{id}`,
  `POST /routines/{id}/run-now`, `GET /calendar/events`,
  `GET /comfyui/status`, `PUT /comfyui/settings`, `POST /comfyui/prompt/test`,
  `GET /images`, `POST /images/generate`,
  `GET /logs`, `POST /support/bundle`.
- A **local SQLite database** via **SQLModel** (no cloud, no paid service, no Alembic).
- **Local documents** created only inside the workspace (`<data_dir>/workspace`),
  with sanitized filenames and traversal protection.
- A **local knowledge base (RAG)** via **ChromaDB** (local persistent at
  `<data_dir>/chroma`, never Chroma Cloud) with local embeddings (default MiniLM
  via onnxruntime; `ollama` or `hash` configurable). Agents with
  `knowledge_enabled` get retrieved context injected into their prompt.
- **Safe agent tools** (deny-by-default per agent): list/read workspace files,
  create Markdown/text documents, search the knowledge base, generate image
  prompts. No shell, no network/browser, no arbitrary filesystem access. The
  workspace is user-configurable (`workspace_dir` setting).
- **Local routines** (manual/once/daily/weekly) with a background scheduler that
  runs only while the backend is running. Every run is logged with visible
  output; runs missed while closed are recorded as "missed", not run late. No
  cloud calendar. `GET /calendar/events` exposes upcoming + past runs.
- **Structured local logging** to stdout, `<data_dir>/logs/agent-engine.log`, and an
  in-memory ring buffer (`GET /logs`, filterable by area/level). A
  **support bundle** (`POST /support/bundle`) collects non-sensitive diagnostics
  (versions, statuses, model names, routine summary, recent logs) — never chat
  messages, document contents, routine prompts, or secrets; written locally.
- **Optional local image generation** via an external **ComfyUI** instance
  (a thin adapter — ComfyUI is not bundled). Disabled by default; configurable at
  runtime. Prompts inject into a workflow (built-in default or a user-provided
  API-format workflow with `%positive_prompt%`/`%negative_prompt%` tokens).
  Generated images are saved into the workspace. No paid/cloud image APIs.
- **Local-only CORS** (localhost / 127.0.0.1 only) so only the desktop app can call it.
- Environment-driven config (no hardcoded secrets), consistent JSON error handling, and tests.

## Database

- **Engine:** SQLite via SQLModel (SQLAlchemy + Pydantic).
- **Location:** `<EVANO_DATA_DIR>/sqlite/evano.db`, where `EVANO_DATA_DIR` defaults
  to `~/.evano-studio`. Override with `EVANO_DATA_DIR` (e.g. point it at the
  repo's `data/` folder for development) or set a full `EVANO_DATABASE_URL`.
- **Initialization:** lightweight — tables are created on startup with
  `SQLModel.metadata.create_all` (creates only missing tables; safe every run).
  No Alembic. A full migration tool can be added later if the schema needs
  backward-incompatible changes.
- **Tables:** `app_settings` (key/value + timestamps) and `service_status_logs`
  (append-only lifecycle events for diagnostics — never secrets/private content).

## Requirements

- Python ≥ 3.10
- `pip` (and ideally a virtual environment)

## 1. Install dependencies

From this folder (`services/agent-engine`):

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"          # runtime + dev (pytest, httpx)
```

For runtime only (no tests), use `pip install -e .`.

Configuration is optional — copy `.env.example` to `.env` only if you want to
override defaults:

```bash
cp .env.example .env
```

## 2. Run the backend

Any of these work (defaults to `http://127.0.0.1:8765`):

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8765
# or
python -m app.main
# or (installed console script)
agent-engine
```

Interactive API docs are available at `http://127.0.0.1:8765/docs`.

## 3. Test the endpoints

Run the test suite:

```bash
pytest
```

Or hit the endpoints manually (while the server is running):

```bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/version
curl http://127.0.0.1:8765/system/info
```

Example `GET /health` response:

```json
{
  "status": "ok",
  "service": "Evano Studio Agent Engine",
  "version": "0.1.0",
  "uptime_seconds": 1.234
}
```

All error responses share one shape:

```json
{ "error": { "code": "http_error", "message": "Not Found" } }
```

## Project structure

```
services/agent-engine/
├── app/
│   ├── main.py            # app factory, lifespan, CORS, error handlers, root
│   ├── core/
│   │   ├── config.py      # env-driven settings (EVANO_* prefix)
│   │   ├── logging.py     # logging setup (no secrets)
│   │   └── errors.py      # AppError + JSON exception handlers
│   ├── api/
│   │   ├── deps.py        # request-scoped dependencies
│   │   ├── health.py      # GET /health
│   │   ├── version.py     # GET /version
│   │   ├── system.py      # GET /system/info
│   │   ├── settings.py    # GET/PUT /settings
│   │   ├── database.py    # GET /database/status
│   │   └── router.py      # aggregates routers
│   ├── db/
│   │   ├── base.py        # TimestampMixin (created_at/updated_at)
│   │   ├── models.py      # AppSetting, ServiceStatusLog
│   │   └── session.py     # engine, init_db (create_all), get_session
│   ├── schemas/
│   │   ├── system.py      # system response models + FeatureFlags
│   │   ├── settings.py    # settings request/response models
│   │   └── database.py    # database status model
│   ├── services/
│   │   ├── system_service.py     # logic (no HTTP here)
│   │   ├── settings_service.py   # settings CRUD
│   │   └── database_service.py   # database status + status logging
│   └── utils/
│       └── time.py
├── tests/
│   └── test_endpoints.py
├── pyproject.toml
├── .env.example
└── README.md
```

## Configuration

All settings are optional and read from the environment (prefix `EVANO_`) or
`.env`. See `.env.example`. No secrets are required.

| Variable | Default | Purpose |
| --- | --- | --- |
| `EVANO_ENVIRONMENT` | `development` | `development` or `production` |
| `EVANO_HOST` | `127.0.0.1` | Bind host (keep local) |
| `EVANO_PORT` | `8765` | Bind port |
| `EVANO_LOG_LEVEL` | `INFO` | Logging level |
| `EVANO_CORS_ALLOW_ORIGIN_REGEX` | localhost/127.0.0.1 regex | Allowed CORS origins |

## How it connects to Electron

In the packaged desktop app, the Electron **main process** will:

1. **Spawn** this backend as a local child process (bound to `127.0.0.1` on a
   known/free port) on app launch.
2. **Health-check** it by polling `GET /health` until it responds `ok`.
3. **Supervise** its lifecycle — shutting it down when the app quits.

The Electron **renderer** then calls the backend over local HTTP (e.g.
`http://127.0.0.1:8765`). CORS is restricted to localhost so nothing else on the
machine or network can reach it. The renderer never accesses the backend process
directly — only over this local HTTP boundary (see `docs/ARCHITECTURE.md` and
`docs/SECURITY.md`).
