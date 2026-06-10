"""Agent documents mixin: the work files agents create in their workspaces.

Agents write their deliverables (reports, drafts, team working files) into
their own workspace folders. This mixin surfaces those files for the Documents
tab — excluding the agent's config/bootstrap files, memory, and skills, which
are managed elsewhere.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from . import metadata, process

logger = logging.getLogger("evano.agent_engine.openclaw")

# Workspace entries that are NOT work documents.
_EXCLUDED_FILES = set(metadata._AGENT_FILE_ORDER) | {"BOOT.md", "MEMORY.md"}
_EXCLUDED_DIRS = {"memory", "skills", "canvas", "sessions", "node_modules", "__pycache__"}

_TEXT_EXTENSIONS = {".md", ".txt", ".csv", ".json", ".html", ".log", ".yaml", ".yml"}
_MAX_FILES_PER_AGENT = 200
_MAX_PREVIEW_BYTES = 200_000


class AgentDocumentsMixin:
    def list_agent_documents(self) -> dict:
        """Work files of every agent, grouped — powers the Documents tab."""
        agents_res = self.list_agents()
        if not agents_res.get("ok"):
            return {"ok": False, "message": agents_res.get("message") or "", "agents": []}
        identities = self._config_identities()
        groups = []
        for agent in agents_res.get("agents") or []:
            ws = Path(agent["workspace"]) if agent.get("workspace") else None
            files = self._work_files(ws) if ws else []
            ident = identities.get(agent["id"], {})
            groups.append({
                "agent_id": agent["id"],
                "name": ident.get("name") or agent.get("name") or agent["id"],
                "emoji": ident.get("emoji") or "",
                "files": files,
            })
        groups.sort(key=lambda g: max((f["modified_at"] for f in g["files"]), default=0), reverse=True)
        return {"ok": True, "message": "", "agents": groups}

    def read_agent_document(self, agent_id: str, rel_path: str) -> dict:
        """Read a text work file from an agent's workspace (bounded, safe)."""
        target, error = self._resolve_work_file(agent_id, rel_path)
        if error:
            return {"ok": False, "message": error, "name": rel_path, "content": "", "truncated": False}
        if target.suffix.lower() not in _TEXT_EXTENSIONS:
            return {"ok": False, "message": "This file type can't be previewed — use Open location.",
                    "name": target.name, "content": "", "truncated": False}
        try:
            raw = target.read_bytes()[: _MAX_PREVIEW_BYTES + 1]
        except OSError as exc:
            return {"ok": False, "message": f"Couldn't read the file: {exc}", "name": target.name,
                    "content": "", "truncated": False}
        truncated = len(raw) > _MAX_PREVIEW_BYTES
        content = raw[:_MAX_PREVIEW_BYTES].decode("utf-8", errors="replace")
        return {"ok": True, "message": "", "name": target.name, "content": content, "truncated": truncated}

    def delete_agent_document(self, agent_id: str, rel_path: str) -> dict:
        target, error = self._resolve_work_file(agent_id, rel_path)
        if error:
            return {"ok": False, "message": error}
        try:
            target.unlink()
        except OSError as exc:
            return {"ok": False, "message": f"Couldn't delete the file: {exc}"}
        logger.info("agent document deleted agent=%s file=%s", agent_id, rel_path)
        return {"ok": True, "message": "Document deleted."}

    # ---- helpers --------------------------------------------------------- #

    def _work_files(self, ws: Path) -> list[dict]:
        if not ws.is_dir():
            return []
        files: list[dict] = []
        try:
            for path in sorted(ws.rglob("*")):
                if len(files) >= _MAX_FILES_PER_AGENT:
                    break
                if not path.is_file():
                    continue
                rel = path.relative_to(ws)
                parts = rel.parts
                if any(p.startswith(".") for p in parts):
                    continue  # hidden files / .git
                if parts[0] in _EXCLUDED_DIRS:
                    continue
                if len(parts) == 1 and parts[0] in _EXCLUDED_FILES:
                    continue
                try:
                    stat = path.stat()
                except OSError:
                    continue
                files.append({
                    "name": path.name,
                    "path": str(rel),
                    "size_bytes": stat.st_size,
                    "modified_at": int(stat.st_mtime * 1000),
                    "abs_path": str(path),
                })
        except OSError:
            return files
        files.sort(key=lambda f: f["modified_at"], reverse=True)
        return files

    def _resolve_work_file(self, agent_id: str, rel_path: str) -> tuple[Path, str | None]:
        """Resolve a relative path inside the agent workspace; refuse escapes and
        config files. Returns (path, error)."""
        if process._which("openclaw") is None:
            return Path(), "Install OpenClaw first."
        ws = self._agent_workspace(agent_id)
        if ws is None or not ws.exists():
            return Path(), "Couldn't find this agent's workspace."
        rel = (rel_path or "").strip()
        if not rel or rel.startswith(("/", "~")):
            return Path(), "Invalid file path."
        candidate = (ws / rel)
        try:
            resolved = candidate.resolve()
            if not resolved.is_relative_to(ws.resolve()):
                return Path(), "Invalid file path."
        except OSError:
            return Path(), "Invalid file path."
        parts = candidate.relative_to(ws).parts
        if any(p.startswith(".") for p in parts) or parts[0] in _EXCLUDED_DIRS:
            return Path(), "That file is managed by the agent, not a document."
        if len(parts) == 1 and parts[0] in _EXCLUDED_FILES:
            return Path(), "That's an agent config file — edit it from the agent's page."
        if not resolved.is_file():
            return Path(), "File not found."
        return resolved, None
