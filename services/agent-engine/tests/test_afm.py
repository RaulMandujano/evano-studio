"""Tests for AFM — Agent File Management (workspace relocation + team archiving)."""

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
    initial = {
        "main": cfg_dir / "workspace",
        "daniel": cfg_dir / "workspaces" / "daniel",
    }
    for aid, ws in initial.items():
        ws.mkdir(parents=True, exist_ok=True)
        (ws / "AGENTS.md").write_text(f"{aid} instructions", encoding="utf-8")
        (ws / "notes.md").write_text(f"{aid} work", encoding="utf-8")

    cfg_file = cfg_dir / "openclaw.json"
    cfg_file.write_text(json.dumps({
        "agents": {"list": [
            {"id": "main"},
            {"id": "daniel", "workspace": str(initial["daniel"]),
             "identity": {"name": "Daniel", "emoji": "💼"}},
        ]},
    }), encoding="utf-8")

    captured: dict = {}

    def fake_run(args, *a, **k):
        if args[1:3] == ["agents", "list"]:
            # Mirror the real CLI: workspaces come from the live config file.
            cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
            rows = []
            for entry in cfg["agents"]["list"]:
                aid = entry["id"]
                ws = entry.get("workspace") or str(initial[aid])
                rows.append({"id": aid, "workspace": ws, "isDefault": aid == "main"})
            return (0, json.dumps(rows), "")
        if args[1:3] == ["agents", "add"]:
            captured["add_args"] = list(args)
            return (0, "{}", "")
        return (0, "{}", "")

    monkeypatch.setattr(config, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", cfg_file)
    monkeypatch.setattr(process, "_which", lambda cmd: f"/usr/local/bin/{cmd}")
    monkeypatch.setattr(process, "_port_open", lambda *a, **k: False)
    monkeypatch.setattr(process, "_run", fake_run)

    settings = Settings(data_dir=tmp_path, environment="test", embedding_provider="hash")
    with TestClient(create_app(settings)) as client:
        yield {
            "client": client,
            "cfg_file": cfg_file,
            "initial": initial,
            "default_root": settings.workspace_path,
            "captured": captured,
        }


def test_apply_default_moves_workspaces_and_updates_config(env) -> None:
    client = env["client"]
    r = client.post("/afm/apply", json={}).json()
    assert r["ok"] is True
    assert sorted(r["moved"]) == ["Daniel", "main"]

    root = env["default_root"]
    daniel_dir = root / "Agents" / "Daniel"
    assert (daniel_dir / "notes.md").read_text(encoding="utf-8") == "daniel work"
    assert not env["initial"]["daniel"].exists()  # moved, not copied

    cfg = json.loads(env["cfg_file"].read_text(encoding="utf-8"))
    daniel = next(e for e in cfg["agents"]["list"] if e["id"] == "daniel")
    assert daniel["workspace"] == str(daniel_dir)
    main = next(e for e in cfg["agents"]["list"] if e["id"] == "main")
    assert main["workspace"] == str(root / "Agents" / "main")

    status = client.get("/afm/status").json()
    assert status["configured"] is True and status["is_default"] is True
    assert all(a["managed"] for a in status["agents"])

    # Re-apply is a no-op (idempotent).
    again = client.post("/afm/apply", json={}).json()
    assert again["ok"] is True and again["moved"] == []


def test_apply_scaffolds_team_folders(env) -> None:
    client = env["client"]
    client.post("/teams", json={"name": "Equipo Clima", "steps": [
        {"agent_id": "daniel", "instruction": "investiga"},
        {"agent_id": "main", "instruction": "resume"},
    ]})
    r = client.post("/afm/apply", json={}).json()
    assert r["ok"] is True
    team_dir = env["default_root"] / "Teams" / "Equipo Clima"
    assert (team_dir / "Daniel").is_dir()
    assert (team_dir / "main").is_dir()


def test_archive_team_run_files_outputs(env) -> None:
    client = env["client"]
    client.post("/afm/apply", json={})
    r = client.post("/afm/archive-team-run", json={
        "team_name": "Equipo Clima",
        "steps": [
            {"agent_id": "daniel", "output": "datos del clima"},
            {"agent_id": "main", "output": "reporte final bonito"},
        ],
        "final": "reporte final bonito",
    }).json()
    assert r["ok"] is True
    team_dir = env["default_root"] / "Teams" / "Equipo Clima"
    daniel_runs = list((team_dir / "Daniel").glob("run-*-step1.md"))
    assert len(daniel_runs) == 1
    assert "datos del clima" in daniel_runs[0].read_text(encoding="utf-8")
    finals = list(team_dir.glob("final-*.md"))
    assert len(finals) == 1


def test_new_agents_created_inside_afm_root(env) -> None:
    client = env["client"]
    client.post("/afm/apply", json={})
    client.post("/openclaw/agents", json={"name": "Sofia"})
    add_args = env["captured"]["add_args"]
    ws = add_args[add_args.index("--workspace") + 1]
    assert ws == str(env["default_root"] / "Agents" / "Sofia")


def test_apply_custom_root(env, tmp_path) -> None:
    client = env["client"]
    custom = tmp_path / "MisAgentes"
    r = client.post("/afm/apply", json={"root": str(custom)}).json()
    assert r["ok"] is True
    assert (custom / "Agents" / "Daniel" / "notes.md").exists()
    status = client.get("/afm/status").json()
    assert status["is_default"] is False
    assert status["root"] == str(custom)
