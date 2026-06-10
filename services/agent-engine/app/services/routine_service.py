"""Routine service — CRUD, run-now, and calendar event assembly."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Session, select

from ..core.config import Settings
from ..core.errors import AppError
from ..db.models import Agent, Routine, RoutineRun
from ..schemas.routine import CalendarEvent, RoutineCreate, RoutineUpdate
from .routine_runner import execute_routine
from .scheduling import compute_next_run, to_naive_local, validate_schedule


class RoutineService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    # ---- helpers --------------------------------------------------------- #

    def _require_agent(self, agent_id: int) -> None:
        if self._session.get(Agent, agent_id) is None:
            raise AppError("Agent not found.", status_code=400, code="invalid_agent")

    def _refresh_schedule(self, routine: Routine) -> None:
        validate_schedule(routine.schedule_type, routine.schedule_value, routine.start_at)
        routine.next_run_at = compute_next_run(routine, datetime.now())
        if not routine.is_enabled:
            routine.status = "disabled"
        elif routine.schedule_type == "manual":
            routine.status = "manual"
        elif routine.next_run_at is not None:
            routine.status = "scheduled"
        else:
            routine.status = "idle"

    # ---- CRUD ------------------------------------------------------------ #

    def list_routines(self) -> list[Routine]:
        return list(
            self._session.exec(select(Routine).order_by(Routine.created_at.desc())).all()
        )

    def get_routine(self, routine_id: int) -> Routine | None:
        return self._session.get(Routine, routine_id)

    def recent_runs(self, routine_id: int, limit: int = 10) -> list[RoutineRun]:
        return list(
            self._session.exec(
                select(RoutineRun)
                .where(RoutineRun.routine_id == routine_id)
                .order_by(RoutineRun.created_at.desc())
                .limit(limit)
            ).all()
        )

    def create_routine(self, data: RoutineCreate) -> Routine:
        # A Team or OpenClaw-agent routine doesn't use a built-in agent; otherwise
        # the built-in agent must exist.
        if data.team_id is not None or data.openclaw_agent_id:
            agent_id = 0
        else:
            self._require_agent(data.agent_id)
            agent_id = data.agent_id
        routine = Routine(
            name=data.name,
            agent_id=agent_id,
            openclaw_agent_id=data.openclaw_agent_id,
            team_id=data.team_id,
            prompt=data.prompt,
            schedule_type=data.schedule_type,
            schedule_value=data.schedule_value,
            start_at=to_naive_local(data.start_at),
            end_at=to_naive_local(data.end_at),
            is_enabled=data.is_enabled,
        )
        self._refresh_schedule(routine)
        self._session.add(routine)
        self._session.commit()
        self._session.refresh(routine)
        return routine

    def update_routine(self, routine_id: int, data: RoutineUpdate) -> Routine | None:
        routine = self._session.get(Routine, routine_id)
        if routine is None:
            return None
        values = data.model_dump(exclude_unset=True)
        if "agent_id" in values:
            self._require_agent(values["agent_id"])
        for key in ("start_at", "end_at"):
            if key in values:
                values[key] = to_naive_local(values[key])
        for key, value in values.items():
            setattr(routine, key, value)
        routine.updated_at = datetime.now()
        self._refresh_schedule(routine)
        self._session.add(routine)
        self._session.commit()
        self._session.refresh(routine)
        return routine

    def delete_routine(self, routine_id: int) -> bool:
        routine = self._session.get(Routine, routine_id)
        if routine is None:
            return False
        # Remove its run history too.
        for run in self._session.exec(
            select(RoutineRun).where(RoutineRun.routine_id == routine_id)
        ).all():
            self._session.delete(run)
        self._session.delete(routine)
        self._session.commit()
        return True

    def run_now(self, routine_id: int) -> RoutineRun | None:
        routine = self._session.get(Routine, routine_id)
        if routine is None:
            return None
        return execute_routine(self._session, self._settings, routine, trigger="manual")

    # ---- calendar -------------------------------------------------------- #

    def calendar_events(self, run_limit: int = 100) -> list[CalendarEvent]:
        events: list[CalendarEvent] = []

        # Upcoming scheduled runs (one per enabled routine).
        for routine in self.list_routines():
            if routine.is_enabled and routine.next_run_at is not None:
                events.append(
                    CalendarEvent(
                        routine_id=routine.id,  # type: ignore[arg-type]
                        routine_name=routine.name,
                        type="scheduled",
                        time=routine.next_run_at,
                        status="scheduled",
                    )
                )

        # Past runs (success / error / missed).
        runs = self._session.exec(
            select(RoutineRun).order_by(RoutineRun.created_at.desc()).limit(run_limit)
        ).all()
        names = {r.id: r.name for r in self.list_routines()}
        for run in runs:
            when = run.started_at or run.created_at
            events.append(
                CalendarEvent(
                    routine_id=run.routine_id,
                    routine_name=names.get(run.routine_id, "(deleted routine)"),
                    type=run.status,
                    time=when,
                    status=run.status,
                    message=run.error,
                )
            )
        return events
