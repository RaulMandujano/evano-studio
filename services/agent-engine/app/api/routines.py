"""Routine CRUD, run-now, and calendar endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from ..core.errors import AppError
from ..db.models import Routine
from ..schemas.routine import (
    CalendarEventsResponse,
    DeleteResponse,
    RoutineCreate,
    RoutineDetail,
    RoutineRead,
    RoutineRunRead,
    RoutineUpdate,
)
from ..services.routine_service import RoutineService
from .deps import get_routine_service

router = APIRouter(prefix="/routines", tags=["routines"])
calendar_router = APIRouter(prefix="/calendar", tags=["calendar"])


def _get_or_404(service: RoutineService, routine_id: int) -> Routine:
    routine = service.get_routine(routine_id)
    if routine is None:
        raise AppError("Routine not found.", status_code=status.HTTP_404_NOT_FOUND, code="not_found")
    return routine


@router.get("", response_model=list[RoutineRead], summary="List routines")
def list_routines(service: RoutineService = Depends(get_routine_service)) -> list[RoutineRead]:
    return [RoutineRead.model_validate(r) for r in service.list_routines()]


@router.post(
    "",
    response_model=RoutineRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a routine",
)
def create_routine(
    payload: RoutineCreate,
    service: RoutineService = Depends(get_routine_service),
) -> RoutineRead:
    return RoutineRead.model_validate(service.create_routine(payload))


@router.get("/{routine_id}", response_model=RoutineDetail, summary="Get a routine (with runs)")
def get_routine(
    routine_id: int,
    service: RoutineService = Depends(get_routine_service),
) -> RoutineDetail:
    routine = _get_or_404(service, routine_id)
    runs = [RoutineRunRead.model_validate(r) for r in service.recent_runs(routine_id)]
    return RoutineDetail(**RoutineRead.model_validate(routine).model_dump(), recent_runs=runs)


@router.put("/{routine_id}", response_model=RoutineRead, summary="Update a routine")
def update_routine(
    routine_id: int,
    payload: RoutineUpdate,
    service: RoutineService = Depends(get_routine_service),
) -> RoutineRead:
    _get_or_404(service, routine_id)
    updated = service.update_routine(routine_id, payload)
    assert updated is not None
    return RoutineRead.model_validate(updated)


@router.delete("/{routine_id}", response_model=DeleteResponse, summary="Delete a routine")
def delete_routine(
    routine_id: int,
    service: RoutineService = Depends(get_routine_service),
) -> DeleteResponse:
    if not service.delete_routine(routine_id):
        raise AppError("Routine not found.", status_code=status.HTTP_404_NOT_FOUND, code="not_found")
    return DeleteResponse(ok=True)


@router.post(
    "/{routine_id}/run-now",
    response_model=RoutineRunRead,
    summary="Run a routine immediately",
)
def run_now(
    routine_id: int,
    service: RoutineService = Depends(get_routine_service),
) -> RoutineRunRead:
    _get_or_404(service, routine_id)
    run = service.run_now(routine_id)
    assert run is not None
    return RoutineRunRead.model_validate(run)


@calendar_router.get("/events", response_model=CalendarEventsResponse, summary="Calendar events")
def calendar_events(
    service: RoutineService = Depends(get_routine_service),
) -> CalendarEventsResponse:
    return CalendarEventsResponse(events=service.calendar_events())
