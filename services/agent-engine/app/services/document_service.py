"""Document service — create/list/read/delete local documents (no HTTP here).

Security: every file lives directly inside the workspace. File names are
sanitized and resolved within the workspace root; traversal and arbitrary paths
are rejected. Existing files are never overwritten unless explicitly allowed.
"""

from __future__ import annotations

import html
import logging
from pathlib import Path

from sqlmodel import Session, select

from ..core.config import Settings
from ..core.errors import AppError
from ..core.paths import is_within, resolve_within, sanitize_filename
from ..core.workspace import effective_workspace
from ..db.models import Document
from ..schemas.document import DocumentCreate

logger = logging.getLogger("evano.agent_engine.documents")

_EXTENSIONS = {"md": ".md", "txt": ".txt", "html": ".html"}


class DocumentService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self._session = session
        self._root = effective_workspace(session, settings)

    # ---- helpers --------------------------------------------------------- #

    def _ensure_root(self) -> Path:
        self._root.mkdir(parents=True, exist_ok=True)
        return self._root

    def _build_filename(self, data: DocumentCreate) -> str:
        ext = _EXTENSIONS[data.file_type]
        base = sanitize_filename(data.file_name or data.title)
        if base.lower().endswith(ext):
            base = base[: -len(ext)]
        base = base.strip(". ") or "document"
        return f"{base}{ext}"

    def _render(self, data: DocumentCreate) -> str:
        if data.file_type != "html":
            return data.content
        stripped = data.content.lstrip().lower()
        if stripped.startswith("<!doctype") or stripped.startswith("<html"):
            return data.content  # already a full document
        return self._html_report(data.title, data.content)

    @staticmethod
    def _html_report(title: str, content: str) -> str:
        safe_title = html.escape(title)
        blocks = []
        for block in content.split("\n\n"):
            text = block.strip()
            if not text:
                continue
            blocks.append("<p>" + html.escape(text).replace("\n", "<br>\n") + "</p>")
        body = "\n".join(blocks) or "<p></p>"
        return (
            "<!doctype html>\n"
            '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            f"<title>{safe_title}</title>\n"
            "<style>body{font-family:system-ui,Arial,sans-serif;max-width:760px;"
            "margin:40px auto;padding:0 20px;line-height:1.6;color:#1a1a1a}"
            "h1{font-size:1.6rem}</style>\n</head>\n<body>\n"
            f"<h1>{safe_title}</h1>\n{body}\n</body>\n</html>\n"
        )

    # ---- public API ------------------------------------------------------ #

    def create_document(self, data: DocumentCreate) -> Document:
        self._ensure_root()
        file_name = self._build_filename(data)
        target = resolve_within(self._root, file_name)  # raises on traversal

        if target.exists() and not data.overwrite:
            raise AppError(
                f"A document named '{file_name}' already exists.",
                status_code=409,
                code="file_exists",
            )

        target.write_text(self._render(data), encoding="utf-8")

        document = Document(
            title=data.title,
            file_name=file_name,
            file_type=data.file_type,
            file_path=str(target),
            created_by_agent_id=data.created_by_agent_id,
        )
        self._session.add(document)
        self._session.commit()
        self._session.refresh(document)
        logger.info("document created: %s (%s)", file_name, data.file_type)
        return document

    def list_documents(self) -> list[Document]:
        return list(
            self._session.exec(select(Document).order_by(Document.created_at.desc())).all()
        )

    def get_document(self, document_id: int) -> Document | None:
        return self._session.get(Document, document_id)

    def read_content(self, document: Document) -> str:
        path = Path(document.file_path)
        if not path.exists():
            raise AppError(
                "The document file is missing on disk.",
                status_code=404,
                code="file_missing",
            )
        return path.read_text(encoding="utf-8")

    def delete_document(self, document_id: int) -> bool:
        document = self._session.get(Document, document_id)
        if document is None:
            return False
        # Only delete the file if it is safely inside the workspace.
        path = Path(document.file_path)
        if path.exists() and is_within(self._root, path):
            path.unlink()
        self._session.delete(document)
        self._session.commit()
        return True
