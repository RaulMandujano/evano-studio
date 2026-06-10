"""Tests for per-agent Discord bot connect/disconnect (bindings mixin).

All CLI calls are stubbed — the real `openclaw` and ~/.openclaw are never touched.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.openclaw_service import config, process


@pytest.fixture()
def client(tmp_path: Path, monkeypatch) -> Iterator[TestClient]:
    cfg_dir = tmp_path / ".openclaw"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(config, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", cfg_dir / "openclaw.json")
    settings = Settings(data_dir=tmp_path, environment="test", embedding_provider="hash")
    with TestClient(create_app(settings)) as c:
        yield c


def _stub_cli(monkeypatch, runner) -> list[list[str]]:
    calls: list[list[str]] = []

    def fake_run(args, *a, **k):
        calls.append(list(args))
        return runner(list(args))

    monkeypatch.setattr(process, "_which", lambda cmd: f"/usr/local/bin/{cmd}")
    monkeypatch.setattr(process, "_run", fake_run)
    monkeypatch.setattr(process, "_port_open", lambda *a, **k: False)  # gateway not running
    return calls


def test_discord_connect_runs_add_and_bind(client: TestClient, monkeypatch) -> None:
    calls = _stub_cli(monkeypatch, lambda args: (0, "{}", ""))
    r = client.post("/openclaw/agents/daniel/discord", json={"bot_token": "abc123"})
    body = r.json()
    assert r.status_code == 200 and body["ok"] is True

    add = next(c for c in calls if c[1:3] == ["channels", "add"])
    assert "--account" in add and add[add.index("--account") + 1] == "agent-daniel"
    assert "--bot-token" in add and add[add.index("--bot-token") + 1] == "abc123"
    bind = next(c for c in calls if c[1:3] == ["agents", "bind"])
    assert bind[bind.index("--bind") + 1] == "discord:agent-daniel"


def test_discord_connect_requires_token(client: TestClient, monkeypatch) -> None:
    _stub_cli(monkeypatch, lambda args: (0, "{}", ""))
    body = client.post("/openclaw/agents/daniel/discord", json={"bot_token": "  "}).json()
    assert body["ok"] is False
    assert "token" in body["message"].lower()


def test_discord_connect_invalid_agent_id(client: TestClient, monkeypatch) -> None:
    _stub_cli(monkeypatch, lambda args: (0, "{}", ""))
    body = client.post("/openclaw/agents/bad!id/discord", json={"bot_token": "abc"}).json()
    assert body["ok"] is False


def test_discord_status_reads_bindings(client: TestClient, monkeypatch) -> None:
    bindings = [{"agentId": "daniel", "channel": "discord", "accountId": "agent-daniel"}]

    def runner(args):
        if args[1:3] == ["agents", "bindings"]:
            return (0, json.dumps(bindings), "")
        return (0, "{}", "")

    _stub_cli(monkeypatch, runner)
    body = client.get("/openclaw/agents/daniel/discord").json()
    assert body["ok"] is True
    assert body["connected"] is True
    assert body["account_id"] == "agent-daniel"

    bindings.clear()
    body = client.get("/openclaw/agents/daniel/discord").json()
    assert body["connected"] is False


def test_discord_disconnect_unbinds_and_removes_account(client: TestClient, monkeypatch) -> None:
    calls = _stub_cli(monkeypatch, lambda args: (0, "{}", ""))
    body = client.delete("/openclaw/agents/daniel/discord").json()
    assert body["ok"] is True
    unbind = next(c for c in calls if c[1:3] == ["agents", "unbind"])
    assert unbind[unbind.index("--bind") + 1] == "discord:agent-daniel"
    remove = next(c for c in calls if c[1:3] == ["channels", "remove"])
    assert remove[remove.index("--account") + 1] == "agent-daniel"
    assert "--delete" in remove


def test_discord_graceful_without_openclaw(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(process, "_which", lambda cmd: None)
    assert client.get("/openclaw/agents/daniel/discord").json()["ok"] is False
    assert client.post("/openclaw/agents/daniel/discord", json={"bot_token": "x"}).json()["ok"] is False
    assert client.delete("/openclaw/agents/daniel/discord").json()["ok"] is False
