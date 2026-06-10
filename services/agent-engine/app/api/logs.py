"""Logs and support-bundle endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from ..core.config import Settings
from ..core.logging import log_store
from ..db.session import get_session
from ..schemas.logs import LogEntry, LogsResponse, SupportBundleResponse
from ..services.support_service import build_support_bundle, write_support_bundle
from .deps import get_app_settings

logs_router = APIRouter(tags=["logs"])
support_router = APIRouter(prefix="/support", tags=["support"])


@logs_router.get("/logs", response_model=LogsResponse, summary="Recent backend logs")
def get_logs(
    limit: int = Query(200, ge=1, le=500),
    level: Optional[str] = Query(None),
    area: Optional[str] = Query(None),
) -> LogsResponse:
    entries = log_store.recent(limit=limit, level=level, area=area)
    return LogsResponse(entries=[LogEntry(**e) for e in entries])


@support_router.post("/bundle", response_model=SupportBundleResponse, summary="Export a support bundle")
def create_support_bundle(
    session=Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> SupportBundleResponse:
    """Build a privacy-respecting diagnostics bundle and write it locally."""
    bundle = build_support_bundle(session, settings)
    path = write_support_bundle(settings, bundle)
    return SupportBundleResponse(path=str(path), bundle=bundle)
