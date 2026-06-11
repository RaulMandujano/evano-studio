"""Tests for the Customer Service routing (support agent ↔ customer channel)."""

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
def env(tmp_path: Path, monkeypatch) -> Iterator[dict]:
    cfg_dir = tmp_path / ".openclaw"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "openclaw.json").write_text(json.dumps({
        "agents": {"list": [{"id": "sofia", "identity": {"name": "Sofía", "emoji": "🎧"}}]},
    }), encoding="utf-8")

    agents = [{"id": "sofia", "workspace": str(cfg_dir / "workspaces" / "sofia")}]
    channels = {"chat": {
        "whatsapp": {"installed": True, "accounts": [{"id": "default"}]},
        "telegram": {"installed": True, "accounts": []},
    }}
    bindings: list[dict] = []
    calls: list[list[str]] = []

    def fake_run(args, *a, **k):
        calls.append(list(args))
        if args[1:3] == ["agents", "list"]:
            return (0, json.dumps(agents), "")
        if args[1:3] == ["channels", "list"]:
            return (0, json.dumps(channels), "")
        if args[1:3] == ["agents", "bindings"]:
            return (0, json.dumps(bindings), "")
        if args[1:3] == ["agents", "bind"]:
            bindings.append({"agentId": args[args.index("--agent") + 1],
                             "channel": args[args.index("--bind") + 1]})
            return (0, "{}", "")
        if args[1:3] == ["agents", "unbind"]:
            bindings.clear()
            return (0, "{}", "")
        return (0, "{}", "")

    monkeypatch.setattr(config, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", cfg_dir / "openclaw.json")
    monkeypatch.setattr(process, "_which", lambda cmd: f"/usr/local/bin/{cmd}")
    monkeypatch.setattr(process, "_port_open", lambda *a, **k: False)
    monkeypatch.setattr(process, "_run", fake_run)

    settings = Settings(data_dir=tmp_path, environment="test", embedding_provider="hash")
    with TestClient(create_app(settings)) as client:
        yield {"client": client, "calls": calls}


def test_status_aggregates_everything(env) -> None:
    body = env["client"].get("/openclaw/support/status").json()
    assert body["ok"] is True
    assert body["agents"] == [{"id": "sofia", "name": "Sofía", "emoji": "🎧"}]
    by_slug = {c["slug"]: c for c in body["channels"]}
    assert set(by_slug) == {"whatsapp", "telegram", "discord", "slack", "signal"}
    assert by_slug["whatsapp"]["configured"] is True
    assert by_slug["whatsapp"]["connect"] == "login"  # QR pairing, not a token
    assert by_slug["telegram"]["configured"] is False
    assert by_slug["telegram"]["connect"] == "token"
    assert body["assignments"] == []


def test_assign_routes_channel_and_shows_in_status(env) -> None:
    client = env["client"]
    r = client.post("/openclaw/support/assign", json={"agent_id": "sofia", "channel": "whatsapp"}).json()
    assert r["ok"] is True

    bind = next(c for c in env["calls"] if c[1:3] == ["agents", "bind"])
    assert bind[bind.index("--agent") + 1] == "sofia"
    assert bind[bind.index("--bind") + 1] == "whatsapp"

    status = client.get("/openclaw/support/status").json()
    assert status["assignments"] == [{"agent_id": "sofia", "channel": "whatsapp", "account_id": ""}]

    r = client.post("/openclaw/support/unassign", json={"agent_id": "sofia", "channel": "whatsapp"}).json()
    assert r["ok"] is True
    assert client.get("/openclaw/support/status").json()["assignments"] == []


def test_assign_rejects_unknown_channel_and_bad_agent(env) -> None:
    client = env["client"]
    assert client.post("/openclaw/support/assign", json={"agent_id": "sofia", "channel": "myspace"}).json()["ok"] is False
    assert client.post("/openclaw/support/assign", json={"agent_id": "bad!id", "channel": "whatsapp"}).json()["ok"] is False
