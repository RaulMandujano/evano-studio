"""Workspace setup endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..schemas.workspace import WorkspaceConfigureRequest, WorkspaceStatusResponse
from ..services.workspace_service import WorkspaceService
from .deps import get_workspace_service

router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.get("/status", response_model=WorkspaceStatusResponse, summary="Workspace status")
def workspace_status(
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceStatusResponse:
    return service.status()


@router.post("/configure", response_model=WorkspaceStatusResponse, summary="Configure workspace")
def configure_workspace(
    payload: WorkspaceConfigureRequest,
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceStatusResponse:
    """Set (or reset) the workspace folder and create its standard subfolders."""
    return service.configure(payload)
