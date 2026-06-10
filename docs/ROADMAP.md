# Roadmap

This roadmap defines the complete V1 scope for Evano Studio, the order in which it will be built, what must be done before a public alpha, and what is explicitly out of scope.

**Current status:** Phase 0 (documentation foundation). No application code exists yet.

---

## V1 complete scope

V1 is the first feature-complete, locally-installable version of Evano Studio. It is considered done when all of the following work end-to-end on macOS, locally, with no paid services:

### Platform & shell
- Electron desktop app (React + TypeScript) with secure config (contextIsolation on, nodeIntegration off).
- Local Python + FastAPI backend, started and supervised by the desktop app.
- Local SQLite database for app data.
- Health checks and graceful handling when Ollama / ComfyUI are missing.

### Agents
- Create, edit, and delete agents.
- Per-agent configuration: name, role/description, model, system prompt, permissions, enabled tools.
- Explicit permission model — agents can only use tools that are turned on.
- See [AGENTS.md](AGENTS.md).

### Chat
- Chat with an agent through the desktop UI.
- Streamed responses from a local Ollama model.
- Conversation history stored locally.

### Documents
- Agents can create documents and save them to the local workspace.
- User can view and open generated documents.

### Knowledge base (RAG)
- Import documents into a local ChromaDB knowledge base.
- Local chunking + local embeddings (no paid API).
- Search the knowledge base.
- Agents can use the knowledge base as context when permitted.
- See [RAG_WITH_CHROMADB.md](RAG_WITH_CHROMADB.md).

### Images
- Agents help generate image prompts.
- Optional local image generation via a user-configured ComfyUI instance.
- Generated images saved to the local workspace.
- All image features cleanly disabled when ComfyUI is not configured.
- See [COMFYUI_INTEGRATION.md](COMFYUI_INTEGRATION.md).

### Routines & calendar
- Create routines that run an agent task on a schedule.
- Visual calendar to view and manage routines.
- Routine run history and statuses.
- Clear behavior when the app/backend is closed (missed, not silently retried).
- See [ROUTINES_AND_CALENDAR.md](ROUTINES_AND_CALENDAR.md).

### Diagnostics
- Local logs.
- Privacy-respecting support bundle (no private chat/document contents by default).
- See [SECURITY.md](SECURITY.md).

### Website
- `evanostudio.com` with landing, download, docs, and FAQ pages.
- Honest, non-overpromising marketing.
- See [WEBSITE.md](WEBSITE.md).

### Packaging & release
- macOS packaging first.
- Open-source release preparation (license, contributing guide, repo hygiene).

---

## Development phases

Phases are built in order. Each phase should leave the project in a working, testable state. **Do not start a phase before the one it depends on is stable.**

### Phase 0 — Documentation foundation ✅ (this phase)
- README and all `docs/` files.
- Architecture, scope, rules, security, and philosophy locked down.
- **No application code, no dependencies.**

### Phase 1 — Monorepo & skeletons
- Create the monorepo structure (`apps/`, `services/`, `packages/`, `data/`).
- Minimal, runnable skeletons: empty Electron window, empty FastAPI app with a `/health` endpoint, shared types package.
- Wire the desktop app to start and health-check the backend.
- No features yet — just the plumbing.

### Phase 2 — Backend core & data layer
- SQLite schema and access layer.
- Core config, path safety, error handling.
- Ollama adapter with model detection.
- Agent CRUD API (no chat yet).

### Phase 3 — Agents & chat
- Agent management UI.
- Chat UI with streamed responses from Ollama.
- Permission model enforced in the backend.

### Phase 4 — Documents
- Document creation tool for agents.
- Workspace file handling with path safety.
- Document viewer in the UI.

### Phase 5 — Knowledge base (RAG)
- ChromaDB adapter (local persistent).
- Import + chunk + local embeddings.
- Search API and UI.
- Agent RAG integration.

### Phase 6 — Routines & calendar
- Routine definitions and scheduler in the backend.
- Calendar UI.
- Run history and logging.

### Phase 7 — Images (ComfyUI)
- ComfyUI adapter with configurable local URL.
- Image prompt generation.
- Image generation + workspace storage.
- Graceful disable when not configured.

### Phase 8 — Diagnostics & polish
- Logs viewer.
- Privacy-respecting support bundle.
- Error states, empty states, onboarding for non-technical users.

### Phase 9 — Website
- Build and deploy `evanostudio.com` (landing, download, docs, FAQ).

### Phase 10 — Packaging & open-source release
- macOS packaging.
- License finalized, repo hygiene, contribution workflow.
- First public alpha.

---

## Order of implementation (summary)

```
0 Docs ─► 1 Skeletons ─► 2 Backend core ─► 3 Agents+chat ─► 4 Documents
   ─► 5 RAG ─► 6 Routines+calendar ─► 7 Images ─► 8 Diagnostics
   ─► 9 Website ─► 10 Packaging & release
```

The guiding rule: **build the spine before the limbs.** Plumbing and data first, then the core agent experience, then the surrounding features, then packaging.

---

## What must be completed before public alpha

A public alpha can ship only when **all** of these are true:

- [ ] Phases 1–4 fully working (skeletons, backend core, agents + chat, documents).
- [ ] At least the knowledge base (Phase 5) working, since RAG is core to the "AI for your business" promise.
- [ ] Routines + calendar (Phase 6) working at a basic level.
- [ ] Diagnostics (Phase 8) — logs and a privacy-safe support bundle, so alpha users can report issues.
- [ ] Graceful handling when Ollama is missing or no model is installed.
- [ ] macOS package that a non-technical user can install and open.
- [ ] Website download page with honest setup instructions.
- [ ] Security rules from [SECURITY.md](SECURITY.md) verified (Electron config, filesystem boundaries, no cloud upload).
- [ ] License chosen and `CONTRIBUTING.md` accurate.

Images (Phase 7) may ship as "experimental/optional" in the first alpha if ComfyUI integration is not fully polished, since it is explicitly optional.

---

## What is NOT included (V1 out of scope)

To avoid overbuilding, the following are intentionally **excluded** from V1:

- ❌ Any cloud sync, cloud accounts, or cloud storage.
- ❌ Any paid API (LLM, embeddings, or image generation).
- ❌ Chroma Cloud or any hosted/paid vector database.
- ❌ Windows and Linux packaging (macOS first; others later).
- ❌ Background daemon that runs routines while the app is closed.
- ❌ Multi-user / team collaboration features.
- ❌ A plugin marketplace or third-party extension system.
- ❌ Mobile apps.
- ❌ Bundling or forking ComfyUI source (it stays an external user-run service).
- ❌ Auto-installing Ollama, models, or ComfyUI silently (the app guides; it does not silently install).
- ❌ Fine-tuning or training models.
- ❌ Advanced agent orchestration (multi-agent graphs, autonomous loops) beyond simple routines.

These may be revisited post-V1, but they must not creep into V1 scope. See [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) on the no-overbuilding rule.
