"""Easy Start setup-status endpoint (aggregated subsystem status)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..schemas.setup import SetupStatusResponse
from ..services.setup_service import SetupService
from .deps import get_setup_service

router = APIRouter(prefix="/setup", tags=["setup"])


@router.get("/status", response_model=SetupStatusResponse, summary="Aggregated setup status")
def setup_status(
    service: SetupService = Depends(get_setup_service),
) -> SetupStatusResponse:
    """One call returning the state of every onboarding step for Easy Start."""
    return service.status()
