# RAG with ChromaDB

The knowledge base lets users import their own documents and have agents answer from them. It is built on **ChromaDB in local persistent mode only**. This is a design document — **no code exists yet**.

---

## ChromaDB — local only

- Evano Studio uses **ChromaDB embedded in the local backend process**, persisting to disk.
- This is the free, open-source, local mode of ChromaDB.

## No Chroma Cloud

- **Chroma Cloud (the hosted/paid product) is never used or required.**
- There is no sign-up, no API key, no remote endpoint.
- No other paid or hosted vector database is used (see [FREE_BY_DEFAULT.md](FREE_BY_DEFAULT.md)).

## Local persistent storage

- Vectors and their metadata persist under `data/chroma/` (dev) or the per-user app data directory (packaged).
- Data survives app restarts and stays entirely on the user's machine.
- **Collection metadata is also mirrored in SQLite** so the UI can list and manage knowledge bases without scanning the vector store (see [ARCHITECTURE.md](ARCHITECTURE.md)).
- ChromaDB is accessed only through `adapters/chroma.py` so it can be upgraded or swapped without touching business logic.

---

## Document import flow

1. **User imports a document** (e.g., text, Markdown, PDF — exact supported formats finalized during implementation) into a chosen knowledge base collection.
2. The backend **extracts plain text** from the document.
3. Text is **chunked** (see below).
4. Each chunk is **embedded locally** (see below).
5. Chunks + embeddings + source metadata are **stored in ChromaDB**.
6. Collection metadata (name, document list, counts) is recorded in SQLite.

All import work happens locally; nothing is uploaded.

---

## Chunking

- Documents are split into **overlapping chunks** sized to fit comfortably within the local model's context budget.
- Each chunk keeps **source metadata** (document name, position) so results can be traced back to their origin.
- Chunk size and overlap are **configurable defaults**, tuned for quality vs. context cost. Sensible defaults ship; exotic tuning is not exposed to non-technical users in V1.
- Re-importing or updating a document re-chunks that document without corrupting others.

---

## Local embeddings strategy

- **Embeddings are generated locally — never via a paid API.**
- Primary approach: use a **local embedding model via Ollama** (the same runtime that powers chat), keeping the stack simple and dependency-light.
- A bundled/local embedding model is an acceptable fallback as long as it runs entirely offline and free.
- The embedding model is wrapped behind the adapter layer so it can change without affecting the rest of the system.
- The **same embedding model must be used for both import and query** within a collection, to keep vectors comparable. If the embedding model changes, the collection must be re-embedded.

---

## Search flow

1. **User (or agent) issues a query.**
2. The query is **embedded locally** with the collection's embedding model.
3. ChromaDB performs a **similarity search** and returns the **top-k** most relevant chunks.
4. Results include their **source metadata** for traceability.
5. Results are returned to the UI (for direct search) or fed into the agent's context (for RAG).

---

## Agent RAG flow

When an agent is permitted to use a knowledge base (see [AGENTS.md](AGENTS.md)):

1. The agent receives a user question.
2. The backend **retrieves the top-k relevant chunks** from the agent's allowed knowledge base(s).
3. Those chunks are **injected into the agent's prompt context** as grounding material.
4. The **local model generates an answer** grounded in the retrieved chunks.
5. Where useful, the answer can reference its **sources** (which documents/chunks were used).

Permissions are enforced: an agent can only search knowledge bases it has been explicitly granted, and only when the RAG permission is enabled.

---

## Limitations

Be honest about what local RAG can and can't do in V1:

- **Quality depends on the local embedding and chat models** and on the user's hardware (see [FREE_BY_DEFAULT.md](FREE_BY_DEFAULT.md)).
- **Large knowledge bases may be slower** to import and search on modest machines.
- **Retrieval is similarity-based**, not perfect understanding — irrelevant or partial matches can occur.
- **Document parsing quality varies** by format (clean text vs. complex PDFs).
- **No cloud fallback** — if local resources are limited, results are limited; the app won't quietly call a paid service to compensate.
- **No automatic re-embedding** across model changes without an explicit re-import/re-embed step.

These limitations are acceptable trade-offs for a free, private, local-first knowledge base.
