"""Schedule parsing and next-run computation for routines.

All times are naive LOCAL datetimes — this is a local desktop scheduler, not a
cloud calendar. Pure functions, easy to unit-test by passing ``now``.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from ..core.errors import AppError

if TYPE_CHECKING:
    from ..db.models import Routine

_DAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def to_naive_local(dt: datetime | None) -> datetime | None:
    """Normalize a datetime to naive local time (drop tzinfo if present)."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone().replace(tzinfo=None)
    return dt


def parse_time(value: str) -> tuple[int, int]:
    match = _TIME_RE.match(value.strip())
    if not match:
        raise AppError(
            "Time must be in HH:MM (24h) format.", status_code=400, code="invalid_schedule"
        )
    return int(match.group(1)), int(match.group(2))


def parse_weekly(value: str) -> tuple[int, int, int]:
    parts = value.strip().split()
    if len(parts) != 2 or parts[0].lower() not in _DAYS:
        raise AppError(
            "Weekly schedule must be like 'mon 09:00'.",
            status_code=400,
            code="invalid_schedule",
        )
    hour, minute = parse_time(parts[1])
    return _DAYS[parts[0].lower()], hour, minute


def validate_schedule(schedule_type: str, schedule_value: str, start_at: datetime | None) -> None:
    """Raise AppError if the schedule is invalid for its type."""
    if schedule_type == "manual":
        return
    if schedule_type == "once":
        if start_at is None:
            raise AppError(
                "A 'once' routine needs a start date/time.",
                status_code=400,
                code="invalid_schedule",
            )
        return
    if schedule_type == "daily":
        parse_time(schedule_value)
        return
    if schedule_type == "weekly":
        parse_weekly(schedule_value)
        return
    raise AppError(f"Unknown schedule type: {schedule_type}", status_code=400, code="invalid_schedule")


def compute_next_run(routine: "Routine", now: datetime) -> datetime | None:
    """Return the next run time (naive local), or None if not scheduled."""
    if not routine.is_enabled:
        return None

    st = routine.schedule_type
    if st == "manual":
        return None

    start = to_naive_local(routine.start_at) or now
    end = to_naive_local(routine.end_at)

    if st == "once":
        # Runs once at start; once it has run, it never reschedules.
        if routine.last_run_at is not None:
            return None
        candidate = start
    elif st == "daily":
        hour, minute = parse_time(routine.schedule_value)
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        while candidate < start:
            candidate += timedelta(days=1)
    elif st == "weekly":
        dow, hour, minute = parse_weekly(routine.schedule_value)
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        days_ahead = (dow - candidate.weekday()) % 7
        candidate += timedelta(days=days_ahead)
        if candidate <= now:
            candidate += timedelta(days=7)
        while candidate < start:
            candidate += timedelta(days=7)
    else:
        return None

    if end is not None and candidate > end:
        return None
    return candidate
