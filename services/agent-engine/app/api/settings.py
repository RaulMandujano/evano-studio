"""Settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..schemas.settings import SettingsResponse, SettingsUpdateRequest
from ..services.settings_service import SettingsService
from .deps import get_settings_service

router = APIRouter(tags=["settings"])


@router.get("/settings", response_model=SettingsResponse, summary="Get all settings")
def get_settings_endpoint(
    service: SettingsService = Depends(get_settings_service),
) -> SettingsResponse:
    return SettingsResponse(settings=service.get_all())


@router.put("/settings", response_model=SettingsResponse, summary="Create/update settings")
def put_settings_endpoint(
    payload: SettingsUpdateRequest,
    service: SettingsService = Depends(get_settings_service),
) -> SettingsResponse:
    """Merge the provided key/value settings and return the full set."""
    return SettingsResponse(settings=service.upsert_many(payload.settings))
