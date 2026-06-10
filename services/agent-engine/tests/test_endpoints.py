"""Smoke tests for the meta/system endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"]
    assert body["version"]


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"]
    assert body["version"]
    assert body["uptime_seconds"] >= 0


def test_version(client: TestClient) -> None:
    response = client.get("/version")
    assert response.status_code == 200
    body = response.json()
    assert body["name"]
    assert body["version"]
    assert body["environment"]


def test_system_info(client: TestClient) -> None:
    response = client.get("/system/info")
    assert response.status_code == 200
    body = response.json()
    assert body["python_version"]
    assert body["platform"]
    assert "timestamp" in body
    assert body["workspace_path"]
    features = body["features"]
    # All V1 integrations are wired up; runtime status is per-endpoint.
    assert features["database"] is True
    assert features["ollama"] is True
    assert features["chromadb"] is True
    assert features["comfyui"] is True


def test_unknown_route_returns_structured_error(client: TestClient) -> None:
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "http_error"
