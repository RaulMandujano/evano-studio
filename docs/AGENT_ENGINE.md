# Agent Engine (Backend)

The local backend — **Python + FastAPI** — that powers all of Evano Studio's
logic. It runs on `127.0.0.1` only and owns the data layer plus every local
integration (Ollama, ChromaDB, ComfyUI). It is **free, local, and offline-capable**.

## Run

```bash
cd services/agent-engine
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --host 127.0.0.1 --port 8765
# interactive API docs: http://127.0.0.1:8765/docs
pytest                      # run the test suite
```

Configuration is environment-driven (prefix `EVANO_`); no secrets required. Local
data lives under `EVANO_DATA_DIR` (default `~/.evano-studio`).

## Layering (`services/agent-engine/app`)

```
api/        HTTP routers (one module per domain) + deps.py
services/   business logic (no HTTP): agents, ollama, chroma, knowledge,
            documents, tools, routines, images, support, system, …
db/         SQLModel models + engine/session + lightweight migrations
schemas/    Pydantic request/response models
core/       config, logging (+ log store), errors, paths, workspace, comfyui
utils/      small helpers (time, text chunking)
tools/      the safe tool registry
```

Rule: `api → services → db/adapters`. HTTP concerns stay in `api/`; external
systems (Ollama, ChromaDB, ComfyUI) are reached through their service modules.

## Endpoints (overview)

Health/system, settings, database status, Ollama (status/models/pull/chat-test),
agents (CRUD + chat + tools + image-prompt/generate-image), documents, knowledge
base (status/import/search), tools (list/test), routines + calendar, ComfyUI
(status/settings/test) + images, logs + support bundle. See the live `/docs`.

## Notes

- Graceful degradation everywhere: if Ollama/ChromaDB/ComfyUI are missing, the
  affected endpoints return clear messages instead of crashing.
- A background scheduler runs routines **only while the backend is running**.
- All errors share one JSON shape: `{"error": {"code", "message"}}`.
