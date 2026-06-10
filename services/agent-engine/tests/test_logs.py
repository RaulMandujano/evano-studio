"""Tests for the logs endpoint and the support bundle."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(
        data_dir=tmp_path,
        environment="test",
        embedding_provider="hash",
        ollama_base_url="http://127.0.0.1:9",
        ollama_timeout_seconds=0.5,
        comfyui_timeout_seconds=0.5,
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_logs_endpoint_returns_entries(client: TestClient) -> None:
    # Generate a categorized log entry: a created document.
    client.post("/documents", json={"title": "Note", "content": "hi"})

    body = client.get("/logs").json()
    assert isinstance(body["entries"], list)
    for entry in body["entries"]:
        assert {"timestamp", "level", "area", "logger", "message"} <= set(entry.keys())
    # The startup entry is always present.
    assert any("started" in e["message"].lower() for e in body["entries"])


def test_logs_area_filter(client: TestClient) -> None:
    client.post("/documents", json={"title": "Filtered", "content": "x"})
    body = client.get("/logs", params={"area": "Documents"}).json()
    assert len(body["entries"]) >= 1
    assert all(e["area"] == "Documents" for e in body["entries"])


def test_logs_file_written(client: TestClient, tmp_path: Path) -> None:
    client.get("/health")
    log_file = tmp_path / "logs" / "agent-engine.log"
    assert log_file.exists()


def test_support_bundle(client: TestClient, tmp_path: Path) -> None:
    response = client.post("/support/bundle")
    assert response.status_code == 200
    body = response.json()

    # File written locally.
    path = Path(body["path"])
    assert path.exists()
    assert path.parent == (tmp_path / "logs").resolve()

    bundle = body["bundle"]
    # Required sections present.
    for key in ("app", "os", "database", "ollama", "chromadb", "comfyui", "routines", "recent_logs"):
        assert key in bundle
    assert bundle["app"]["version"]
    assert "installed_models" in bundle["ollama"]
    assert isinstance(bundle["recent_logs"], list)
    assert "exclude" in bundle["privacy_note"].lower()

    # The on-disk file is valid JSON with the same shape.
    on_disk = json.loads(path.read_text())
    assert on_disk["app"]["version"] == bundle["app"]["version"]


def test_support_bundle_excludes_private_content(client: TestClient) -> None:
    # Create an agent + routine whose prompt is private content.
    agent = client.post("/agents", json={"name": "A", "model_name": "x"}).json()
    client.post(
        "/routines",
        json={
            "name": "Secret routine",
            "agent_id": agent["id"],
            "prompt": "SUPER_SECRET_PROMPT_TEXT",
            "schedule_type": "manual",
        },
    )
    raw = client.post("/support/bundle").json()
    serialized = json.dumps(raw["bundle"])
    # Routine name may appear, but the prompt content must NOT.
    assert "SUPER_SECRET_PROMPT_TEXT" not in serialized
