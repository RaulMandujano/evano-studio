"""Tests for the human-in-the-loop approval flow for computer-control tools."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.ollama_service import AgenticTurn, OllamaService


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(
        data_dir=tmp_path, environment="test", embedding_provider="hash",
        ollama_base_url="http://127.0.0.1:9", ollama_timeout_seconds=0.5,
    )
    with TestClient(create_app(settings)) as c:
        yield c


def _wants(name: str, args: dict) -> dict:
    return {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": name, "arguments": args}}]}


def test_agent_proposes_command_and_user_approves(client, monkeypatch):
    agent = client.post(
        "/agents", json={"name": "Ops", "model_name": "x", "enabled_tools": ["run_command"]}
    ).json()

    # The model asks to run a command; the loop should STOP and request approval.
    monkeypatch.setattr(
        OllamaService, "chat_agentic",
        lambda *a, **k: AgenticTurn(ok=True, tool_calls=[{"name": "run_command", "arguments": {"command": "echo hola-evano"}}],
                                    raw_message=_wants("run_command", {"command": "echo hola-evano"})),
    )

    r = client.post(f"/agents/{agent['id']}/chat", json={"message": "muestra un saludo"}).json()
    assert r["pending_action"] is not None
    pa = r["pending_action"]
    assert pa["tool_id"] == "run_command"
    assert pa["preview"] == "echo hola-evano"
    assert pa["status"] == "pending"

    # Nothing ran yet — it's listed as pending.
    pending = client.get("/actions?status=pending").json()
    assert any(p["id"] == pa["id"] for p in pending)

    # Approve → the command actually runs now.
    res = client.post(f"/actions/{pa['id']}/approve").json()
    assert res["ok"] is True
    assert res["status"] == "done"
    assert "hola-evano" in (res["execution"]["result"]["stdout"] or "")

    # Re-approving is rejected.
    again = client.post(f"/actions/{pa['id']}/approve").json()
    assert again["ok"] is False
    assert again["status"] == "already_resolved"


def test_user_can_deny(client, monkeypatch):
    agent = client.post(
        "/agents", json={"name": "Ops", "model_name": "x", "enabled_tools": ["run_command"]}
    ).json()
    monkeypatch.setattr(
        OllamaService, "chat_agentic",
        lambda *a, **k: AgenticTurn(ok=True, tool_calls=[{"name": "run_command", "arguments": {"command": "rm -rf /tmp/whatever"}}],
                                    raw_message=_wants("run_command", {"command": "rm -rf /tmp/whatever"})),
    )
    r = client.post(f"/agents/{agent['id']}/chat", json={"message": "haz algo"}).json()
    pa = r["pending_action"]
    denied = client.post(f"/actions/{pa['id']}/deny").json()
    assert denied["ok"] is True
    assert denied["status"] == "denied"


def test_sudo_is_blocked_even_when_approved(client):
    # Manual run (Tools page path) of a sudo command must be refused.
    r = client.post(
        "/tools/test", json={"tool_id": "run_command", "params": {"command": "sudo rm -rf /"}}
    ).json()
    assert r["ok"] is False
    assert "sudo" in (r["message"] or "").lower()
