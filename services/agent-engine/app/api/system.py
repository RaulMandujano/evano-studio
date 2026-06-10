"""System info endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..schemas.system import SystemInfoResponse
from ..services.system_service import SystemService
from .deps import get_system_service

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info", response_model=SystemInfoResponse, summary="Runtime / system info")
def get_system_info(
    service: SystemService = Depends(get_system_service),
) -> SystemInfoResponse:
    """Return non-sensitive runtime info and available-feature flags."""
    return service.system_info()
