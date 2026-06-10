"""Tests: mirroring the KB into OpenClaw agent memory folders."""

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
    workspaces = {
        "main": cfg_dir / "workspace",
        "daniel": cfg_dir / "workspaces" / "daniel",
    }
    for ws in workspaces.values():
        ws.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "openclaw.json").write_text("{}", encoding="utf-8")

    agents = [{"id": aid, "workspace": str(ws)} for aid, ws in workspaces.items()]
    index_calls: list[str] = []

    def fake_run(args, *a, **k):
        if args[1:3] == ["agents", "list"]:
            return (0, json.dumps(agents), "")
        if args[1:3] == ["memory", "index"]:
            index_calls.append(args[args.index("--agent") + 1])
        return (0, "{}", "")

    monkeypatch.setattr(config, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", cfg_dir / "openclaw.json")
    monkeypatch.setattr(process, "_which", lambda cmd: f"/usr/local/bin/{cmd}")
    monkeypatch.setattr(process, "_run", fake_run)

    settings = Settings(data_dir=tmp_path, environment="test", embedding_provider="hash")
    with TestClient(create_app(settings)) as client:
        yield {"client": client, "workspaces": workspaces, "index_calls": index_calls}


def _import(client: TestClient, title: str, content: str) -> int:
    r = client.post("/knowledge/documents/import", json={
        "title": title, "file_name": f"{title.lower().replace(' ', '-')}.txt", "content": content,
    })
    assert r.status_code in (200, 201)
    return r.json()["id"]


def test_sync_writes_memory_files_to_all_agents(env) -> None:
    client = env["client"]
    doc_id = _import(client, "Precios", "El plan premium cuesta 49 dolares al mes.")

    body = client.post("/knowledge/sync-agents").json()
    assert body["ok"] is True
    assert body["agents_synced"] == 2
    assert body["files_written"] == 2

    for ws in env["workspaces"].values():
        files = list((ws / "memory").glob("evano-kb-*.md"))
        assert len(files) == 1
        text = files[0].read_text(encoding="utf-8")
        assert f"evano-kb-{doc_id}-" in files[0].name
        assert "# Precios" in text
        assert "49 dolares" in text
        assert "Synced from the Evano Studio Knowledge Base" in text

    assert sorted(env["index_calls"]) == ["daniel", "main"]


def test_sync_removes_stale_files_and_is_idempotent(env) -> None:
    client = env["client"]
    doc_id = _import(client, "Horario", "Abrimos de 9 a 6.")
    client.post("/knowledge/sync-agents")

    # Second sync with no changes writes nothing new.
    body = client.post("/knowledge/sync-agents").json()
    assert body["files_written"] == 0

    # Deleting the doc + resync removes the mirrored files.
    client.delete(f"/knowledge/documents/{doc_id}")
    body = client.post("/knowledge/sync-agents").json()
    assert body["ok"] is True
    for ws in env["workspaces"].values():
        assert list((ws / "memory").glob("evano-kb-*.md")) == []


def test_sync_does_not_touch_user_memory_files(env) -> None:
    client = env["client"]
    ws = env["workspaces"]["daniel"]
    (ws / "memory").mkdir(parents=True, exist_ok=True)
    own = ws / "memory" / "2026-06-10.md"
    own.write_text("nota personal del agente", encoding="utf-8")

    _import(client, "Datos", "info importante")
    client.post("/knowledge/sync-agents")
    client.post("/knowledge/sync-agents")

    assert own.read_text(encoding="utf-8") == "nota personal del agente"
