"""Health endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..schemas.system import HealthResponse
from ..services.system_service import SystemService
from .deps import get_system_service

router = APIRouter(tags=["meta"])


@router.get("/health", response_model=HealthResponse, summary="Liveness / health check")
def get_health(service: SystemService = Depends(get_system_service)) -> HealthResponse:
    """Return ``ok`` if the service is up. Used by the desktop app on startup."""
    return service.health()
