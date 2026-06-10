"""Tests for deterministic tool-intent detection and agent tool calling."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.tools.intent import detect_tool_intent


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(
        data_dir=tmp_path,
        environment="test",
        embedding_provider="hash",
        ollama_base_url="http://127.0.0.1:9",  # offline → proves no model call for tools
        ollama_timeout_seconds=0.5,
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_detect_create_folder() -> None:
    intent = detect_tool_intent("Create a folder called Clients")
    assert intent is not None
    assert intent.tool_id == "create_folder"
    assert intent.params["folder_name"] == "Clients"


def test_detect_create_folder_with_parent() -> None:
    intent = detect_tool_intent("make a folder named Q1 in Projects")
    assert intent.tool_id == "create_folder"
    assert intent.params == {"folder_name": "Q1", "parent": "Projects"}


def test_detect_list_files() -> None:
    assert detect_tool_intent("list my files").tool_id == "list_files"
    assert detect_tool_intent("show the files in Projects").params["path"] == "Projects"


def test_detect_search_and_read() -> None:
    assert detect_tool_intent("search the workspace for invoice").tool_id == "search_workspace"
    assert detect_tool_intent("read the file notes.txt").tool_id == "read_text_file"


def test_no_false_positive_on_chat() -> None:
    assert detect_tool_intent("What's the weather like today?") is None
    assert detect_tool_intent("Tell me a story about a folder") is None
    assert detect_tool_intent("create a plan for the launch") is None  # 'plan' isn't a tool object
    assert detect_tool_intent("") is None


# ---- Spanish + document detection ----------------------------------------- #


def test_detect_spanish_folder() -> None:
    intent = detect_tool_intent("crea una carpeta llamada Clientes")
    assert intent.tool_id == "create_folder"
    assert intent.params["folder_name"] == "Clientes"


def test_detect_subjunctive_phrasing() -> None:
    # "quiero que crees..." / "necesito que me crees..." (very common Spanish).
    i1 = detect_tool_intent("quiero que crees un folder llamado HOLA AMIGO")
    assert i1.tool_id == "create_folder"
    assert i1.params["folder_name"] == "HOLA AMIGO"
    i2 = detect_tool_intent("necesito que me crees una carpeta llamada Clientes")
    assert i2.tool_id == "create_folder"
    assert i2.params["folder_name"] == "Clientes"
    # Not a tool request.
    assert detect_tool_intent("quiero que me expliques algo") is None


def test_detect_document_literal_spanish() -> None:
    intent = detect_tool_intent("crea un documento llamado prueba.md que diga Hola Evano")
    assert intent.tool_id == "create_markdown_document"
    assert intent.name == "prueba.md"
    assert intent.content.mode == "literal"
    assert intent.content.text == "Hola Evano"


def test_detect_document_literal_english() -> None:
    intent = detect_tool_intent("create a document called notes that says Hello world")
    assert intent.tool_id == "create_markdown_document"
    assert intent.name == "notes"
    assert intent.content.text == "Hello world"


def test_detect_document_generate() -> None:
    intent = detect_tool_intent("create a document about local AI agents")
    assert intent.tool_id == "create_markdown_document"
    assert intent.content.mode == "generate"
    assert "local AI agents" in intent.content.topic


def test_detect_text_file_spanish() -> None:
    intent = detect_tool_intent("crea un archivo llamado notes.txt que diga hola")
    assert intent.tool_id == "create_text_file"
    assert intent.name == "notes.txt"
    assert intent.content.text == "hola"


def test_detect_report_generate() -> None:
    intent = detect_tool_intent("create a report about Q1 sales")
    assert intent.tool_id == "create_text_report"
    assert intent.content.mode == "generate"


def test_detect_save_as_document() -> None:
    intent = detect_tool_intent("save this as a document")
    assert intent.tool_id == "create_markdown_document"
    assert intent.content.mode == "from_history"


def test_detect_spanish_list_read_search() -> None:
    assert detect_tool_intent("lista mis archivos").tool_id == "list_files"
    assert detect_tool_intent("lee el archivo notes.txt").tool_id == "read_text_file"
    assert detect_tool_intent("busca en el workspace por factura").tool_id == "search_workspace"


# ---- orchestrator end-to-end (no model needed for literal content) -------- #


def test_chat_creates_document_with_literal_content(client: TestClient, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    client.post("/workspace/configure", json={"path": str(ws)})
    agent = client.post(
        "/agents",
        json={
            "name": "Writer",
            "model_name": "x",
            "enabled_tools": ["create_folder", "create_markdown_document"],
        },
    ).json()

    # Spanish folder
    r1 = client.post(
        f"/agents/{agent['id']}/chat", json={"message": "crea una carpeta llamada Clientes"}
    ).json()
    assert r1["ok"] is True and r1["tool_execution"]["tool_id"] == "create_folder"
    assert (ws / "Clientes").is_dir()

    # Spanish document with literal content (no model call needed)
    r2 = client.post(
        f"/agents/{agent['id']}/chat",
        json={"message": "crea un documento llamado prueba.md que diga Hola Evano"},
    ).json()
    assert r2["ok"] is True
    assert r2["tool_execution"]["tool_id"] == "create_markdown_document"
    doc = ws / "prueba.md"
    assert doc.is_file()
    assert doc.read_text(encoding="utf-8") == "Hola Evano"

    logs = client.get("/tools/logs").json()
    assert any(e["source"] == "agent" and e["tool_id"] == "create_markdown_document" for e in logs)


def test_chat_permission_denied_shows_error(client: TestClient, tmp_path: Path) -> None:
    client.post("/workspace/configure", json={"path": str(tmp_path / "ws")})
    agent = client.post(
        "/agents", json={"name": "FolderOnly", "model_name": "x", "enabled_tools": ["create_folder"]}
    ).json()
    # Asks for a document, but only the folder tool is enabled.
    r = client.post(
        f"/agents/{agent['id']}/chat",
        json={"message": "create a document called x that says hi"},
    ).json()
    assert r["ok"] is False
    assert r["tool_execution"]["ok"] is False
    assert "permission" in (r["message"] or "").lower()
    # The denial is logged.
    logs = client.get("/tools/logs").json()
    assert any(e["status"] == "error" and e["tool_id"] == "create_markdown_document" for e in logs)


def test_chat_generate_offline_is_graceful(client: TestClient, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    client.post("/workspace/configure", json={"path": str(ws)})
    agent = client.post(
        "/agents",
        json={"name": "W", "model_name": "x", "enabled_tools": ["create_markdown_document"]},
    ).json()
    # "about X" needs the model, which is offline in this fixture → clean failure.
    r = client.post(
        f"/agents/{agent['id']}/chat", json={"message": "create a document about cats"}
    ).json()
    assert r["ok"] is False
    assert r["tool_execution"]["ok"] is False
    # Nothing was written.
    assert not any(p.suffix == ".md" for p in ws.glob("*"))


def test_agent_chat_runs_tool_when_enabled(client: TestClient, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    client.post("/workspace/configure", json={"path": str(ws)})
    agent = client.post(
        "/agents", json={"name": "Worker", "model_name": "x", "enabled_tools": ["create_folder"]}
    ).json()

    response = client.post(
        f"/agents/{agent['id']}/chat", json={"message": "Create a folder called Clients"}
    ).json()
    assert response["ok"] is True
    assert response["tool_execution"] is not None
    assert response["tool_execution"]["tool_id"] == "create_folder"
    assert (ws / "Clients").is_dir()
    # Logged as an agent-sourced execution.
    logs = client.get("/tools/logs").json()
    assert any(e["source"] == "agent" and e["tool_id"] == "create_folder" for e in logs)


def test_agent_chat_tool_without_permission_is_clear(client: TestClient, tmp_path: Path) -> None:
    client.post("/workspace/configure", json={"path": str(tmp_path / "ws")})
    # Agent with NO tools enabled: a clear tool request must NOT be answered by the
    # model pretending it worked — it returns a clear "enable the tool" message.
    agent = client.post("/agents", json={"name": "Plain", "model_name": "x"}).json()
    response = client.post(
        f"/agents/{agent['id']}/chat", json={"message": "Create a folder called Clients"}
    ).json()
    assert response["ok"] is False
    assert response["tool_execution"] is not None
    assert response["tool_execution"]["tool_id"] == "create_folder"
    assert "permission" in (response["message"] or "").lower()
    # And no folder was created.
    assert not (tmp_path / "ws" / "Clients").exists()


def test_agent_chat_non_tool_message_falls_through(client: TestClient, tmp_path: Path) -> None:
    client.post("/workspace/configure", json={"path": str(tmp_path / "ws")})
    agent = client.post("/agents", json={"name": "Plain", "model_name": "x"}).json()
    # A normal message (no tool intent) still goes to the model (offline here).
    response = client.post(
        f"/agents/{agent['id']}/chat", json={"message": "Hello, how are you?"}
    ).json()
    assert response["tool_execution"] is None
    assert response["ok"] is False  # ollama offline
