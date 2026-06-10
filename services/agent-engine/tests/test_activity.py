"""Tests for the live agent activity tracker (Office view)."""

from __future__ import annotations

import pytest

from app.services.activity_service import ActivityTracker, get_activity_tracker, track


def test_tracker_begin_and_end() -> None:
    tracker = ActivityTracker()
    activity_id = tracker.begin(
        agent_id="openclaw:writer", agent_name="writer", kind="chat", task="Answering a chat"
    )

    snap = tracker.snapshot()
    assert len(snap["active"]) == 1
    assert snap["active"][0]["agent_id"] == "openclaw:writer"
    assert snap["active"][0]["status"] == "working"
    assert snap["recent"] == []

    tracker.end(activity_id, ok=False, note="Ollama offline.")
    snap = tracker.snapshot()
    assert snap["active"] == []
    assert len(snap["recent"]) == 1
    assert snap["recent"][0]["status"] == "error"
    assert snap["recent"][0]["note"] == "Ollama offline."
    assert snap["recent"][0]["finished_at"] is not None


def test_tracker_end_unknown_id_is_noop() -> None:
    tracker = ActivityTracker()
    tracker.end(999)
    snap = tracker.snapshot()
    assert snap["active"] == []
    assert snap["recent"] == []


def test_track_context_manager_success_and_failure() -> None:
    tracker = get_activity_tracker()

    with track(agent_id="builtin:1", agent_name="Helper", kind="routine", task="Routine \"Daily\"") as outcome:
        outcome["ok"] = True
    snap = tracker.snapshot()
    assert snap["recent"][0]["agent_id"] == "builtin:1"
    assert snap["recent"][0]["status"] == "done"

    with pytest.raises(RuntimeError):
        with track(agent_id="builtin:2", agent_name="Crashy", kind="chat", task="Answering"):
            raise RuntimeError("boom")
    snap = tracker.snapshot()
    assert snap["recent"][0]["agent_id"] == "builtin:2"
    assert snap["recent"][0]["status"] == "error"


def test_activity_endpoint_shape(client) -> None:
    response = client.get("/activity")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["active"], list)
    assert isinstance(body["recent"], list)
    assert body["generated_at"]
