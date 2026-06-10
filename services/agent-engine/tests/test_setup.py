"""Tests for the Easy Start /setup/status aggregator."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    # Point Ollama/ComfyUI at closed ports so the aggregator stays offline-fast.
    settings = Settings(
        data_dir=tmp_path,
        environment="test",
        embedding_provider="hash",
        ollama_base_url="http://127.0.0.1:9",
        ollama_timeout_seconds=0.5,
        comfyui_base_url="http://127.0.0.1:9",
        comfyui_timeout_seconds=0.5,
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_setup_status_shape(client: TestClient) -> None:
    body = client.get("/setup/status").json()
    for key in ("backend", "ollama", "models", "sqlite", "workspace", "chromadb", "comfyui", "agents"):
        assert key in body

    assert body["backend"]["running"] is True
    assert body["sqlite"]["connected"] is True
    assert body["sqlite"]["table_count"] > 0
    # Ollama unreachable on a closed port → reported offline, not an error.
    assert body["ollama"]["reachable"] is False
    assert body["comfyui"]["reachable"] is False


def test_setup_status_reflects_workspace_and_agents(client: TestClient, tmp_path: Path) -> None:
    client.post("/workspace/configure", json={"path": str(tmp_path / "ws")})
    agent = client.post(
        "/agents", json={"name": "A", "model_name": "x", "enabled_tools": ["create_folder"]}
    ).json()
    assert agent["enabled_tools"] == ["create_folder"]

    body = client.get("/setup/status").json()
    assert body["workspace"]["configured"] is True
    assert body["workspace"]["ready"] is True
    assert body["agents"]["count"] == 1
    assert body["agents"]["with_tools"] == 1
