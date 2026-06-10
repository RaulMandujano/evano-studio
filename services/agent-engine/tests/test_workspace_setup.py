"""Tests for workspace setup + the new filesystem tools and tool logging."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.workspace import WORKSPACE_SUBDIRS
from app.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(data_dir=tmp_path, environment="test", embedding_provider="hash")
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_workspace_status_default(client: TestClient) -> None:
    status = client.get("/workspace/status").json()
    assert status["is_default"] is True
    assert status["configured"] is False
    # Default workspace isn't structured until configured.
    assert status["ready"] is False


def test_configure_workspace_creates_subdirs(client: TestClient, tmp_path: Path) -> None:
    target = tmp_path / "MyWorkspace"
    status = client.post("/workspace/configure", json={"path": str(target)}).json()
    assert status["configured"] is True
    assert status["ready"] is True
    assert target.is_dir()
    for name in WORKSPACE_SUBDIRS:
        assert (target / name).is_dir()
    # All standard subdirs are reported as existing.
    assert all(s["exists"] for s in status["subdirs"])


def test_configure_rejects_relative_path(client: TestClient) -> None:
    response = client.post("/workspace/configure", json={"path": "relative/dir"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_path"


def test_reset_workspace(client: TestClient, tmp_path: Path) -> None:
    client.post("/workspace/configure", json={"path": str(tmp_path / "ws")})
    reset = client.post("/workspace/configure", json={"path": ""}).json()
    assert reset["is_default"] is True


def test_create_folder_tool_and_log(client: TestClient, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    client.post("/workspace/configure", json={"path": str(ws)})

    result = client.post(
        "/tools/test", json={"tool_id": "create_folder", "params": {"folder_name": "Clients"}}
    ).json()
    assert result["ok"] is True
    assert (ws / "Clients").is_dir()

    # The action is visible in the tool-execution log.
    logs = client.get("/tools/logs").json()
    assert any(e["tool_id"] == "create_folder" and e["status"] == "success" for e in logs)


def test_create_folder_in_parent(client: TestClient, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    client.post("/workspace/configure", json={"path": str(ws)})
    result = client.post(
        "/tools/test",
        json={"tool_id": "create_folder", "params": {"folder_name": "Q1", "parent": "Projects"}},
    ).json()
    assert result["ok"] is True
    assert (ws / "Projects" / "Q1").is_dir()


def test_create_read_write_text_file_in_subfolder(client: TestClient, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    client.post("/workspace/configure", json={"path": str(ws)})

    created = client.post(
        "/tools/test",
        json={
            "tool_id": "create_text_file",
            "params": {"file_name": "plan", "content": "hello", "folder": "Projects"},
        },
    ).json()
    assert created["ok"] is True
    assert created["result"]["name"] == "plan.txt"
    assert (ws / "Projects" / "plan.txt").read_text() == "hello"

    # Creating the same file again fails (use write to overwrite).
    again = client.post(
        "/tools/test",
        json={
            "tool_id": "create_text_file",
            "params": {"file_name": "plan", "content": "x", "folder": "Projects"},
        },
    ).json()
    assert again["ok"] is False

    overwritten = client.post(
        "/tools/test",
        json={"tool_id": "write_text_file", "params": {"path": "Projects/plan.txt", "content": "v2"}},
    ).json()
    assert overwritten["ok"] is True
    assert overwritten["result"]["overwritten"] is True

    read = client.post(
        "/tools/test", json={"tool_id": "read_text_file", "params": {"path": "Projects/plan.txt"}}
    ).json()
    assert read["ok"] is True
    assert read["result"]["content"] == "v2"


def test_list_files_tool(client: TestClient, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    client.post("/workspace/configure", json={"path": str(ws)})
    listed = client.post("/tools/test", json={"tool_id": "list_files", "params": {}}).json()
    assert listed["ok"] is True
    names = {e["name"] for e in listed["result"]["entries"]}
    assert "Documents" in names  # standard subfolders show up


def test_search_workspace_tool(client: TestClient, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    client.post("/workspace/configure", json={"path": str(ws)})
    client.post(
        "/tools/test",
        json={"tool_id": "write_text_file", "params": {"path": "secret.txt", "content": "ZEBRA-77 token"}},
    )
    result = client.post(
        "/tools/test", json={"tool_id": "search_workspace", "params": {"query": "ZEBRA-77"}}
    ).json()
    assert result["ok"] is True
    assert result["result"]["count"] >= 1
    assert any(m["file"] == "secret.txt" for m in result["result"]["matches"])


def test_file_tools_return_verified_contract(client: TestClient, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    client.post("/workspace/configure", json={"path": str(ws)})

    created = client.post(
        "/tools/test",
        json={"tool_id": "create_text_file", "params": {"file_name": "test-real.txt", "content": "Hola Evano"}},
    ).json()
    assert created["ok"] is True
    res = created["result"]
    # Full file-tool contract.
    for key in ("success", "tool_name", "relative_path", "absolute_path", "bytes_written", "verified_exists", "message"):
        assert key in res, key
    assert res["success"] is True
    assert res["verified_exists"] is True
    assert res["tool_name"] == "create_text_file"
    assert res["relative_path"] == "test-real.txt"
    assert res["bytes_written"] == len("Hola Evano".encode("utf-8"))
    # absolute_path points at the real, configured workspace and the file exists.
    abs_path = Path(res["absolute_path"])
    assert abs_path == (ws / "test-real.txt").resolve()
    assert abs_path.read_text(encoding="utf-8") == "Hola Evano"

    # Markdown documents return the same contract and land in the workspace.
    doc = client.post(
        "/tools/test",
        json={"tool_id": "create_markdown_document", "params": {"title": "reporte", "content": "# Resumen"}},
    ).json()["result"]
    assert doc["verified_exists"] is True
    assert doc["relative_path"] == "reporte.md"
    assert (ws / "reporte.md").is_file()


def test_create_text_file_without_content_makes_empty_file(client: TestClient, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    client.post("/workspace/configure", json={"path": str(ws)})
    client.post("/tools/test", json={"tool_id": "create_folder", "params": {"folder_name": "HOLA EVANO"}})
    # No "content" param + a .doc name inside the subfolder (the user's real case).
    res = client.post(
        "/tools/test",
        json={"tool_id": "create_text_file", "params": {"file_name": "HolaEvano.doc", "folder": "HOLA EVANO"}},
    ).json()
    assert res["ok"] is True
    assert res["result"]["verified_exists"] is True
    assert res["result"]["relative_path"] == "HOLA EVANO/HolaEvano.doc"
    target = ws / "HOLA EVANO" / "HolaEvano.doc"
    assert target.is_file()  # exact name kept (not renamed to .doc.txt)
    assert target.read_text() == ""


def test_executable_extensions_blocked(client: TestClient, tmp_path: Path) -> None:
    client.post("/workspace/configure", json={"path": str(tmp_path / "ws")})
    res = client.post(
        "/tools/test",
        json={"tool_id": "create_text_file", "params": {"file_name": "evil.sh", "content": "rm -rf /"}},
    ).json()
    assert res["ok"] is False
    assert "blocked" in (res["message"] or "").lower() or ".sh" in (res["message"] or "")


def test_new_file_tools_block_traversal(client: TestClient, tmp_path: Path) -> None:
    client.post("/workspace/configure", json={"path": str(tmp_path / "ws")})
    for tool, params in [
        ("write_text_file", {"path": "../../escape.txt", "content": "x"}),
        ("read_text_file", {"path": "../../../etc/passwd"}),
        ("create_folder", {"folder_name": "x", "parent": "../.."}),
    ]:
        result = client.post("/tools/test", json={"tool_id": tool, "params": params}).json()
        assert result["ok"] is False, tool
