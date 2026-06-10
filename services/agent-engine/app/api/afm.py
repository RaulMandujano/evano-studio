"""AFM endpoints — where each agent's content lives on disk."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..schemas.afm import (
    AfmApplyRequest,
    AfmApplyResult,
    AfmArchiveRequest,
    AfmArchiveResult,
    AfmStatusResponse,
)
from ..services.afm_service import AFMService
from .deps import get_afm_service

router = APIRouter(prefix="/afm", tags=["afm"])


@router.get("/status", response_model=AfmStatusResponse, summary="AFM status")
def afm_status(service: AFMService = Depends(get_afm_service)) -> dict:
    """Current root, and per-agent/per-team folder placement."""
    return service.status()


@router.post("/apply", response_model=AfmApplyResult, summary="Choose the root and organize")
def afm_apply(
    payload: AfmApplyRequest,
    service: AFMService = Depends(get_afm_service),
) -> dict:
    """Point every agent's OpenClaw workspace at <root>/Agents/<Name> (moving the
    existing files), scaffold Teams folders, and reload the gateway."""
    return service.apply(payload.root)


@router.post("/archive-team-run", response_model=AfmArchiveResult, summary="Save a team run")
def afm_archive_team_run(
    payload: AfmArchiveRequest,
    service: AFMService = Depends(get_afm_service),
) -> dict:
    """Store each member's step output and the final result under Teams/<Team>/."""
    return service.archive_team_run(
        team_name=payload.team_name,
        steps=[s.model_dump() for s in payload.steps],
        final=payload.final,
    )
