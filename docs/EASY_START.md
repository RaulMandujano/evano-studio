# Easy Start — onboarding wizard

**Easy Start** is the first page new users see. It's a guided setup center that
shows, at a glance, what's configured and what still needs attention — no
terminal required.

## What it checks

Easy Start reads a single aggregated endpoint, `GET /setup/status`, and renders a
checklist with visual progress. Steps:

1. **Backend** — the local Agent Engine is running.
2. **Ollama** — the local AI runtime is installed and reachable.
3. **Recommended Model** — at least one local model is installed.
4. **SQLite** — the local database is initialized.
5. **Workspace Folder** — a workspace is configured with its standard folders.
6. **Tool Permissions** — at least one agent can use tools.
7. **Knowledge Base** — local ChromaDB is available (optional).
8. **ComfyUI** — optional local image generation.
9. **Ready** — derived from the required steps above.

Each step shows a status, a plain-English explanation, an optional detail, and —
where relevant — a button that jumps to the page where you fix it (Models,
Agents, Settings, Knowledge Base, Images) or, for Ollama, opens the download
page in your browser.

## The aggregator endpoint

`GET /setup/status` (see `app/api/setup.py` / `app/services/setup_service.py`)
returns one object combining every subsystem's state:

```jsonc
{
  "backend":  { "running": true, "version": "0.1.0", "uptime_seconds": 2.2 },
  "ollama":   { "status": "running", "reachable": true, "recommended_available": true, ... },
  "models":   { "count": 3, "installed": ["gemma4:latest", ...] },     // names only
  "sqlite":   { "connected": true, "file_exists": true, "table_count": 9 },
  "workspace":{ "configured": true, "ready": true, "missing_subdirs": [] },
  "chromadb": { "available": true, "document_count": 0 },
  "comfyui":  { "enabled": false, "reachable": false },
  "agents":   { "count": 1, "with_tools": 1 }
}
```

It reuses each subsystem's own service, computed defensively: if one subsystem
is offline (e.g. Ollama), the rest of the response is unaffected. Only
non-sensitive metadata is included (model *names*, table *counts*) — never file
contents, prompts, or secrets.

## Workspace setup

The Workspace step is configured from **Settings → Workspace folder** (or
programmatically):

```
POST /workspace/configure   { "path": "/Users/you/EvanoWorkspace" }
GET  /workspace/status
```

Configuring validates the path (must be an absolute folder, not a filesystem
root or a file) and creates the standard structure:

```
EvanoWorkspace/
  Documents/  Images/  KnowledgeBase/  Projects/  Reports/  Logs/
```

An empty path resets to the default workspace. The folders are created *before*
the choice is saved, so a failure (e.g. permission denied) never leaves a broken
configuration. See [DOCUMENTS.md](DOCUMENTS.md) and [TOOLS.md](TOOLS.md).
