"""Database status endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..schemas.database import DatabaseStatusResponse
from ..services.database_service import DatabaseService
from .deps import get_database_service

router = APIRouter(prefix="/database", tags=["database"])


@router.get("/status", response_model=DatabaseStatusResponse, summary="Local database status")
def get_database_status(
    service: DatabaseService = Depends(get_database_service),
) -> DatabaseStatusResponse:
    return service.status()
