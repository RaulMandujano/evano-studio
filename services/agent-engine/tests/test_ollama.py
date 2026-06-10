"""Tests for the Ollama endpoints.

These point the backend at a closed local port so Ollama is guaranteed
unreachable — verifying graceful offline handling without needing Ollama
installed or any model present.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture()
def offline_client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(
        data_dir=tmp_path,
        environment="test",
        ollama_base_url="http://127.0.0.1:9",  # closed port → unreachable
        ollama_timeout_seconds=0.5,
        ollama_chat_timeout_seconds=0.5,
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_ollama_status_offline(offline_client: TestClient) -> None:
    response = offline_client.get("/ollama/status")
    assert response.status_code == 200
    body = response.json()
    assert body["reachable"] is False
    assert body["status"] in ("offline", "error")
    assert body["model_count"] == 0
    assert body["recommended_model"] == "gemma4"
    assert body["message"]


def test_ollama_models_offline(offline_client: TestClient) -> None:
    response = offline_client.get("/ollama/models")
    assert response.status_code == 200
    body = response.json()
    assert body["reachable"] is False
    assert body["models"] == []
    assert body["count"] == 0
    assert body["message"]


def test_ollama_chat_test_offline(offline_client: TestClient) -> None:
    response = offline_client.post("/ollama/chat/test", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["message"]


def test_recommended_models(offline_client: TestClient) -> None:
    response = offline_client.get("/ollama/models/recommended")
    assert response.status_code == 200
    body = response.json()
    # The curated list is returned even when Ollama is unreachable.
    assert body["reachable"] is False
    assert body["recommended_model"] == "gemma4"
    assert len(body["models"]) >= 5
    first = body["models"][0]
    assert {"model", "name", "category", "notes", "installed"} <= set(first.keys())
    # Nothing is reported as installed when Ollama is offline.
    assert all(m["installed"] is False for m in body["models"])
    # Families requested by the product are represented.
    families = {m["family"] for m in body["models"]}
    assert {"gemma", "qwen", "llama", "mistral", "deepseek"} <= families


def test_pull_status_idle_for_unknown_model(offline_client: TestClient) -> None:
    response = offline_client.get("/ollama/models/pull/status", params={"model": "nope:1b"})
    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "nope:1b"
    assert body["state"] == "idle"


def test_pull_starts_and_fails_gracefully_when_offline(offline_client: TestClient) -> None:
    start = offline_client.post("/ollama/models/pull", json={"model": "llama3.2:3b"})
    assert start.status_code == 200
    assert start.json()["model"] == "llama3.2:3b"
    assert start.json()["state"] in ("pending", "downloading", "error")

    # The background pull against a closed port should resolve to an error.
    final_state = None
    for _ in range(40):
        status = offline_client.get(
            "/ollama/models/pull/status", params={"model": "llama3.2:3b"}
        ).json()
        final_state = status["state"]
        if final_state in ("error", "success"):
            break
        time.sleep(0.05)
    assert final_state == "error"
