"""Tests for agent CRUD and chat.

Uses an offline Ollama (closed port) so chat behavior is deterministic without
needing a model installed.
"""

from __future__ import annotations

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
        ollama_base_url="http://127.0.0.1:9",  # unreachable → deterministic chat
        ollama_timeout_seconds=0.5,
        ollama_chat_timeout_seconds=0.5,
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def _make(client: TestClient, **overrides) -> dict:
    body = {"name": "Helper", "model_name": "llama3.2:3b", **overrides}
    response = client.post("/agents", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_and_list(client: TestClient) -> None:
    assert client.get("/agents").json() == []

    agent = _make(client, description="A helpful assistant", temperature=0.5)
    assert agent["id"] >= 1
    assert agent["name"] == "Helper"
    assert agent["temperature"] == 0.5
    assert agent["is_enabled"] is True

    listed = client.get("/agents").json()
    assert len(listed) == 1
    assert listed[0]["id"] == agent["id"]


def test_get_404(client: TestClient) -> None:
    response = client.get("/agents/9999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_update(client: TestClient) -> None:
    agent = _make(client)
    response = client.put(
        f"/agents/{agent['id']}",
        json={"name": "Renamed", "is_enabled": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Renamed"
    assert body["is_enabled"] is False
    # Unspecified fields are unchanged.
    assert body["model_name"] == "llama3.2:3b"


def test_delete(client: TestClient) -> None:
    agent = _make(client)
    assert client.delete(f"/agents/{agent['id']}").json() == {"ok": True}
    assert client.get(f"/agents/{agent['id']}").status_code == 404
    assert client.delete(f"/agents/{agent['id']}").status_code == 404


def test_create_validation_error(client: TestClient) -> None:
    # Missing required model_name.
    response = client.post("/agents", json={"name": "X"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_chat_offline_graceful(client: TestClient) -> None:
    agent = _make(client)
    response = client.post(f"/agents/{agent['id']}/chat", json={"message": "Hello"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False  # Ollama unreachable in tests
    assert body["model"] == "llama3.2:3b"
    assert body["message"]


def test_chat_disabled_agent(client: TestClient) -> None:
    agent = _make(client, is_enabled=False)
    response = client.post(f"/agents/{agent['id']}/chat", json={"message": "Hello"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert "disabled" in body["message"].lower()
