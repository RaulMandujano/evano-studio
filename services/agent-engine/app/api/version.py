"""Version endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..schemas.system import VersionResponse
from ..services.system_service import SystemService
from .deps import get_system_service

router = APIRouter(tags=["meta"])


@router.get("/version", response_model=VersionResponse, summary="Service version")
def get_version(service: SystemService = Depends(get_system_service)) -> VersionResponse:
    """Return the service name, version, and environment."""
    return service.version()
