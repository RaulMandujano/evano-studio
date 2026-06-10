"""Workspace-confined file tools (create/list/read/write/search)."""
from __future__ import annotations

import logging

from ...core.errors import AppError
from ...core.paths import resolve_subpath, resolve_within, sanitize_filename
from ...db.models import Agent
from .constants import (
    _READABLE_EXTENSIONS,
    _SEARCH_MAX_FILE_BYTES,
    _SEARCH_MAX_FILES,
    _SEARCH_MAX_MATCHES,
)

logger = logging.getLogger("evano.agent_engine.tools")


class FileToolsMixin:
    def _tool_create_folder(self, params: dict, agent: Agent | None) -> dict:
        parent = str(params.get("parent", "")).strip()
        folder_name = sanitize_filename(str(params["folder_name"]))
        relative = f"{parent}/{folder_name}" if parent else folder_name
        target = resolve_subpath(self._workspace, relative)
        logger.info("create_folder resolved: %s", target)
        if target.exists():
            raise AppError("That folder already exists.", status_code=409, code="already_exists")
        self._safe_io(lambda: target.mkdir(parents=True, exist_ok=False))
        # Verify the folder really exists before reporting success.
        if not target.is_dir():
            raise AppError(
                f"Folder verification failed: '{target.name}' was not created.",
                status_code=500,
                code="verify_failed",
            )
        rel = str(target.relative_to(self._workspace.resolve()))
        return {
            # Keep the original keys (path/relative_path) plus the verified fields.
            "success": True,
            "tool_name": "create_folder",
            "name": target.name,
            "path": str(target),
            "relative_path": rel,
            "absolute_path": str(target),
            "verified_exists": True,
            "message": f"Created folder {rel} in the workspace.",
        }

    def _tool_list_files(self, params: dict, agent: Agent | None) -> dict:
        rel = str(params.get("path", "")).strip()
        target = resolve_subpath(self._workspace, rel, require=False)
        if not target.exists():
            raise AppError("That folder doesn't exist.", status_code=404, code="not_found")
        if not target.is_dir():
            raise AppError("That path is a file, not a folder.", status_code=400, code="not_a_dir")
        entries = []
        for entry in sorted(target.iterdir(), key=lambda e: (e.is_file(), e.name.lower())):
            entries.append(
                {
                    "name": entry.name,
                    "type": "file" if entry.is_file() else "folder",
                    "size_bytes": entry.stat().st_size if entry.is_file() else None,
                }
            )
        return {"path": rel or ".", "entries": entries, "count": len(entries)}

    def _tool_create_text_file(self, params: dict, agent: Agent | None) -> dict:
        folder = str(params.get("folder", "")).strip()
        file_name = self._ensure_text_extension(sanitize_filename(str(params["file_name"])))
        relative = f"{folder}/{file_name}" if folder else file_name
        target = resolve_subpath(self._workspace, relative)
        logger.info("create_text_file resolved: %s", target)
        self._check_writable(target)
        if target.exists():
            raise AppError(
                "A file with that name already exists. Use write_text_file to overwrite.",
                status_code=409,
                code="already_exists",
            )
        self._safe_io(lambda: target.parent.mkdir(parents=True, exist_ok=True))
        content = str(params.get("content", ""))  # content optional → empty file is valid
        self._safe_io(lambda: target.write_text(content, encoding="utf-8"))
        return self._verified_file_result("create_text_file", target)

    def _tool_write_text_file(self, params: dict, agent: Agent | None) -> dict:
        target = resolve_subpath(self._workspace, str(params["path"]))
        logger.info("write_text_file resolved: %s", target)
        self._check_writable(target)
        existed = target.exists()
        self._safe_io(lambda: target.parent.mkdir(parents=True, exist_ok=True))
        self._safe_io(lambda: target.write_text(str(params["content"]), encoding="utf-8"))
        return self._verified_file_result("write_text_file", target, extra={"overwritten": existed})

    def _tool_read_text_file(self, params: dict, agent: Agent | None) -> dict:
        target = resolve_subpath(self._workspace, str(params["path"]))
        return self._read_text(target, str(params["path"]))

    def _tool_search_workspace(self, params: dict, agent: Agent | None) -> dict:
        query = str(params["query"]).strip()
        needle = query.lower()
        root = self._workspace.resolve()
        root.mkdir(parents=True, exist_ok=True)
        matches: list[dict] = []
        scanned = 0
        for path in sorted(root.rglob("*")):
            if len(matches) >= _SEARCH_MAX_MATCHES or scanned >= _SEARCH_MAX_FILES:
                break
            if not path.is_file() or path.suffix.lower() not in _READABLE_EXTENSIONS:
                continue
            scanned += 1
            rel = str(path.relative_to(root))
            name_match = needle in path.name.lower()
            snippet: str | None = None
            try:
                if path.stat().st_size <= _SEARCH_MAX_FILE_BYTES:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                    idx = text.lower().find(needle)
                    if idx != -1:
                        start = max(0, idx - 40)
                        snippet = text[start : idx + len(query) + 60].strip().replace("\n", " ")
            except OSError:
                continue
            if name_match or snippet is not None:
                matches.append({"file": rel, "name_match": name_match, "snippet": snippet})
        return {"query": query, "matches": matches, "count": len(matches), "files_scanned": scanned}

    # ---- back-compat / root-only file tools ----------------------------- #

    def _tool_list_allowed_files(self, params: dict, agent: Agent | None) -> dict:
        self._workspace.mkdir(parents=True, exist_ok=True)
        files = []
        for entry in sorted(self._workspace.iterdir()):
            if entry.is_file():
                files.append({"name": entry.name, "size_bytes": entry.stat().st_size})
        return {"files": files}

    def _tool_read_allowed_text_file(self, params: dict, agent: Agent | None) -> dict:
        file_name = str(params["file_name"])
        target = resolve_within(self._workspace, file_name)  # blocks traversal (flat only)
        return self._read_text(target, file_name)
