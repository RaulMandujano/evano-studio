"""Workspace service — configure and report the local workspace folder.

The workspace is the single writable location for documents and file tools. This
service validates a user-chosen path, creates the standard folder structure, and
reports current status. It never touches paths outside the chosen workspace.
"""

from __future__ import annotations

import logging

from sqlmodel import Session

from ..core.config import Settings
from ..core.workspace import (
    WORKSPACE_SETTING_KEY,
    effective_workspace,
    ensure_workspace_structure,
    validate_workspace_path,
    workspace_subdir_status,
)
from ..db.models import AppSetting
from ..schemas.workspace import (
    WorkspaceConfigureRequest,
    WorkspaceStatusResponse,
    WorkspaceSubdir,
)

logger = logging.getLogger("evano.agent_engine.system")


class WorkspaceService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    def status(self) -> WorkspaceStatusResponse:
        workspace = effective_workspace(self._session, self._settings)
        default = self._settings.workspace_path
        override = self._session.get(AppSetting, WORKSPACE_SETTING_KEY)
        configured = bool(override is not None and override.value.strip())
        exists = workspace.is_dir()
        subdir_map = workspace_subdir_status(workspace) if exists else {}
        subdirs = [WorkspaceSubdir(name=name, exists=ok) for name, ok in subdir_map.items()]
        ready = exists and all(subdir_map.values()) if subdir_map else False

        if not configured:
            message = "Using the default workspace. Choose a folder to organize your files."
        elif not exists:
            message = "The configured workspace folder no longer exists."
        elif not ready:
            message = "Workspace is missing some standard folders. Re-run setup to create them."
        else:
            message = None

        return WorkspaceStatusResponse(
            path=str(workspace),
            configured=configured,
            exists=exists,
            is_default=not configured,
            default_path=str(default),
            subdirs=subdirs,
            ready=ready,
            message=message,
        )

    def configure(self, payload: WorkspaceConfigureRequest) -> WorkspaceStatusResponse:
        """Set (or reset) the workspace folder and create its structure.

        An empty path resets to the default location (and still creates the
        default's standard subfolders).
        """
        raw = (payload.path or "").strip()
        if raw:
            workspace = validate_workspace_path(raw)
            # Create the structure FIRST so a failure (e.g. permission denied)
            # never leaves a broken override pointing at an unusable folder.
            ensure_workspace_structure(workspace)
            self._save_override(str(workspace))
            logger.info("workspace configured: %s", workspace)
        else:
            workspace = self._settings.workspace_path
            ensure_workspace_structure(workspace)
            self._clear_override()
            logger.info("workspace reset to default: %s", workspace)

        return self.status()

    # ---- internals ------------------------------------------------------- #

    def _save_override(self, value: str) -> None:
        existing = self._session.get(AppSetting, WORKSPACE_SETTING_KEY)
        if existing is not None:
            existing.value = value
            self._session.add(existing)
        else:
            self._session.add(AppSetting(key=WORKSPACE_SETTING_KEY, value=value))
        self._session.commit()

    def _clear_override(self) -> None:
        existing = self._session.get(AppSetting, WORKSPACE_SETTING_KEY)
        if existing is not None:
            self._session.delete(existing)
            self._session.commit()
