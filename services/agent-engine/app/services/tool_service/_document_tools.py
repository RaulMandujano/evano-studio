"""Document / knowledge tools (markdown, report, Word, PDF, RAG search)."""
from __future__ import annotations

from pathlib import Path

from ...core.errors import AppError
from ...core.paths import resolve_subpath, sanitize_filename
from ...db.models import Agent
from ...schemas.document import DocumentCreate
from ..chroma_service import ChromaService
from ..document_service import DocumentService
from ..knowledge_service import KnowledgeService


class DocumentToolsMixin:
    def _tool_create_markdown_document(self, params: dict, agent: Agent | None) -> dict:
        return self._create_document(params, agent, file_type="md", tool_id="create_markdown_document")

    def _tool_create_text_report(self, params: dict, agent: Agent | None) -> dict:
        return self._create_document(params, agent, file_type="txt", tool_id="create_text_report")

    def _create_document(
        self, params: dict, agent: Agent | None, *, file_type: str, tool_id: str
    ) -> dict:
        documents = DocumentService(self._session, self._settings)
        document = documents.create_document(
            DocumentCreate(
                title=str(params["title"]),
                content=str(params["content"]),
                file_type=file_type,  # type: ignore[arg-type]
                created_by_agent_id=agent.id if agent is not None else None,
            )
        )
        # Verify on disk and return the unified file-tool contract.
        return self._verified_file_result(
            tool_id,
            Path(document.file_path),
            extra={
                "id": document.id,
                "title": document.title,
                "file_name": document.file_name,
                "file_path": document.file_path,
            },
        )

    def _tool_create_word_document(self, params: dict, agent: Agent | None) -> dict:
        return self._create_export(params, builder="docx", ext=".docx", tool_id="create_word_document")

    def _tool_create_pdf_document(self, params: dict, agent: Agent | None) -> dict:
        return self._create_export(params, builder="pdf", ext=".pdf", tool_id="create_pdf_document")

    def _create_export(self, params: dict, *, builder: str, ext: str, tool_id: str) -> dict:
        from ..document_export import build_docx, build_pdf

        title = str(params["title"]).strip()
        content = str(params.get("content", ""))
        folder = str(params.get("folder", "")).strip()
        base = sanitize_filename(title) or "document"
        if not base.lower().endswith(ext):
            base = f"{base}{ext}"
        relative = f"{folder}/{base}" if folder else base
        target = resolve_subpath(self._workspace, relative)
        if target.exists():
            raise AppError("A file with that name already exists.", status_code=409, code="already_exists")
        self._safe_io(lambda: target.parent.mkdir(parents=True, exist_ok=True))
        data = build_docx(title, content) if builder == "docx" else build_pdf(title, content)
        self._safe_io(lambda: target.write_bytes(data))
        return self._verified_file_result(tool_id, target, extra={"title": title})

    def _tool_search_knowledge_base(self, params: dict, agent: Agent | None) -> dict:
        chroma = ChromaService(self._settings)
        available, message = chroma.availability()
        if not available:
            return {"results": [], "message": message}
        knowledge = KnowledgeService(self._session, self._settings, chroma)
        top_k = params.get("top_k")
        try:
            top_k = int(top_k) if top_k not in (None, "") else None
        except (TypeError, ValueError):
            top_k = None
        results = knowledge.search(str(params["query"]), top_k)
        return {
            "results": [
                {
                    "text": r.text,
                    "title": r.title,
                    "file_name": r.file_name,
                    "distance": r.distance,
                }
                for r in results
            ]
        }
