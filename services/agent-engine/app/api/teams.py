"""Team endpoints — CRUD for saved multi-agent workflows."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from ..core.errors import AppError
from ..db.models import Team
from ..schemas.team import DeleteResponse, TeamCreate, TeamRead, TeamUpdate
from ..services.team_service import TeamService
from .deps import get_team_service

router = APIRouter(prefix="/teams", tags=["teams"])


def _get_or_404(service: TeamService, team_id: int) -> Team:
    team = service.get_team(team_id)
    if team is None:
        raise AppError("Team not found.", status_code=status.HTTP_404_NOT_FOUND, code="not_found")
    return team


@router.get("", response_model=list[TeamRead], summary="List saved teams")
def list_teams(service: TeamService = Depends(get_team_service)) -> list[Team]:
    return service.list_teams()


@router.post("", response_model=TeamRead, status_code=status.HTTP_201_CREATED, summary="Create a team")
def create_team(payload: TeamCreate, service: TeamService = Depends(get_team_service)) -> Team:
    return service.create_team(payload)


@router.get("/{team_id}", response_model=TeamRead, summary="Get a team")
def get_team(team_id: int, service: TeamService = Depends(get_team_service)) -> Team:
    return _get_or_404(service, team_id)


@router.put("/{team_id}", response_model=TeamRead, summary="Update a team")
def update_team(team_id: int, payload: TeamUpdate, service: TeamService = Depends(get_team_service)) -> Team:
    _get_or_404(service, team_id)
    updated = service.update_team(team_id, payload)
    assert updated is not None
    return updated


@router.delete("/{team_id}", response_model=DeleteResponse, summary="Delete a team")
def delete_team(team_id: int, service: TeamService = Depends(get_team_service)) -> DeleteResponse:
    return DeleteResponse(ok=service.delete_team(team_id))
