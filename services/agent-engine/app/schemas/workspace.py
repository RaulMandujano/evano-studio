"""Schemas for the workspace setup endpoints."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class WorkspaceSubdir(BaseModel):
    name: str
    exists: bool


class WorkspaceStatusResponse(BaseModel):
    """Current state of the configured workspace folder."""

    path: str
    # True when the user has explicitly chosen a workspace (vs. the default).
    configured: bool
    exists: bool
    is_default: bool
    default_path: str
    subdirs: list[WorkspaceSubdir] = Field(default_factory=list)
    # True when the folder exists and all standard subfolders are present.
    ready: bool
    message: Optional[str] = None


class WorkspaceConfigureRequest(BaseModel):
    """Set (or reset) the workspace folder.

    When ``path`` is empty/omitted the workspace is reset to the default
    location. A non-empty path is validated and its standard subfolders created.
    """

    path: str = ""
