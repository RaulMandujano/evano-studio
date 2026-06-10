"""Tests for the org chart — validation, persistence, and applying to OpenClaw.

The OpenClaw CLI and ~/.openclaw are fully stubbed/redirected to a temp dir.
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
def env(tmp_path: Path, monkeypatch) -> Iterator[dict]:
    """App client + fake OpenClaw install with three agents (boss, ana, leo)."""
    cfg_dir = tmp_path / ".openclaw"
    workspaces = {}
    agents = []
    for aid, emoji in (("boss", "👑"), ("ana", "📊"), ("leo", "🔎")):
        ws = cfg_dir / "workspaces" / aid
        ws.mkdir(parents=True, exist_ok=True)
        (ws / "AGENTS.md").write_text(f"# {aid}\n\nOriginal mission.\n", encoding="utf-8")
        workspaces[aid] = ws
        agents.append({"id": aid, "workspace": str(ws), "model": "ollama/gemma4:latest",
                       "isDefault": aid == "boss", "bindings": 0})

    cfg_file = cfg_dir / "openclaw.json"
    cfg_file.write_text(json.dumps({
        "agents": {
            "defaults": {"model": {"primary": "ollama/gemma4:latest"}},
            "list": [
                {"id": aid, "identity": {"name": aid.title(), "emoji": emoji}}
                for aid, emoji in (("boss", "👑"), ("ana", "📊"), ("leo", "🔎"))
            ],
        },
    }), encoding="utf-8")

    monkeypatch.setattr(config, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", cfg_file)
    monkeypatch.setattr(process, "_which", lambda cmd: f"/usr/local/bin/{cmd}")
    monkeypatch.setattr(process, "_port_open", lambda *a, **k: False)

    def fake_run(args, *a, **k):
        if args[1:3] == ["agents", "list"]:
            return (0, json.dumps(agents), "")
        return (0, "{}", "")

    monkeypatch.setattr(process, "_run", fake_run)

    settings = Settings(data_dir=tmp_path, environment="test", embedding_provider="hash")
    with TestClient(create_app(settings)) as client:
        yield {"client": client, "cfg_file": cfg_file, "workspaces": workspaces}


def test_chart_starts_empty(env) -> None:
    body = env["client"].get("/org/chart").json()
    assert body["ok"] is True
    assert {a["id"] for a in body["agents"]} == {"boss", "ana", "leo"}
    assert body["agents"][0]["name"] == "Boss"  # identity name from config
    assert body["links"] == []


def test_save_applies_permissions_and_notes(env) -> None:
    client, cfg_file = env["client"], env["cfg_file"]
    r = client.put("/org/chart", json={"links": [
        {"agent_id": "ana", "parent_agent_id": "boss"},
        {"agent_id": "leo", "parent_agent_id": "boss"},
    ]})
    assert r.status_code == 200 and r.json()["ok"] is True

    cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
    boss = next(e for e in cfg["agents"]["list"] if e["id"] == "boss")
    assert sorted(boss["subagents"]["allowAgents"]) == ["ana", "leo"]
    ana = next(e for e in cfg["agents"]["list"] if e["id"] == "ana")
    assert "subagents" not in ana

    boss_md = (env["workspaces"]["boss"] / "AGENTS.md").read_text(encoding="utf-8")
    assert "Original mission." in boss_md  # never clobbers existing content
    assert "Your team (Org Chart)" in boss_md
    assert 'agentId: "ana"' in boss_md
    ana_md = (env["workspaces"]["ana"] / "AGENTS.md").read_text(encoding="utf-8")
    assert "Your team" not in ana_md

    # The saved chart is returned on read.
    links = client.get("/org/chart").json()["links"]
    assert {(l["agent_id"], l["parent_agent_id"]) for l in links} == {("ana", "boss"), ("leo", "boss")}


def test_demoting_a_manager_cleans_up(env) -> None:
    client, cfg_file = env["client"], env["cfg_file"]
    client.put("/org/chart", json={"links": [{"agent_id": "ana", "parent_agent_id": "boss"}]})
    # New chart: ana now reports to leo; boss manages nobody.
    r = client.put("/org/chart", json={"links": [{"agent_id": "ana", "parent_agent_id": "leo"}]})
    assert r.json()["ok"] is True

    cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
    boss = next(e for e in cfg["agents"]["list"] if e["id"] == "boss")
    assert "subagents" not in boss
    leo = next(e for e in cfg["agents"]["list"] if e["id"] == "leo")
    assert leo["subagents"]["allowAgents"] == ["ana"]

    boss_md = (env["workspaces"]["boss"] / "AGENTS.md").read_text(encoding="utf-8")
    assert "Your team" not in boss_md
    assert "Original mission." in boss_md


def test_multilevel_sets_spawn_depth(env) -> None:
    client, cfg_file = env["client"], env["cfg_file"]
    r = client.put("/org/chart", json={"links": [
        {"agent_id": "ana", "parent_agent_id": "boss"},
        {"agent_id": "leo", "parent_agent_id": "ana"},
    ]})
    assert r.json()["ok"] is True
    cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
    assert cfg["agents"]["defaults"]["subagents"]["maxSpawnDepth"] == 2


@pytest.mark.parametrize(
    "links,fragment",
    [
        ([{"agent_id": "ana", "parent_agent_id": "ana"}], "itself"),
        ([{"agent_id": "ana", "parent_agent_id": "boss"},
          {"agent_id": "ana", "parent_agent_id": "leo"}], "two managers"),
        ([{"agent_id": "ana", "parent_agent_id": "leo"},
          {"agent_id": "leo", "parent_agent_id": "ana"}], "loop"),
        ([{"agent_id": "ghost", "parent_agent_id": "boss"}], "Unknown agent"),
    ],
)
def test_save_rejects_invalid_trees(env, links, fragment) -> None:
    r = env["client"].put("/org/chart", json={"links": links})
    assert r.status_code == 400
    assert fragment.lower() in r.json()["error"]["message"].lower()
