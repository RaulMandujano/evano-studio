"""Resolve and manage the effective workspace directory.

The workspace is the ONLY place documents and file tools may read or write. It
defaults to ``settings.workspace_path`` but can be overridden by the user via the
``workspace_dir`` app setting (set from the desktop Settings / Easy Start pages).

A configured workspace has a standard folder structure so generated files land
in sensible places. See docs/TOOLS.md and docs/SECURITY.md.
"""

from __future__ import annotations

from pathlib import Path

from sqlmodel import Session

from .config import Settings
from .errors import AppError

# Standard subfolders created inside a configured workspace.
WORKSPACE_SUBDIRS: tuple[str, ...] = (
    "Documents",
    "Images",
    "KnowledgeBase",
    "Projects",
    "Reports",
    "Logs",
)

# The setting key that stores a user-chosen workspace path override.
WORKSPACE_SETTING_KEY = "workspace_dir"


def effective_workspace(session: Session, settings: Settings) -> Path:
    """Return the workspace path in use (user override, else the default)."""
    from ..db.models import AppSetting

    override = session.get(AppSetting, WORKSPACE_SETTING_KEY)
    if override is not None and override.value.strip():
        return Path(override.value.strip()).expanduser()
    return settings.workspace_path


def validate_workspace_path(raw_path: str) -> Path:
    """Validate a user-supplied workspace path and return it expanded.

    Rejects empty paths, non-absolute paths, filesystem roots, and paths that
    point at an existing *file*. Does not create anything. Raises AppError with
    a clear, user-facing message on failure.
    """
    value = (raw_path or "").strip()
    if not value:
        raise AppError("Please choose a workspace folder.", status_code=400, code="invalid_path")

    path = Path(value).expanduser()
    if not path.is_absolute():
        raise AppError(
            "The workspace path must be an absolute folder path.",
            status_code=400,
            code="invalid_path",
        )

    resolved = path.resolve()
    if resolved.parent == resolved:
        # e.g. "/" or "C:\\" — refuse to use a filesystem root as the workspace.
        raise AppError(
            "Please choose a specific folder, not a drive/filesystem root.",
            status_code=400,
            code="invalid_path",
        )
    if resolved.exists() and not resolved.is_dir():
        raise AppError(
            "That path points to a file, not a folder.",
            status_code=400,
            code="invalid_path",
        )
    return resolved


def ensure_workspace_structure(workspace: Path) -> list[str]:
    """Create the workspace folder and its standard subfolders (idempotent).

    Returns the list of subfolder names that now exist. Raises AppError if the
    folders can't be created (e.g. permission denied).
    """
    try:
        workspace.mkdir(parents=True, exist_ok=True)
        for name in WORKSPACE_SUBDIRS:
            (workspace / name).mkdir(exist_ok=True)
    except OSError as exc:
        raise AppError(
            f"Couldn't create the workspace folders: {exc}",
            status_code=400,
            code="workspace_create_failed",
        ) from exc
    return [name for name in WORKSPACE_SUBDIRS if (workspace / name).is_dir()]


def workspace_subdir_status(workspace: Path) -> dict[str, bool]:
    """Return {subfolder: exists} for each standard workspace subfolder."""
    return {name: (workspace / name).is_dir() for name in WORKSPACE_SUBDIRS}
