"""Tests for document CRUD and workspace security."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    return tmp_path / "workspace"


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(data_dir=tmp_path, environment="test")
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_create_and_read_markdown(client: TestClient, workspace: Path) -> None:
    response = client.post(
        "/documents",
        json={"title": "My Notes", "content": "# Hello\n\nWorld", "file_type": "md"},
    )
    assert response.status_code == 201, response.text
    doc = response.json()
    assert doc["file_name"] == "My Notes.md"
    assert doc["file_type"] == "md"
    assert doc["exists"] is True

    # File is on disk inside the workspace.
    file_path = Path(doc["file_path"])
    assert file_path.exists()
    assert file_path.parent == workspace.resolve()

    # Content is readable via GET.
    detail = client.get(f"/documents/{doc['id']}").json()
    assert detail["content"] == "# Hello\n\nWorld"


def test_list_and_delete(client: TestClient) -> None:
    created = client.post("/documents", json={"title": "Doc A", "content": "x"}).json()
    assert len(client.get("/documents").json()) == 1

    file_path = Path(created["file_path"])
    assert client.delete(f"/documents/{created['id']}").json() == {"ok": True}
    assert client.get("/documents").json() == []
    assert not file_path.exists()  # the file is removed too
    assert client.delete(f"/documents/{created['id']}").status_code == 404


def test_txt_and_html_types(client: TestClient) -> None:
    txt = client.post("/documents", json={"title": "Plain", "content": "hi", "file_type": "txt"}).json()
    assert txt["file_name"] == "Plain.txt"

    html = client.post(
        "/documents",
        json={"title": "Report", "content": "Line one\n\nLine two", "file_type": "html"},
    ).json()
    assert html["file_name"] == "Report.html"
    content = client.get(f"/documents/{html['id']}").json()["content"]
    assert "<!doctype html>" in content.lower()
    assert "<title>Report</title>" in content


def test_filename_is_sanitized_against_traversal(client: TestClient, workspace: Path) -> None:
    doc = client.post(
        "/documents",
        json={"title": "evil", "file_name": "../../etc/passwd", "content": "x"},
    ).json()
    file_path = Path(doc["file_path"])
    # No traversal: the file stays directly inside the workspace.
    assert file_path.parent == workspace.resolve()
    assert ".." not in doc["file_name"]
    assert "/" not in doc["file_name"]


def test_no_overwrite_unless_allowed(client: TestClient) -> None:
    body = {"title": "Same", "content": "v1"}
    assert client.post("/documents", json=body).status_code == 201

    # Same name again → conflict.
    dup = client.post("/documents", json=body)
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "file_exists"

    # With overwrite, it succeeds.
    ok = client.post("/documents", json={**body, "content": "v2", "overwrite": True})
    assert ok.status_code == 201
    detail = client.get(f"/documents/{ok.json()['id']}").json()
    assert detail["content"] == "v2"


def test_from_agent_response(client: TestClient) -> None:
    response = client.post(
        "/documents/from-agent-response",
        json={"title": "Summary", "content": "Generated text", "agent_id": 7},
    )
    assert response.status_code == 201
    doc = response.json()
    assert doc["created_by_agent_id"] == 7
    assert doc["file_name"] == "Summary.md"
