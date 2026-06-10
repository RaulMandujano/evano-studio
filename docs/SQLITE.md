# SQLite (Local Database)

Evano Studio stores app data in a local **SQLite** database via **SQLModel**
(SQLAlchemy + Pydantic). It's serverless, file-based, free, and entirely local —
no cloud database, no account.

## Where it lives

`<EVANO_DATA_DIR>/sqlite/evano.db`, where `EVANO_DATA_DIR` defaults to
`~/.evano-studio`. Override with `EVANO_DATA_DIR`, or set a full
`EVANO_DATABASE_URL` (advanced; e.g. `sqlite://` in tests).

## What it stores

- `app_settings` — key/value preferences (e.g. workspace override, ComfyUI config)
- `agents` — agent configs (model, prompt, permissions, enabled tools)
- `documents` — metadata for generated documents (files live in the workspace)
- `knowledge_documents` — knowledge-base document metadata (vectors live in ChromaDB)
- `routines` / `routine_runs` — schedules and their logged executions
- `image_generations` — image request metadata
- `service_status_logs` — non-sensitive lifecycle events

Large/binary content is **not** in SQLite — files live in the workspace, vectors
in ChromaDB.

## Migrations

Lightweight, no Alembic: tables are created on startup with
`SQLModel.metadata.create_all` (only missing tables), and a small idempotent
step adds new columns to existing tables. A full migration tool can be added later
if the schema needs backward-incompatible changes.

## Why SQLite fits the mission

Zero setup, zero cost, one local file the user owns — exactly the local-first,
privacy-first, free-by-default promise. See also
[RAG_WITH_CHROMADB.md](RAG_WITH_CHROMADB.md) for the vector store.
