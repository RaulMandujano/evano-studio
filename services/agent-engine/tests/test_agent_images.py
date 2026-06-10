"""Tests for agent image endpoints (offline-graceful, permission checks)."""

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
        ollama_base_url="http://127.0.0.1:9",
        ollama_timeout_seconds=0.5,
        ollama_chat_timeout_seconds=0.5,
        comfyui_timeout_seconds=0.5,
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def _agent(client: TestClient, **kw) -> dict:
    body = {"name": "Artist", "model_name": "x", **kw}
    return client.post("/agents", json=body).json()


def test_image_prompt_offline(client: TestClient) -> None:
    agent = _agent(client)
    body = client.post(
        f"/agents/{agent['id']}/image-prompt",
        json={"idea": "a fox in a forest", "style": "watercolor"},
    ).json()
    # Ollama offline → ok False with a message, not a crash.
    assert body["ok"] is False
    assert body["model"] == "x"
    assert body["message"]


def test_image_prompt_disabled_agent(client: TestClient) -> None:
    agent = _agent(client, is_enabled=False)
    body = client.post(
        f"/agents/{agent['id']}/image-prompt", json={"idea": "a fox"}
    ).json()
    assert body["ok"] is False
    assert "disabled" in (body["message"] or "").lower()


def test_generate_image_requires_image_enabled(client: TestClient) -> None:
    agent = _agent(client, image_enabled=False)
    response = client.post(
        f"/agents/{agent['id']}/generate-image", json={"prompt": "a fox"}
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "image_not_enabled"


def test_generate_image_records_error_when_comfyui_disabled(client: TestClient) -> None:
    agent = _agent(client, image_enabled=True)
    record = client.post(
        f"/agents/{agent['id']}/generate-image",
        json={"prompt": "a fox in a forest"},
    ).json()
    # ComfyUI disabled → record with error, attributed to the agent.
    assert record["status"] == "error"
    assert record["error"]
    assert record["created_by_agent_id"] == agent["id"]

    # Visible in image history.
    history = client.get("/images").json()
    assert any(i["created_by_agent_id"] == agent["id"] for i in history)
