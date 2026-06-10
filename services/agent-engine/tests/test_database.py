"""Tests for the database status endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_database_status(client: TestClient) -> None:
    response = client.get("/database/status")
    assert response.status_code == 200
    body = response.json()

    assert body["connected"] is True
    assert body["engine"] == "sqlite"
    # Tables created by the lightweight init.
    assert "app_settings" in body["tables"]
    assert "service_status_logs" in body["tables"]
    # Startup recorded one service status log entry.
    assert body["status_log_count"] >= 1
    assert body["settings_count"] == 0


def test_database_status_reflects_settings(client: TestClient) -> None:
    client.put("/settings", json={"settings": {"a": "1", "b": "2"}})
    body = client.get("/database/status").json()
    assert body["settings_count"] == 2
