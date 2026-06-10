"""Tool execution service: validate, dispatch, verify, and log every tool run."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from sqlmodel import Session, desc, select

from ...core.config import Settings
from ...core.errors import AppError
from ...core.workspace import effective_workspace
from ...db.models import Agent, ToolExecutionLog
from ...tools.registry import get_tool
from .constants import _BLOCKED_WRITE_EXTENSIONS, _MAX_READ_BYTES, _READABLE_EXTENSIONS
from ._computer_tools import ComputerToolsMixin
from ._document_tools import DocumentToolsMixin
from ._file_tools import FileToolsMixin

logger = logging.getLogger("evano.agent_engine.tools")


class ToolService(FileToolsMixin, DocumentToolsMixin, ComputerToolsMixin):
    """Executes curated local tools with strict, logged boundaries."""

    def __init__(self, session: Session, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._workspace = effective_workspace(session, settings)

    def execute(
        self,
        tool_id: str,
        params: dict[str, Any],
        *,
        agent: Agent | None = None,
        source: str = "manual",
    ) -> Any:
        spec = get_tool(tool_id)
        if spec is None:
            raise AppError(f"Unknown tool: {tool_id}", status_code=404, code="unknown_tool")

        action = self._action_for(tool_id, params)

        # Deny-by-default: an agent may only run tools it has been granted.
        permitted = agent is None or tool_id in (agent.enabled_tools or [])

        # Debug logging: active workspace, requested tool, permission result.
        logger.info(
            "tool execute: tool=%s source=%s agent=%s permitted=%s workspace=%s",
            tool_id,
            source,
            agent.id if agent is not None else "none",
            permitted,
            str(self._workspace),
        )

        if not permitted:
            self._record(tool_id, spec.name, agent, source, action, "error", "Tool not enabled")
            logger.warning("tool denied: tool=%s agent=%s (not enabled)", tool_id, agent.id)
            raise AppError(
                f"Tool '{tool_id}' is not enabled for this agent.",
                status_code=403,
                code="tool_not_enabled",
            )

        # Validate required parameters.
        for param in spec.parameters:
            if param.required and not str(params.get(param.name, "")).strip():
                self._record(
                    tool_id, spec.name, agent, source, action, "error",
                    f"Missing parameter: {param.name}",
                )
                logger.warning("tool param missing: tool=%s param=%s", tool_id, param.name)
                raise AppError(
                    f"Missing required parameter: {param.name}",
                    status_code=400,
                    code="invalid_params",
                )

        handler = getattr(self, f"_tool_{tool_id}")
        try:
            result = handler(params, agent)
        except AppError as exc:
            self._record(tool_id, spec.name, agent, source, action, "error", exc.message)
            logger.warning("tool failed: tool=%s error=%s", tool_id, exc.message)
            raise
        except Exception as exc:  # noqa: BLE001 - record then re-raise for the API layer
            self._record(tool_id, spec.name, agent, source, action, "error", str(exc))
            logger.exception("tool crashed: tool=%s", tool_id)
            raise

        detail = self._detail_for(tool_id, result)
        self._record(tool_id, spec.name, agent, source, action, "success", detail)
        logger.info("tool ok: tool=%s source=%s detail=%s", tool_id, source, detail)
        return result

    def _read_text(self, target: Path, label: str) -> dict:
        if not target.exists() or not target.is_file():
            raise AppError("File not found in workspace.", status_code=404, code="not_found")
        if target.suffix.lower() not in _READABLE_EXTENSIONS:
            raise AppError("Only text files can be read.", status_code=400, code="unsupported_type")
        if target.stat().st_size > _MAX_READ_BYTES:
            raise AppError("File is too large to read.", status_code=400, code="too_large")
        return {"path": label, "content": target.read_text(encoding="utf-8")}

    @staticmethod
    def _safe_io(action):
        """Run a filesystem action, turning OSError into a clean AppError."""
        try:
            return action()
        except OSError as exc:
            raise AppError(
                f"Filesystem error: {exc.strerror or exc}",
                status_code=400,
                code="io_error",
            ) from exc

    def _check_writable(self, target: Path) -> None:
        if target.suffix.lower() in _BLOCKED_WRITE_EXTENSIONS:
            raise AppError(
                f"For safety, '{target.suffix}' files can't be created here "
                "(executable/script types are blocked).",
                status_code=400,
                code="unsupported_type",
            )

    def _ensure_text_extension(self, name: str) -> str:
        # Keep the extension the user asked for (e.g. .doc, .csv); only add .txt
        # when there's no extension at all.
        return name if Path(name).suffix else f"{name}.txt"

    def _verified_file_result(
        self, tool_id: str, target: Path, *, extra: dict | None = None
    ) -> dict:
        """Verify a just-written file exists inside the workspace and return the
        unified file-tool result contract. Raises if verification fails so the
        caller (and the chat) reports a real failure instead of a false success.
        """
        root = self._workspace.resolve()
        target = target.resolve()
        # Defense in depth: the file must be inside the configured workspace.
        if target != root and root not in target.parents:
            raise AppError(
                "Refusing to report a file written outside the workspace.",
                status_code=400,
                code="invalid_path",
            )
        if not target.is_file():
            raise AppError(
                f"File verification failed: '{target.name}' was not found after writing.",
                status_code=500,
                code="verify_failed",
            )
        size = target.stat().st_size
        try:
            rel = str(target.relative_to(root))
        except ValueError:  # pragma: no cover - guarded above
            rel = target.name
        result = {
            "success": True,
            "tool_name": tool_id,
            "name": target.name,
            "relative_path": rel,
            "absolute_path": str(target),
            "bytes_written": size,
            "verified_exists": True,
            "message": f"Created {rel} ({size} bytes) in the workspace.",
        }
        if extra:
            result.update(extra)
        return result

    def _record(
        self,
        tool_id: str,
        tool_name: str,
        agent: Agent | None,
        source: str,
        action: str,
        status: str,
        detail: str | None,
    ) -> None:
        """Append a tool-execution log row. Never raises (logging must not break tools)."""
        try:
            self._session.add(
                ToolExecutionLog(
                    agent_id=agent.id if agent is not None else None,
                    agent_name=agent.name if agent is not None else None,
                    tool_id=tool_id,
                    tool_name=tool_name,
                    source=source,
                    action=action,
                    status=status,
                    detail=(detail or "")[:500] or None,
                )
            )
            self._session.commit()
        except Exception:  # noqa: BLE001
            self._session.rollback()

    def recent_logs(self, limit: int = 50) -> list[ToolExecutionLog]:
        limit = max(1, min(limit, 500))
        return list(
            self._session.exec(
                select(ToolExecutionLog).order_by(desc(ToolExecutionLog.created_at)).limit(limit)
            ).all()
        )

    @staticmethod
    def _action_for(tool_id: str, params: dict) -> str:
        p = params
        summaries = {
            "create_folder": lambda: f"Create folder '{p.get('folder_name', '')}'",
            "list_files": lambda: f"List files in '{p.get('path') or 'workspace root'}'",
            "create_text_file": lambda: f"Create file '{p.get('file_name', '')}'",
            "write_text_file": lambda: f"Write file '{p.get('path', '')}'",
            "read_text_file": lambda: f"Read file '{p.get('path', '')}'",
            "search_workspace": lambda: f"Search workspace for '{p.get('query', '')}'",
            "list_allowed_files": lambda: "List workspace files",
            "read_allowed_text_file": lambda: f"Read file '{p.get('file_name', '')}'",
            "create_markdown_document": lambda: f"Create document '{p.get('title', '')}'",
            "create_text_report": lambda: f"Create report '{p.get('title', '')}'",
            "create_word_document": lambda: f"Create Word document '{p.get('title', '')}'",
            "create_pdf_document": lambda: f"Create PDF document '{p.get('title', '')}'",
            "search_knowledge_base": lambda: f"Search knowledge base for '{p.get('query', '')}'",
            "generate_image_prompt": lambda: f"Compose image prompt for '{p.get('subject', '')}'",
            "open_application": lambda: f"Open application '{p.get('app_name', '')}'",
            "open_url": lambda: f"Open URL '{p.get('url', '')}'",
            "run_command": lambda: f"Run command: {p.get('command', '')}",
        }
        fn = summaries.get(tool_id)
        return fn() if fn else tool_id

    @staticmethod
    def _detail_for(tool_id: str, result: Any) -> str | None:
        if not isinstance(result, dict):
            return None
        if "relative_path" in result:
            return result["relative_path"]
        if "file_name" in result:
            return str(result["file_name"])
        if "count" in result:
            return f"{result['count']} item(s)"
        if "files" in result:
            return f"{len(result['files'])} file(s)"
        return None
