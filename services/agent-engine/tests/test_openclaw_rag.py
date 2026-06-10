"""Tests: the local knowledge base feeds OpenClaw agent chats (RAG injection)."""

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
    (cfg_dir / "openclaw.json").write_text(json.dumps({"agents": {"list": [{"id": "daniel"}]}}), encoding="utf-8")

    monkeypatch.setattr(config, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", cfg_dir / "openclaw.json")
    monkeypatch.setattr(process, "_which", lambda cmd: f"/usr/local/bin/{cmd}")
    monkeypatch.setattr(process, "_port_open", lambda *a, **k: False)

    captured: dict = {}

    def fake_run(args, *a, **k):
        if args[1] == "agent":
            captured["args"] = list(args)
            return (0, json.dumps({"payloads": [{"text": "hola"}], "meta": {}}), "")
        return (0, "[]", "")

    monkeypatch.setattr(process, "_run", fake_run)

    # Hash embeddings: deterministic, no model download, no network.
    settings = Settings(data_dir=tmp_path, environment="test", embedding_provider="hash")
    with TestClient(create_app(settings)) as client:
        yield {"client": client, "captured": captured}


def _sent_message(captured: dict) -> str:
    args = captured["args"]
    return args[args.index("--message") + 1]


def test_chat_without_kb_is_untouched(env) -> None:
    r = env["client"].post("/openclaw/agents/daniel/chat", json={"message": "hola, ¿cómo estás?"})
    assert r.status_code == 200
    assert _sent_message(env["captured"]) == "hola, ¿cómo estás?"


def test_chat_gets_kb_context_when_relevant(env) -> None:
    client = env["client"]
    imported = client.post("/knowledge/documents/import", json={
        "title": "Manual interno",
        "file_name": "manual.txt",
        "content": "La clave del almacén es CASTOR-99 y el horario es de 9 a 6.",
    })
    assert imported.status_code in (200, 201)

    r = client.post("/openclaw/agents/daniel/chat", json={"message": "¿cuál es la clave del almacén?"})
    assert r.status_code == 200 and r.json()["ok"] is True

    sent = _sent_message(env["captured"])
    assert "knowledge base" in sent
    assert "CASTOR-99" in sent
    assert sent.endswith("¿cuál es la clave del almacén?")
