# data/

Local development data. **Everything here stays on your machine and must never be committed** (the contents are git-ignored; only the folder structure and this README are tracked).

| Folder | Holds |
| --- | --- |
| `sqlite/` | Local app database (agents, routines, run history, metadata). |
| `chroma/` | Local ChromaDB persistent vector store for the knowledge base (RAG). |
| `workspace/` | User-facing generated files (documents, images). |
| `logs/` | Local application logs. |

## Why this is not committed

This folder contains **user and runtime data** — private documents, chat-derived content, databases, vectors, and logs. Committing it would:

- Leak private/local content into version control (violates the privacy-first promise — see [docs/SECURITY.md](../docs/SECURITY.md)).
- Bloat the repository with machine-specific binary data.

The `.gitignore` ignores the contents of each subfolder but keeps the folders via `.gitkeep` so the structure exists on a fresh checkout.

> In a packaged app, this data lives in the OS-appropriate per-user application data directory, not inside the repo. This `data/` folder is for **development only**. See [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).
