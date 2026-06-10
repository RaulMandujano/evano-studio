"""Tests for ComfyUI settings/status and image generation (offline-graceful)."""

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
        comfyui_timeout_seconds=0.5,
        comfyui_poll_timeout_seconds=1.0,
        comfyui_poll_interval_seconds=0.2,
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_status_default_disabled(client: TestClient) -> None:
    body = client.get("/comfyui/status").json()
    assert body["enabled"] is False
    assert "base_url" in body
    assert body["reachable"] in (True, False)  # probed regardless


def test_update_settings_persists(client: TestClient) -> None:
    updated = client.put(
        "/comfyui/settings",
        json={"enabled": True, "base_url": "http://127.0.0.1:9"},
    ).json()
    assert updated["enabled"] is True
    assert updated["base_url"] == "http://127.0.0.1:9"

    status = client.get("/comfyui/status").json()
    assert status["enabled"] is True
    assert status["reachable"] is False  # closed port
    assert status["message"]


def test_prompt_test_when_disabled(client: TestClient) -> None:
    body = client.post("/comfyui/prompt/test", json={"prompt": "a cat"}).json()
    assert body["ok"] is False
    assert "disabled" in (body["message"] or "").lower()


def test_prompt_test_offline(client: TestClient) -> None:
    client.put("/comfyui/settings", json={"enabled": True, "base_url": "http://127.0.0.1:9"})
    body = client.post("/comfyui/prompt/test", json={"prompt": "a cat"}).json()
    assert body["ok"] is False
    assert body["reachable"] is False


def test_generate_disabled_records_error(client: TestClient) -> None:
    record = client.post("/images/generate", json={"prompt": "a fox"}).json()
    assert record["status"] == "error"
    assert "disabled" in (record["error"] or "").lower()
    # History reflects it.
    assert len(client.get("/images").json()) == 1


def test_generate_offline_records_error(client: TestClient) -> None:
    client.put("/comfyui/settings", json={"enabled": True, "base_url": "http://127.0.0.1:9"})
    record = client.post(
        "/images/generate", json={"prompt": "a fox", "negative_prompt": "blurry"}
    ).json()
    assert record["status"] == "error"
    assert record["error"]
    assert record["output_path"] is None
