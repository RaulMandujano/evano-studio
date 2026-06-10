"""Tests for the aggregated Chats listing and chat-origin detection."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.openclaw_service import config, process
from app.services.openclaw_service._agents import AgentsMixin


@pytest.mark.parametrize(
    "sid,key,expected",
    [
        ("evano-abc123", "", "evano"),
        ("evano-team-48d2-1-0", "", "team"),
        ("9f3a", "agent:main:discord:channel:42", "discord"),
        ("9f3a", "agent:main:telegram:dm:7", "telegram"),
        ("9f3a", "agent:main:subagent:uuid", "subagent"),
        ("9f3a", "agent:main:cron:job", "cron"),
        ("9f3a", "agent:main:main", "dashboard"),
        ("9f3a", "", "other"),
    ],
)
def test_session_origin(sid: str, key: str, expected: str) -> None:
    assert AgentsMixin._session_origin(sid, key) == expected


def _write_session(sdir: Path, sid: str, text: str) -> None:
    sdir.mkdir(parents=True, exist_ok=True)
    line = json.dumps({
        "type": "message",
        "message": {"role": "user", "content": [{"type": "text", "text": text}]},
    })
    (sdir / f"{sid}.jsonl").write_text(line + "\n", encoding="utf-8")


@pytest.fixture()
def client(tmp_path: Path, monkeypatch) -> Iterator[TestClient]:
    cfg_dir = tmp_path / ".openclaw"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "openclaw.json").write_text(json.dumps({
        "agents": {"list": [
            {"id": "main"},
            {"id": "daniel", "identity": {"name": "Daniel", "emoji": "💼"}},
        ]},
    }), encoding="utf-8")

    # daniel: an Evano chat + a Discord chat (indexed key); main: none.
    daniel_sessions = cfg_dir / "agents" / "daniel" / "sessions"
    _write_session(daniel_sessions, "evano-x1", "hola desde evano")
    _write_session(daniel_sessions, "abc-discord-uuid", "hola desde discord")
    (daniel_sessions / "sessions.json").write_text(json.dumps({
        "agent:daniel:discord:channel:99": {"sessionId": "abc-discord-uuid"},
    }), encoding="utf-8")

    agents = [
        {"id": "main", "workspace": str(cfg_dir / "workspace"), "isDefault": True},
        {"id": "daniel", "workspace": str(cfg_dir / "workspaces" / "daniel")},
    ]

    monkeypatch.setattr(config, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", cfg_dir / "openclaw.json")
    monkeypatch.setattr(process, "_which", lambda cmd: f"/usr/local/bin/{cmd}")
    monkeypatch.setattr(
        process, "_run",
        lambda args, *a, **k: (0, json.dumps(agents), "") if args[1:3] == ["agents", "list"] else (0, "{}", ""),
    )

    settings = Settings(data_dir=tmp_path, environment="test", embedding_provider="hash")
    with TestClient(create_app(settings)) as c:
        yield c


def test_all_chats_grouped_with_origins(client: TestClient) -> None:
    body = client.get("/openclaw/chats").json()
    assert body["ok"] is True
    by_id = {g["agent_id"]: g for g in body["agents"]}
    assert set(by_id) == {"main", "daniel"}

    daniel = by_id["daniel"]
    assert daniel["name"] == "Daniel" and daniel["emoji"] == "💼"
    origins = {s["session_id"]: s["origin"] for s in daniel["sessions"]}
    assert origins == {"evano-x1": "evano", "abc-discord-uuid": "discord"}
    assert all(s["preview"] for s in daniel["sessions"])

    assert by_id["main"]["sessions"] == []
    # Agents with recent chats sort first.
    assert body["agents"][0]["agent_id"] == "daniel"
