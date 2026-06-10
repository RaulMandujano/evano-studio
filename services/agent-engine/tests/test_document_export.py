"""Tests for real .docx / .pdf document generation tools."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(data_dir=tmp_path, environment="test", embedding_provider="hash")
    with TestClient(create_app(settings)) as c:
        yield c


def test_create_word_document(client: TestClient, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    client.post("/workspace/configure", json={"path": str(ws)})
    res = client.post(
        "/tools/test",
        json={
            "tool_id": "create_word_document",
            "params": {"title": "Informe mensual", "content": "# Resumen\n\nVentas áéíóú\n- punto 1"},
        },
    ).json()
    assert res["ok"] is True
    assert res["result"]["verified_exists"] is True
    path = Path(res["result"]["absolute_path"])
    assert path.name == "Informe mensual.docx"
    assert path.read_bytes()[:2] == b"PK"  # .docx is a zip archive
    assert path.stat().st_size > 1000


def test_create_pdf_document_in_subfolder(client: TestClient, tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    client.post("/workspace/configure", json={"path": str(ws)})
    client.post("/tools/test", json={"tool_id": "create_folder", "params": {"folder_name": "Reportes"}})
    res = client.post(
        "/tools/test",
        json={
            "tool_id": "create_pdf_document",
            "params": {"title": "Reporte", "content": "Hola Evano áéíóú", "folder": "Reportes"},
        },
    ).json()
    assert res["ok"] is True
    assert res["result"]["relative_path"] == "Reportes/Reporte.pdf"
    path = Path(res["result"]["absolute_path"])
    assert path.read_bytes()[:4] == b"%PDF"


def test_doc_tools_listed_no_approval(client: TestClient) -> None:
    by_id = {t["id"]: t for t in client.get("/tools").json()}
    assert "create_word_document" in by_id
    assert "create_pdf_document" in by_id
    # Document creation stays inside the workspace → no approval needed.
    assert by_id["create_word_document"]["requires_approval"] is False
