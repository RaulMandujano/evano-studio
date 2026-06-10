"""Tests for agent work-file documents (Documents tab, OpenClaw side)."""

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
    ws = cfg_dir / "workspaces" / "daniel"
    (ws / "memory").mkdir(parents=True, exist_ok=True)
    (ws / "reports").mkdir(parents=True, exist_ok=True)
    # Config + managed files (must NOT appear as documents).
    (ws / "AGENTS.md").write_text("instructions", encoding="utf-8")
    (ws / "SOUL.md").write_text("persona", encoding="utf-8")
    (ws / "memory" / "evano-kb-1-doc.md").write_text("kb mirror", encoding="utf-8")
    # Real work files.
    (ws / "report.md").write_text("# Informe\nVentas subieron 10%.", encoding="utf-8")
    (ws / "reports" / "q2.csv").write_text("mes,total\nabril,100", encoding="utf-8")
    (cfg_dir / "openclaw.json").write_text(json.dumps({
        "agents": {"list": [{"id": "daniel", "identity": {"name": "Daniel", "emoji": "💼"}}]},
    }), encoding="utf-8")

    agents = [{"id": "daniel", "workspace": str(ws)}]
    monkeypatch.setattr(config, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", cfg_dir / "openclaw.json")
    monkeypatch.setattr(process, "_which", lambda cmd: f"/usr/local/bin/{cmd}")
    monkeypatch.setattr(
        process, "_run",
        lambda args, *a, **k: (0, json.dumps(agents), "") if args[1:3] == ["agents", "list"] else (0, "{}", ""),
    )

    settings = Settings(data_dir=tmp_path, environment="test", embedding_provider="hash")
    with TestClient(create_app(settings)) as client:
        yield {"client": client, "ws": ws}


def test_lists_work_files_not_config(env) -> None:
    body = env["client"].get("/openclaw/documents").json()
    assert body["ok"] is True
    daniel = body["agents"][0]
    assert daniel["name"] == "Daniel" and daniel["emoji"] == "💼"
    names = {f["path"] for f in daniel["files"]}
    assert names == {"report.md", "reports/q2.csv"}


def test_preview_reads_text_content(env) -> None:
    body = env["client"].get("/openclaw/documents/content", params={"agent_id": "daniel", "path": "report.md"}).json()
    assert body["ok"] is True
    assert "Ventas subieron 10%" in body["content"]
    assert body["truncated"] is False


def test_preview_refuses_traversal_and_config(env) -> None:
    client = env["client"]
    for bad in ("../../../etc/passwd", "AGENTS.md", "memory/evano-kb-1-doc.md"):
        body = client.get("/openclaw/documents/content", params={"agent_id": "daniel", "path": bad}).json()
        assert body["ok"] is False, bad


def test_delete_work_file_only(env) -> None:
    client = env["client"]
    assert client.delete("/openclaw/documents/content", params={"agent_id": "daniel", "path": "AGENTS.md"}).json()["ok"] is False
    assert (env["ws"] / "AGENTS.md").exists()

    assert client.delete("/openclaw/documents/content", params={"agent_id": "daniel", "path": "report.md"}).json()["ok"] is True
    assert not (env["ws"] / "report.md").exists()
