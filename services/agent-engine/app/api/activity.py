"""Live activity endpoint — who is working on what right now (Office view)."""

from __future__ import annotations

from fastapi import APIRouter

from ..schemas.activity import ActivitySnapshotResponse
from ..services.activity_service import get_activity_tracker

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=ActivitySnapshotResponse, summary="Live agent activity snapshot")
def activity_snapshot() -> dict:
    """In-memory presence data: active work + recently finished work. The desktop
    Office view polls this to animate agents at their desks."""
    return get_activity_tracker().snapshot()
