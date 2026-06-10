"""Tests for the OpenClaw control endpoints (detect / status / config parsing).

Config-write and gateway actions shell out to the real `openclaw` CLI, so they
are exercised live (not here). These tests cover detection, the response shape,
and parsing OpenClaw's real config JSON — with the config path redirected to a
temp dir so the real ~/.openclaw is never touched.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services import openclaw_service
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


def test_status_shape(client: TestClient) -> None:
    s = client.get("/openclaw/status").json()
    for key in ("node", "npm", "ollama", "openclaw", "config", "gateway", "web_search", "ready"):
        assert key in s
    assert isinstance(s["gateway"]["running"], bool)
    assert isinstance(s["gateway"]["port"], int)
    assert isinstance(s["web_search"]["enabled"], bool)
    assert s["config"]["exists"] is False  # temp dir, no config written


def test_enable_web_search(client: TestClient, monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(args, *a, **k):
        calls.append(args)
        return (0, "", "")

    monkeypatch.setattr(process, "_which", lambda _c: "/fake/openclaw")
    monkeypatch.setattr(process, "_run", fake_run)
    r = client.post("/openclaw/web-search/enable").json()
    assert r["ok"] is True
    assert ["openclaw", "config", "set", "tools.web.search.provider", "duckduckgo"] in calls


def test_parses_real_openclaw_config(client: TestClient, tmp_path: Path) -> None:
    # The exact shape OpenClaw's onboarding writes.
    cfg = {
        "agents": {"defaults": {"model": {"primary": "ollama/gemma4:latest"}}},
        "gateway": {"mode": "local", "port": 19001},
    }
    (tmp_path / ".openclaw" / "openclaw.json").write_text(json.dumps(cfg), encoding="utf-8")
    s = client.get("/openclaw/status").json()
    assert s["config"]["exists"] is True
    assert s["config"]["provider"] == "ollama"
    assert s["config"]["model"] == "gemma4:latest"
    assert s["gateway"]["port"] == 19001


def test_install_status_idle(client: TestClient) -> None:
    s = client.get("/openclaw/install/status").json()
    assert s["state"] in ("idle", "running", "success", "error")


def test_dashboard_url_uses_config_token(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    cfg = {"gateway": {"port": 18789, "auth": {"token": "abc123"}}}
    (tmp_path / ".openclaw" / "openclaw.json").write_text(json.dumps(cfg), encoding="utf-8")
    monkeypatch.setattr(process, "_which", lambda _c: "/fake/openclaw")
    monkeypatch.setattr(process, "_run", lambda *a, **k: (0, "", ""))
    r = client.get("/openclaw/dashboard").json()
    assert r["ok"] is True
    assert r["url"] == "http://127.0.0.1:18789/#token=abc123"


_CHANNELS_JSON = json.dumps({
    "chat": {
        "discord": {"accounts": [], "installed": False, "origin": "installable"},
        "whatsapp": {"accounts": [{"id": "default"}], "installed": True, "origin": "bundled"},
    }
})


def test_channels_list_parsing(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(process, "_which", lambda _c: "/fake/openclaw")
    monkeypatch.setattr(process, "_run", lambda *a, **k: (0, _CHANNELS_JSON, ""))
    r = client.get("/openclaw/channels").json()
    assert r["ok"] is True
    by_slug = {c["slug"]: c for c in r["channels"]}
    assert by_slug["whatsapp"]["configured"] is True
    assert by_slug["whatsapp"]["connect"] == "login"  # QR/login channel
    assert by_slug["discord"]["configured"] is False
    assert by_slug["discord"]["connect"] == "token"
    # Popular channels (whatsapp) sort before non-popular configured ones.
    assert r["channels"][0]["slug"] == "whatsapp"


def test_add_channel_login_rejected_without_shelling(client: TestClient, monkeypatch) -> None:
    # WhatsApp needs an interactive login → we never call the CLI, just guide.
    monkeypatch.setattr(process, "_which", lambda _c: "/fake/openclaw")
    monkeypatch.setattr(process, "_run", lambda *a, **k: pytest.fail("should not shell out"))
    r = client.post("/openclaw/channels/add", json={"channel": "whatsapp", "token": "x"}).json()
    assert r["ok"] is False
    assert "login" in r["message"].lower()


def test_add_channel_token_ok(client: TestClient, monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(args, *a, **k):
        calls.append(args)
        return (0, "added", "")

    monkeypatch.setattr(process, "_which", lambda _c: "/fake/openclaw")
    monkeypatch.setattr(process, "_run", fake_run)
    r = client.post("/openclaw/channels/add", json={"channel": "discord", "token": "bot-token"}).json()
    assert r["ok"] is True
    assert ["openclaw", "channels", "add", "--channel", "discord", "--token", "bot-token"] in calls


_AGENTS_JSON = json.dumps([
    {"id": "main", "workspace": "/ws/main", "model": "ollama/gemma4:latest", "bindings": 0, "isDefault": True},
])


def test_list_agents_parsing(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(process, "_which", lambda _c: "/fake/openclaw")
    monkeypatch.setattr(process, "_run", lambda *a, **k: (0, _AGENTS_JSON, ""))
    r = client.get("/openclaw/agents").json()
    assert r["ok"] is True
    assert r["agents"][0]["id"] == "main"
    assert r["agents"][0]["is_default"] is True
    assert r["agents"][0]["model"] == "ollama/gemma4:latest"


def test_create_agent_builds_argv_and_writes_mission(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(args, *a, **k):
        calls.append(args)
        return (0, "{}", "")

    monkeypatch.setattr(process, "_which", lambda _c: "/fake/openclaw")
    monkeypatch.setattr(process, "_run", fake_run)
    r = client.post("/openclaw/agents", json={
        "name": "Sales Helper", "instructions": "Help close deals.", "emoji": "💼",
    }).json()
    assert r["ok"] is True
    assert r["agent"]["id"] == "sales-helper"  # slugified
    assert r["agent"]["model"] == "ollama/gemma4:latest"  # default free model
    add_call = next(c for c in calls if c[:3] == ["openclaw", "agents", "add"])
    assert "sales-helper" in add_call and "--non-interactive" in add_call
    assert "--model" in add_call and "ollama/gemma4:latest" in add_call
    # set-identity called with the friendly name + emoji
    assert any(c[:3] == ["openclaw", "agents", "set-identity"] for c in calls)
    # mission appended to the (scaffolded-or-created) AGENTS.md in the temp workspace
    agents_md = tmp_path / ".openclaw" / "workspaces" / "sales-helper" / "AGENTS.md"
    assert agents_md.exists() and "Help close deals." in agents_md.read_text(encoding="utf-8")


def test_delete_default_agent_blocked(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(process, "_which", lambda _c: "/fake/openclaw")
    monkeypatch.setattr(process, "_run", lambda *a, **k: pytest.fail("should not shell out"))
    r = client.delete("/openclaw/agents/main").json()
    assert r["ok"] is False
    assert "default" in r["message"].lower()


def test_agent_chat_parses_reply_and_keeps_session(client: TestClient, monkeypatch) -> None:
    turn = json.dumps({
        "payloads": [{"text": "Hello there!", "mediaUrl": None}],
        "meta": {"agentMeta": {"model": "gemma4:latest", "sessionId": "evano-abc"}},
    })
    calls: list[list[str]] = []

    def fake_run(args, *a, **k):
        calls.append(args)
        return (0, turn, "warn")

    monkeypatch.setattr(process, "_which", lambda _c: "/fake/openclaw")
    monkeypatch.setattr(process, "_run", fake_run)
    r = client.post("/openclaw/agents/main/chat", json={"message": "hi", "session_id": "evano-abc"}).json()
    assert r["ok"] is True
    assert r["reply"] == "Hello there!"
    assert r["model"] == "gemma4:latest"
    assert r["session_id"] == "evano-abc"
    # the stable session id was passed to OpenClaw for continuity
    chat_call = next(c for c in calls if c[:3] == ["openclaw", "agent", "--agent"])
    assert "--session-id" in chat_call and "evano-abc" in chat_call


def test_agent_files_read_and_save(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    ws = tmp_path / "agent-ws"
    ws.mkdir()
    (ws / "AGENTS.md").write_text("original instructions", encoding="utf-8")
    agents_list = json.dumps([{"id": "main", "workspace": str(ws), "model": "ollama/gemma4:latest"}])
    monkeypatch.setattr(process, "_which", lambda _c: "/fake/openclaw")
    monkeypatch.setattr(process, "_run", lambda *a, **k: (0, agents_list, ""))

    listing = client.get("/openclaw/agents/main/files").json()
    assert listing["ok"] is True
    by_name = {f["name"]: f for f in listing["files"]}
    assert by_name["AGENTS.md"]["label"] == "Instructions"
    assert by_name["AGENTS.md"]["content"] == "original instructions"

    saved = client.put("/openclaw/agents/main/files/AGENTS.md", json={"content": "new instructions"}).json()
    assert saved["ok"] is True
    assert (ws / "AGENTS.md").read_text(encoding="utf-8") == "new instructions"


def _write_session(cfg_dir: Path, agent: str, sid: str, turns: list[tuple[str, str]]) -> None:
    sdir = cfg_dir / "agents" / agent / "sessions"
    sdir.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps({"type": "session", "id": sid, "timestamp": "2026-06-08T00:00:00Z"})]
    for role, text in turns:
        lines.append(json.dumps({
            "type": "message",
            "message": {"role": role, "content": [{"type": "text", "text": text}]},
        }))
    (sdir / f"{sid}.jsonl").write_text("\n".join(lines), encoding="utf-8")


def test_sessions_list_get_delete(client: TestClient, tmp_path: Path) -> None:
    cfg = tmp_path / ".openclaw"
    sid = "evano-test-1234"
    _write_session(cfg, "main", sid, [("user", "Hello agent"), ("assistant", "Hi there!")])

    listing = client.get("/openclaw/agents/main/sessions").json()
    assert listing["ok"] is True
    assert len(listing["sessions"]) == 1
    s = listing["sessions"][0]
    assert s["session_id"] == sid
    assert s["preview"] == "Hello agent"
    assert s["message_count"] == 2
    assert listing["total_bytes"] > 0

    detail = client.get(f"/openclaw/agents/main/sessions/{sid}").json()
    assert detail["ok"] is True
    assert detail["messages"] == [
        {"role": "user", "content": "Hello agent"},
        {"role": "assistant", "content": "Hi there!"},
    ]

    deleted = client.delete(f"/openclaw/agents/main/sessions/{sid}").json()
    assert deleted["ok"] is True
    assert client.get("/openclaw/agents/main/sessions").json()["sessions"] == []


def test_sessions_clear_all(client: TestClient, tmp_path: Path) -> None:
    cfg = tmp_path / ".openclaw"
    _write_session(cfg, "main", "evano-a", [("user", "one")])
    _write_session(cfg, "main", "evano-b", [("user", "two")])
    r = client.post("/openclaw/agents/main/sessions/clear", json={}).json()
    assert r["ok"] is True
    assert r["deleted"] == 2
    assert client.get("/openclaw/agents/main/sessions").json()["sessions"] == []


def test_agent_file_save_rejects_non_md(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    ws = tmp_path / "agent-ws2"
    ws.mkdir()
    agents_list = json.dumps([{"id": "main", "workspace": str(ws)}])
    monkeypatch.setattr(process, "_which", lambda _c: "/fake/openclaw")
    monkeypatch.setattr(process, "_run", lambda *a, **k: (0, agents_list, ""))
    r = client.put("/openclaw/agents/main/files/secrets.txt", json={"content": "x"}).json()
    assert r["ok"] is False
    assert ".md" in r["message"].lower()
