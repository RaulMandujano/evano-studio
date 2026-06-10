"""Tests for the agentic tool-calling loop (native Ollama function calling).

The test environment has no live model, so we monkeypatch ``chat_agentic`` to
script the model's tool calls. Tools execute for real against a temp workspace.
"""

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
        data_dir=tmp_path,
        environment="test",
        embedding_provider="hash",
        ollama_base_url="http://127.0.0.1:9",
        ollama_timeout_seconds=0.5,
    )
    with TestClient(create_app(settings)) as c:
        yield c


def _tool_call(name: str, args: dict) -> dict:
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [{"function": {"name": name, "arguments": args}}],
    }


def test_agentic_loop_executes_tools_and_summarizes(client, tmp_path, monkeypatch):
    ws = tmp_path / "ws"
    client.post("/workspace/configure", json={"path": str(ws)})
    agent = client.post(
        "/agents",
        json={"name": "A", "model_name": "x", "enabled_tools": ["create_folder", "create_text_file"]},
    ).json()

    # Script the model: step 1 → make a folder, step 2 → make a file, step 3 → final answer.
    steps = [
        AgenticTurn(ok=True, tool_calls=[{"name": "create_folder", "arguments": {"folder_name": "Clients"}}],
                    raw_message=_tool_call("create_folder", {"folder_name": "Clients"})),
        AgenticTurn(ok=True, tool_calls=[{"name": "create_text_file", "arguments": {"file_name": "hola.txt", "content": "Hola Evano"}}],
                    raw_message=_tool_call("create_text_file", {"file_name": "hola.txt", "content": "Hola Evano"})),
        AgenticTurn(ok=True, content="Listo: creé la carpeta Clients y el archivo hola.txt.", tool_calls=[]),
    ]
    seq = iter(steps)
    monkeypatch.setattr(OllamaService, "chat_agentic", lambda *a, **k: next(seq))

    r = client.post(f"/agents/{agent['id']}/chat", json={"message": "haz lo necesario"}).json()
    assert r["ok"] is True
    assert "Clients" in r["reply"]
    assert (ws / "Clients").is_dir()
    assert (ws / "hola.txt").read_text(encoding="utf-8") == "Hola Evano"
    # Both tool runs are reported.
    ids = [e["tool_id"] for e in r["tool_executions"]]
    assert ids == ["create_folder", "create_text_file"]


def test_agentic_loop_feeds_back_errors(client, tmp_path, monkeypatch):
    ws = tmp_path / "ws"
    client.post("/workspace/configure", json={"path": str(ws)})
    (ws / "dup").mkdir(parents=True, exist_ok=True)
    agent = client.post(
        "/agents", json={"name": "A", "model_name": "x", "enabled_tools": ["create_folder"]}
    ).json()

    # Model tries a folder that already exists, gets the error, then recovers.
    steps = [
        AgenticTurn(ok=True, tool_calls=[{"name": "create_folder", "arguments": {"folder_name": "dup"}}],
                    raw_message=_tool_call("create_folder", {"folder_name": "dup"})),
        AgenticTurn(ok=True, content="Esa carpeta ya existía.", tool_calls=[]),
    ]
    seq = iter(steps)
    monkeypatch.setattr(OllamaService, "chat_agentic", lambda *a, **k: next(seq))

    r = client.post(f"/agents/{agent['id']}/chat", json={"message": "crea dup"}).json()
    # The only tool call failed → the turn must NOT report success (no fake "Done").
    assert r["ok"] is False
    assert r["tool_executions"][0]["ok"] is False
    assert "did not complete" in (r["reply"] or "")


def test_loop_falls_back_to_router_when_model_lacks_tools(client, tmp_path, monkeypatch):
    ws = tmp_path / "ws"
    client.post("/workspace/configure", json={"path": str(ws)})
    agent = client.post(
        "/agents", json={"name": "A", "model_name": "x", "enabled_tools": ["create_folder"]}
    ).json()

    # Simulate a model that can't do tool calling (e.g. gemma3:4b).
    monkeypatch.setattr(
        OllamaService, "chat_agentic",
        lambda *a, **k: AgenticTurn(ok=False, supports_tools=False, message="does not support tools"),
    )

    # The deterministic router handles a clear request without the model.
    r = client.post(
        f"/agents/{agent['id']}/chat", json={"message": "crea una carpeta llamada Clientes"}
    ).json()
    assert r["ok"] is True
    assert (ws / "Clientes").is_dir()
