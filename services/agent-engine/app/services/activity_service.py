"""Live agent activity tracking for the Office view.

A small in-memory, thread-safe record of "who is working on what right now",
plus a short history of recently finished work. Nothing is persisted — this is
presence data for the visual office, not an audit log (routine runs and the
backend logs already cover auditing).

Agent ids are namespaced so OpenClaw agents and built-in agents never collide:
``openclaw:<slug>`` and ``builtin:<db id>``.
"""

from __future__ import annotations

import threading
from collections import deque
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

_MAX_RECENT = 60
_MAX_TASK_CHARS = 160
_MAX_NOTE_CHARS = 200


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Activity:
    """One unit of agent work (a chat turn, a team step, a routine run)."""

    id: int
    agent_id: str  # namespaced: "openclaw:main" | "builtin:3"
    agent_name: str
    kind: str  # chat | team | routine
    task: str  # short human-readable description
    status: str = "working"  # working | done | error
    started_at: str = field(default_factory=_now_iso)
    finished_at: str | None = None
    note: str = ""


class ActivityTracker:
    """Thread-safe registry of active + recently finished activities."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._next_id = 1
        self._active: dict[int, Activity] = {}
        self._recent: deque[Activity] = deque(maxlen=_MAX_RECENT)

    def begin(self, *, agent_id: str, agent_name: str, kind: str, task: str) -> int:
        with self._lock:
            activity = Activity(
                id=self._next_id,
                agent_id=agent_id,
                agent_name=agent_name,
                kind=kind,
                task=task[:_MAX_TASK_CHARS],
            )
            self._next_id += 1
            self._active[activity.id] = activity
            return activity.id

    def end(self, activity_id: int, *, ok: bool = True, note: str = "") -> None:
        with self._lock:
            activity = self._active.pop(activity_id, None)
            if activity is None:
                return
            activity.status = "done" if ok else "error"
            activity.finished_at = _now_iso()
            activity.note = note[:_MAX_NOTE_CHARS]
            self._recent.appendleft(activity)

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "active": [asdict(a) for a in self._active.values()],
                "recent": [asdict(a) for a in self._recent],
                "generated_at": _now_iso(),
            }


# One tracker per backend process — every worker (API requests, the routine
# scheduler thread, team runs) reports into the same office.
_tracker = ActivityTracker()


def get_activity_tracker() -> ActivityTracker:
    return _tracker


@contextmanager
def track(*, agent_id: str, agent_name: str, kind: str, task: str) -> Iterator[dict]:
    """Record one activity around a block of work.

    Yields a mutable outcome dict — set ``outcome["ok"]`` / ``outcome["note"]``
    before the block ends. An unhandled exception marks the activity failed.
    """
    tracker = get_activity_tracker()
    activity_id = tracker.begin(agent_id=agent_id, agent_name=agent_name, kind=kind, task=task)
    outcome: dict = {"ok": True, "note": ""}
    try:
        yield outcome
    except BaseException:
        tracker.end(activity_id, ok=False, note="Stopped by an unexpected error.")
        raise
    else:
        tracker.end(activity_id, ok=bool(outcome.get("ok", True)), note=str(outcome.get("note") or ""))
