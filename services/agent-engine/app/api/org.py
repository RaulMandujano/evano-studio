"""Org chart endpoints — the chain of command between OpenClaw agents."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..schemas.org import OrgActionResult, OrgChartResponse, OrgSaveRequest
from ..services.org_service import OrgService
from .deps import get_org_service

router = APIRouter(prefix="/org", tags=["org"])


@router.get("/chart", response_model=OrgChartResponse, summary="The org chart")
def get_org_chart(service: OrgService = Depends(get_org_service)) -> dict:
    """All OpenClaw agents (with identity) + the saved reporting lines."""
    return service.get_chart()


@router.put("/chart", response_model=OrgActionResult, summary="Save + apply the org chart")
def save_org_chart(
    payload: OrgSaveRequest,
    service: OrgService = Depends(get_org_service),
) -> dict:
    """Validate the tree (one manager each, no loops), persist it, and apply it to
    OpenClaw: per-manager delegation allowlists, team notes in AGENTS.md, and a
    safe spawn depth. Managers can then command their teams — including from Discord."""
    return service.save_chart([l.model_dump() for l in payload.links])
