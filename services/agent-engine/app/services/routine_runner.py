"""Routine execution and the background scheduler.

Execution is fully logged (a RoutineRun row with visible output) — no hidden
actions. Routines only run while this process is running; runs missed while the
backend was closed are recorded as "missed", not silently executed late.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from ..core.config import Settings
from ..db.models import Agent, Routine, RoutineRun
from ..utils.time import utc_now
from .activity_service import track
from .ollama_service import OllamaService
from .scheduling import compute_next_run
from .tool_service import ToolService

logger = logging.getLogger("evano.agent_engine.routines")


def _schedule_status(routine: Routine) -> str:
    if not routine.is_enabled:
        return "disabled"
    if routine.schedule_type == "manual":
        return "manual"
    if routine.next_run_at is not None:
        return "scheduled"
    return "idle"


def execute_routine(
    session: Session,
    settings: Settings,
    routine: Routine,
    *,
    trigger: str,
) -> RoutineRun:
    """Run a routine now, logging the result. ``trigger`` is 'manual' or 'scheduled'."""
    now = datetime.now()
    run = RoutineRun(
        routine_id=routine.id,  # type: ignore[arg-type]
        trigger=trigger,
        status="running",
        started_at=now,
        output="",
    )

    if routine.team_id is not None:
        # Run a whole saved Team workflow autonomously (the relay, on the backend).
        from ..db.models import Team
        from .team_runner import run_team

        team = session.get(Team, routine.team_id)
        if team is None:
            run.status, run.error = "error", "Team not found."
        else:
            result = run_team(
                name=team.name, steps=team.steps,
                starting_input=routine.prompt, working_file=team.working_file,
            )
            if not result.get("ok"):
                run.status, run.error = "error", result.get("error") or "Team workflow failed."
                run.output = ""
            else:
                run.status = "success"
                run.output = result.get("final") or ""
                # File the run into the AFM Teams folder (best-effort).
                from .afm_service import AFMService

                try:
                    AFMService(session, settings).archive_team_run(
                        team_name=team.name,
                        steps=[
                            {"agent_id": s.get("agent_id", ""), "output": s.get("output", "")}
                            for s in result.get("steps") or []
                        ],
                        final=run.output,
                    )
                except Exception:  # noqa: BLE001 - archiving never breaks the run
                    pass
    elif routine.openclaw_agent_id:
        # Run an OpenClaw agent on schedule (its full toolset + Gemma 4). Uses the
        # same native one-shot path as the Agents chat — no gateway pairing needed.
        # Relevant local knowledge base content is prepended, like in chats.
        from .chroma_service import ChromaService
        from .knowledge_service import KnowledgeService
        from .openclaw_service import OpenClawService

        knowledge = KnowledgeService(session, settings, ChromaService(settings))
        prompt = knowledge.context_block(routine.prompt) + routine.prompt
        with track(
            agent_id=f"openclaw:{routine.openclaw_agent_id}",
            agent_name=routine.openclaw_agent_id,
            kind="routine",
            task=f'Routine "{routine.name}"',
        ) as outcome:
            result = OpenClawService().agent_chat(
                agent_id=routine.openclaw_agent_id, message=prompt
            )
            outcome["ok"] = bool(result.get("ok"))
            if not outcome["ok"]:
                outcome["note"] = result.get("message") or ""
        if not result.get("ok"):
            run.status, run.error = "error", result.get("message") or "OpenClaw agent failed."
        else:
            run.status = "success"
            run.output = result.get("reply") or ""
    elif (agent := session.get(Agent, routine.agent_id)) is None:
        run.status, run.error = "error", "Agent not found."
    elif not agent.is_enabled:
        run.status, run.error = "error", "Agent is disabled."
    else:
        messages: list[dict] = []
        if agent.system_prompt:
            messages.append({"role": "system", "content": agent.system_prompt})
        messages.append({"role": "user", "content": routine.prompt})
        with track(
            agent_id=f"builtin:{agent.id}",
            agent_name=agent.name,
            kind="routine",
            task=f'Routine "{routine.name}"',
        ) as outcome:
            result = OllamaService(settings).chat(agent.model_name, messages, agent.temperature)
            outcome["ok"] = result.ok
            if not result.ok:
                outcome["note"] = result.message or ""
        if not result.ok:
            run.status, run.error = "error", result.message
        else:
            run.status = "success"
            run.output = result.reply or ""
            # If the agent is allowed to create documents, save the output.
            if "create_markdown_document" in (agent.enabled_tools or []):
                try:
                    created = ToolService(session, settings).execute(
                        "create_markdown_document",
                        {
                            "title": f"{routine.name} — {now:%Y-%m-%d %H:%M}",
                            "content": run.output,
                        },
                        agent=agent,
                    )
                    run.document_path = created.get("file_path")
                except Exception as exc:  # noqa: BLE001
                    run.error = f"Document save failed: {exc}"

    run.finished_at = datetime.now()
    session.add(run)

    routine.last_run_at = now
    if trigger == "scheduled":
        routine.next_run_at = compute_next_run(routine, now)
        if run.status == "error":
            routine.status = "error"
        elif routine.next_run_at is not None:
            routine.status = "scheduled"
        else:
            routine.status = "done"
    else:
        routine.status = "error" if run.status == "error" else _schedule_status(routine)

    session.add(routine)
    session.commit()
    session.refresh(run)
    logger.info(
        "routine run: id=%s routine=%s trigger=%s status=%s",
        run.id,
        routine.id,
        trigger,
        run.status,
    )
    return run


class RoutineScheduler:
    """Background thread that runs due routines and records missed ones."""

    def __init__(self, engine: Engine, settings: Settings) -> None:
        self._engine = engine
        self._settings = settings
        self._interval = max(5, settings.routine_tick_seconds)
        self._grace = settings.routine_grace_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("routine scheduler started (interval=%ss)", self._interval)

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
        logger.info("routine scheduler stopped")

    def _loop(self) -> None:
        # Wait before the first tick so short-lived processes (tests) don't fire.
        while not self._stop.wait(self._interval):
            try:
                self._tick()
            except Exception as exc:  # noqa: BLE001
                logger.exception("routine scheduler tick failed: %s", exc)

    def _tick(self) -> None:
        now = datetime.now()
        with Session(self._engine) as session:
            due = session.exec(
                select(Routine).where(
                    Routine.is_enabled == True,  # noqa: E712
                    Routine.next_run_at != None,  # noqa: E711
                    Routine.next_run_at <= now,
                )
            ).all()
            for routine in due:
                scheduled_at = routine.next_run_at
                if scheduled_at is None:
                    continue
                if scheduled_at >= now - timedelta(seconds=self._grace):
                    execute_routine(session, self._settings, routine, trigger="scheduled")
                else:
                    self._mark_missed(session, routine, now)

    def _mark_missed(self, session: Session, routine: Routine, now: datetime) -> None:
        run = RoutineRun(
            routine_id=routine.id,  # type: ignore[arg-type]
            trigger="scheduled",
            status="missed",
            started_at=now,
            finished_at=now,
            output="",
            error="Missed — the backend was not running at the scheduled time.",
        )
        session.add(run)
        if routine.schedule_type == "once":
            routine.next_run_at = None
            routine.status = "missed"
        else:
            routine.next_run_at = compute_next_run(routine, now)
            routine.status = "scheduled" if routine.next_run_at else "missed"
        session.add(routine)
        session.commit()
        logger.info("routine missed: routine=%s", routine.id)
