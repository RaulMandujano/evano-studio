"""Tests for the settings endpoints and persistence."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_settings_start_empty(client: TestClient) -> None:
    response = client.get("/settings")
    assert response.status_code == 200
    assert response.json() == {"settings": {}}


def test_put_settings_creates_and_returns(client: TestClient) -> None:
    response = client.put(
        "/settings",
        json={"settings": {"theme": "dark", "default_model": "gemma"}},
    )
    assert response.status_code == 200
    assert response.json()["settings"] == {"theme": "dark", "default_model": "gemma"}

    # Persisted and readable via GET.
    assert client.get("/settings").json()["settings"]["theme"] == "dark"


def test_put_settings_merges_and_updates(client: TestClient) -> None:
    client.put("/settings", json={"settings": {"theme": "dark"}})
    client.put("/settings", json={"settings": {"theme": "light", "lang": "en"}})

    settings = client.get("/settings").json()["settings"]
    assert settings == {"theme": "light", "lang": "en"}
