"""Tests for saved agent teams (multi-agent workflows) CRUD."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(data_dir=tmp_path, environment="test", embedding_provider="hash")
    with TestClient(create_app(settings)) as c:
        yield c


def test_team_crud(client: TestClient) -> None:
    created = client.post(
        "/teams",
        json={
            "name": "Weekly report",
            "steps": [
                {"agent_id": "researcher", "instruction": "Gather the numbers."},
                {"agent_id": "writer", "instruction": "Write the summary."},
            ],
        },
    ).json()
    assert created["name"] == "Weekly report"
    assert len(created["steps"]) == 2
    assert created["steps"][0]["agent_id"] == "researcher"
    assert created["steps"][0]["instruction"] == "Gather the numbers."

    assert len(client.get("/teams").json()) == 1

    updated = client.put(
        f"/teams/{created['id']}",
        json={"steps": [{"agent_id": "solo", "instruction": "Do it all."}]},
    ).json()
    assert len(updated["steps"]) == 1
    assert updated["steps"][0]["agent_id"] == "solo"
    assert updated["name"] == "Weekly report"  # unchanged

    assert client.delete(f"/teams/{created['id']}").json() == {"ok": True}
    assert client.get(f"/teams/{created['id']}").status_code == 404


def test_team_requires_name(client: TestClient) -> None:
    r = client.post("/teams", json={"steps": []})
    assert r.status_code == 422


def test_team_working_file_roundtrips(client: TestClient) -> None:
    created = client.post(
        "/teams",
        json={"name": "Doc flow", "steps": [{"agent_id": "a", "instruction": "x"}], "working_file": "report.md"},
    ).json()
    assert created["working_file"] == "report.md"
    assert client.get(f"/teams/{created['id']}").json()["working_file"] == "report.md"


def test_file_handoff_copies_between_workspaces(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    from app.services.openclaw_service import _agents

    src = tmp_path / "ws-a"
    dst = tmp_path / "ws-b"
    src.mkdir()
    dst.mkdir()
    (src / "report.md").write_text("hello from A", encoding="utf-8")

    monkeypatch.setattr(
        _agents.AgentsMixin, "_agent_workspace",
        lambda self, aid: {"a": src, "b": dst}.get(aid),
    )
    r = client.post(
        "/openclaw/file-handoff",
        json={"from_agent_id": "a", "to_agent_id": "b", "file_name": "report.md"},
    ).json()
    assert r["ok"] is True
    assert (dst / "report.md").read_text(encoding="utf-8") == "hello from A"

    # Missing file → clean error, no crash.
    bad = client.post(
        "/openclaw/file-handoff",
        json={"from_agent_id": "a", "to_agent_id": "b", "file_name": "missing.md"},
    ).json()
    assert bad["ok"] is False
