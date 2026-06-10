"""Tests for routines: scheduling math + CRUD + run-now."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.models import Routine
from app.main import create_app
from app.services.scheduling import compute_next_run


# ---- pure scheduling tests (no app) ---------------------------------------

def _routine(**kw) -> Routine:
    defaults = dict(
        name="R",
        agent_id=1,
        prompt="p",
        schedule_type="daily",
        schedule_value="09:00",
        is_enabled=True,
    )
    defaults.update(kw)
    return Routine(**defaults)


def test_compute_daily_next_run() -> None:
    now = datetime(2026, 6, 6, 8, 0)  # 08:00, before 09:00
    nxt = compute_next_run(_routine(schedule_type="daily", schedule_value="09:00"), now)
    assert nxt == datetime(2026, 6, 6, 9, 0)

    now = datetime(2026, 6, 6, 10, 0)  # after 09:00 → tomorrow
    nxt = compute_next_run(_routine(schedule_type="daily", schedule_value="09:00"), now)
    assert nxt == datetime(2026, 6, 7, 9, 0)


def test_compute_weekly_next_run() -> None:
    # 2026-06-06 is a Saturday. Next Monday 09:00 = 2026-06-08.
    now = datetime(2026, 6, 6, 10, 0)
    nxt = compute_next_run(_routine(schedule_type="weekly", schedule_value="mon 09:00"), now)
    assert nxt == datetime(2026, 6, 8, 9, 0)


def test_compute_once_and_manual() -> None:
    start = datetime(2026, 7, 1, 12, 0)
    once = _routine(schedule_type="once", schedule_value="", start_at=start, last_run_at=None)
    assert compute_next_run(once, datetime(2026, 6, 6, 0, 0)) == start
    # After it ran, no reschedule.
    once.last_run_at = datetime(2026, 7, 1, 12, 0)
    assert compute_next_run(once, datetime(2026, 7, 1, 13, 0)) is None
    # Manual never schedules.
    assert compute_next_run(_routine(schedule_type="manual"), datetime.now()) is None


def test_disabled_has_no_next_run() -> None:
    assert compute_next_run(_routine(is_enabled=False), datetime.now()) is None


# ---- API tests (scheduler disabled; Ollama offline for determinism) --------

@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(
        data_dir=tmp_path,
        environment="test",
        routine_scheduler_enabled=False,
        ollama_base_url="http://127.0.0.1:9",
        ollama_timeout_seconds=0.5,
        ollama_chat_timeout_seconds=0.5,
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def _agent(client: TestClient) -> int:
    return client.post("/agents", json={"name": "Worker", "model_name": "x"}).json()["id"]


def test_create_routine_sets_next_run(client: TestClient) -> None:
    agent_id = _agent(client)
    response = client.post(
        "/routines",
        json={
            "name": "Daily summary",
            "agent_id": agent_id,
            "prompt": "Summarize the day.",
            "schedule_type": "daily",
            "schedule_value": "09:00",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "scheduled"
    assert body["next_run_at"] is not None


def test_invalid_schedule_rejected(client: TestClient) -> None:
    agent_id = _agent(client)
    response = client.post(
        "/routines",
        json={
            "name": "Bad",
            "agent_id": agent_id,
            "prompt": "x",
            "schedule_type": "daily",
            "schedule_value": "not-a-time",
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_schedule"


def test_create_requires_existing_agent(client: TestClient) -> None:
    response = client.post(
        "/routines",
        json={"name": "X", "agent_id": 999, "prompt": "x", "schedule_type": "manual"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_agent"


def test_crud_and_list(client: TestClient) -> None:
    agent_id = _agent(client)
    created = client.post(
        "/routines",
        json={"name": "Manual one", "agent_id": agent_id, "prompt": "do it", "schedule_type": "manual"},
    ).json()
    assert created["status"] == "manual"
    assert created["next_run_at"] is None

    assert len(client.get("/routines").json()) == 1
    detail = client.get(f"/routines/{created['id']}").json()
    assert detail["recent_runs"] == []

    updated = client.put(f"/routines/{created['id']}", json={"name": "Renamed"}).json()
    assert updated["name"] == "Renamed"

    assert client.delete(f"/routines/{created['id']}").json() == {"ok": True}
    assert client.get(f"/routines/{created['id']}").status_code == 404


def test_run_now_logs_a_run(client: TestClient) -> None:
    agent_id = _agent(client)
    routine = client.post(
        "/routines",
        json={"name": "Now", "agent_id": agent_id, "prompt": "hello", "schedule_type": "manual"},
    ).json()

    run = client.post(f"/routines/{routine['id']}/run-now").json()
    assert run["trigger"] == "manual"
    # Ollama is offline in tests → the run is logged with an error, not hidden.
    assert run["status"] == "error"
    assert run["error"]

    # The run is visible in the routine detail.
    detail = client.get(f"/routines/{routine['id']}").json()
    assert len(detail["recent_runs"]) == 1
    assert detail["last_run_at"] is not None


def test_openclaw_routine_runs_via_openclaw_agent(client: TestClient, monkeypatch) -> None:
    # A routine that targets an OpenClaw agent runs it (no built-in agent needed).
    from app.services import openclaw_service

    monkeypatch.setattr(
        openclaw_service.OpenClawService,
        "agent_chat",
        lambda self, *, agent_id, message, session_id=None: {
            "ok": True, "reply": f"done:{message}", "model": "gemma4:latest",
            "session_id": "", "message": "",
        },
    )
    created = client.post(
        "/routines",
        json={
            "name": "Daily report",
            "openclaw_agent_id": "office-assistant",
            "prompt": "Summarize sales",
            "schedule_type": "manual",
        },
    ).json()
    assert created["openclaw_agent_id"] == "office-assistant"
    assert created["agent_id"] == 0  # no built-in agent

    run = client.post(f"/routines/{created['id']}/run-now").json()
    assert run["status"] == "success"
    assert run["output"] == "done:Summarize sales"


def test_team_routine_runs_whole_team(client: TestClient, monkeypatch) -> None:
    # A routine that targets a Team runs the whole workflow autonomously.
    from app.services import team_runner

    monkeypatch.setattr(
        team_runner,
        "run_team",
        lambda *, name, steps, starting_input="", working_file=None: {"ok": True, "final": f"done:{name}", "error": None, "steps": []},
    )
    team = client.post(
        "/teams", json={"name": "Flow", "steps": [{"agent_id": "a", "instruction": "x"}]}
    ).json()
    routine = client.post(
        "/routines",
        json={"name": "Auto flow", "team_id": team["id"], "prompt": "go", "schedule_type": "manual"},
    ).json()
    assert routine["team_id"] == team["id"]
    assert routine["agent_id"] == 0

    run = client.post(f"/routines/{routine['id']}/run-now").json()
    assert run["status"] == "success"
    assert run["output"] == "done:Flow"


def test_calendar_events(client: TestClient) -> None:
    agent_id = _agent(client)
    routine = client.post(
        "/routines",
        json={
            "name": "Daily",
            "agent_id": agent_id,
            "prompt": "x",
            "schedule_type": "daily",
            "schedule_value": "09:00",
        },
    ).json()
    client.post(f"/routines/{routine['id']}/run-now")

    events = client.get("/calendar/events").json()["events"]
    types = {e["type"] for e in events}
    assert "scheduled" in types  # upcoming next run
    assert "error" in types  # the manual run (offline)
