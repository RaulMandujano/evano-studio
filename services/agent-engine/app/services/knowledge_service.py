"""Knowledge base service — orchestrates SQLite metadata + ChromaDB vectors.

Plain-text extraction only for V1 (.txt / .md). All local, all free.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from sqlmodel import Session, select

from ..core.config import Settings
from ..core.errors import AppError
from ..db.models import KnowledgeDocument
from ..schemas.knowledge import (
    KnowledgeImportRequest,
    KnowledgeStatusResponse,
    SearchResultItem,
)
from ..utils.text import chunk_text
from .chroma_service import ChromaService
from .embeddings import embedding_label

logger = logging.getLogger("evano.agent_engine.knowledge")


class KnowledgeService:
    def __init__(self, session: Session, settings: Settings, chroma: ChromaService) -> None:
        self._session = session
        self._settings = settings
        self._chroma = chroma

    def status(self) -> KnowledgeStatusResponse:
        available, message = self._chroma.availability()
        document_count = len(self.list_documents())
        chunk_count = 0
        if available:
            try:
                chunk_count = self._chroma.count()
            except Exception:  # noqa: BLE001
                chunk_count = 0
        return KnowledgeStatusResponse(
            available=available,
            embedding=embedding_label(self._settings),
            path=str(self._settings.chroma_path),
            collection=self._settings.chroma_collection,
            document_count=document_count,
            chunk_count=chunk_count,
            message=message,
        )

    def list_documents(self) -> list[KnowledgeDocument]:
        return list(
            self._session.exec(
                select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
            ).all()
        )

    def get_document(self, document_id: int) -> KnowledgeDocument | None:
        return self._session.get(KnowledgeDocument, document_id)

    def import_document(self, data: KnowledgeImportRequest) -> KnowledgeDocument:
        # Verify ChromaDB is available before creating any state.
        available, message = self._chroma.availability()
        if not available:
            raise AppError(
                message or "ChromaDB is not available locally.",
                status_code=503,
                code="chromadb_unavailable",
            )

        chunks = chunk_text(
            data.content,
            size=self._settings.chunk_size,
            overlap=self._settings.chunk_overlap,
        )
        if not chunks:
            raise AppError("The document has no text content.", status_code=400, code="empty_document")

        document = KnowledgeDocument(
            title=data.title,
            file_name=data.file_name,
            source_path=data.source_path,
            collection_name=self._settings.chroma_collection,
            chunk_count=0,
        )
        self._session.add(document)
        self._session.commit()
        self._session.refresh(document)

        try:
            self._chroma.add_chunks(
                document.id,  # type: ignore[arg-type]
                chunks,
                title=data.title,
                file_name=data.file_name,
            )
        except Exception as exc:  # noqa: BLE001 - roll back the metadata row
            self._session.delete(document)
            self._session.commit()
            raise AppError(
                f"Failed to index the document: {exc}",
                status_code=500,
                code="index_failed",
            ) from exc

        document.chunk_count = len(chunks)
        self._session.add(document)
        self._session.commit()
        self._session.refresh(document)
        logger.info(
            "knowledge document imported: %s (%d chunks)", data.file_name, len(chunks)
        )
        self._maybe_sync()
        return document

    def delete_document(self, document_id: int) -> bool:
        document = self._session.get(KnowledgeDocument, document_id)
        if document is None:
            return False
        try:
            self._chroma.delete_document(document_id)
        except Exception:  # noqa: BLE001 - still remove the metadata row
            pass
        self._session.delete(document)
        self._session.commit()
        self._maybe_sync()
        return True

    def _maybe_sync(self) -> None:
        """Auto-mirror the KB into agent memories after a change. Skipped under
        tests so they never touch real OpenClaw workspaces."""
        if self._settings.environment == "test":
            return
        try:
            self.sync_to_agents()
        except Exception:  # noqa: BLE001 - sync must never break import/delete
            pass

    def search(self, query: str, top_k: int | None = None) -> list[SearchResultItem]:
        k = top_k or self._settings.rag_top_k
        hits = self._chroma.search(query, k)
        return [SearchResultItem(**hit) for hit in hits]

    # ---- sync to OpenClaw agent memory ---------------------------------- #
    # KB docs are mirrored as memory files in every OpenClaw agent workspace
    # (memory/evano-kb-*.md). OpenClaw's own memory_search indexes them, so
    # agents keep this knowledge on channels Evano can't intercept — Discord,
    # the dashboard, and Org Chart sub-agent runs.

    _KB_FILE_RE = re.compile(r"^evano-kb-\d+-.*\.md$")

    def sync_to_agents(self) -> dict:
        """Mirror all KB documents into every agent's memory folder. Best-effort:
        returns a summary, never raises."""
        from .openclaw_service import OpenClawService, process as oc_process

        svc = OpenClawService()
        agents_res = svc.list_agents()
        if not agents_res.get("ok"):
            return {"ok": False, "agents_synced": 0, "files_written": 0,
                    "message": agents_res.get("message") or "OpenClaw isn't ready."}

        documents = self.list_documents()
        files: dict[str, str] = {}
        for doc in documents:
            try:
                text = self._chroma.get_document_text(doc.id)  # type: ignore[arg-type]
            except Exception:  # noqa: BLE001
                continue
            if not text.strip():
                continue
            safe = re.sub(r"[^A-Za-z0-9_-]+", "-", (doc.file_name or doc.title or "doc"))[:60].strip("-")
            files[f"evano-kb-{doc.id}-{safe}.md"] = (
                f"# {doc.title}\n\n"
                "<!-- Synced from the Evano Studio Knowledge Base. Do not edit — "
                "changes are overwritten on the next sync. -->\n\n"
                f"{text}\n"
            )

        synced = 0
        written = 0
        for agent in agents_res.get("agents") or []:
            ws = agent.get("workspace")
            if not ws:
                continue
            memory_dir = Path(ws) / "memory"
            try:
                memory_dir.mkdir(parents=True, exist_ok=True)
                # Remove KB mirrors that no longer exist in the KB.
                for old in memory_dir.glob("evano-kb-*.md"):
                    if self._KB_FILE_RE.match(old.name) and old.name not in files:
                        old.unlink(missing_ok=True)
                for name, content in files.items():
                    target = memory_dir / name
                    if not target.exists() or target.read_text(encoding="utf-8") != content:
                        target.write_text(content, encoding="utf-8")
                        written += 1
                synced += 1
                # Ask OpenClaw to reindex this agent's memory (best-effort).
                oc_process._run(["openclaw", "memory", "index", "--agent", agent["id"]], timeout=60)
            except OSError:
                continue

        logger.info("knowledge sync: %d docs → %d agents (%d files written)", len(files), synced, written)
        return {
            "ok": True,
            "agents_synced": synced,
            "files_written": written,
            "message": f"{len(files)} document(s) synced to {synced} agent(s).",
        }

    def context_block(self, query: str) -> str:
        """A bounded, ready-to-prepend context block for the query — or "".

        Used to give knowledge-base awareness to chats that take a single
        message string (e.g. OpenClaw agents). Never raises: no KB, no
        ChromaDB, or an indexing error simply yields no context.
        """
        try:
            hits = self.search(query)
        except Exception:  # noqa: BLE001 - RAG must never break chat
            return ""
        parts: list[str] = []
        total = 0
        budget = self._settings.rag_max_context_chars
        for hit in hits:
            text = (hit.text or "").strip()
            if not text:
                continue
            remaining = budget - total
            if remaining <= 0:
                break
            snippet = text[:remaining]
            label = hit.title or hit.file_name or "source"
            parts.append(f"[{label}]\n{snippet}")
            total += len(snippet)
        if not parts:
            return ""
        return (
            "Context from the user's local knowledge base — use it only if it is "
            "relevant to the request, otherwise ignore it:\n\n"
            + "\n\n".join(parts)
            + "\n\n---\n\n"
        )
