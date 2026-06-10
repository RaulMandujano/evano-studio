"""Tests for the Discord channel status + config (no live Discord connection)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.discord import get_discord_config
from app.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(data_dir=tmp_path, environment="test", embedding_provider="hash")
    with TestClient(create_app(settings)) as c:
        yield c


def test_discord_status_default_off(client: TestClient) -> None:
    s = client.get("/discord/status").json()
    assert s["enabled"] is False
    assert s["configured"] is False
    assert s["state"] in ("disabled", "stopped")
    # discord.py is a dependency, so it should be importable.
    assert s["available"] is True


def test_discord_status_reflects_settings(client: TestClient) -> None:
    agent = client.post("/agents", json={"name": "A", "model_name": "x"}).json()
    client.put(
        "/settings",
        json={
            "settings": {
                "discord_enabled": "true",
                "discord_bot_token": "fake-token",
                "discord_agent_id": str(agent["id"]),
                "discord_allowed_user_ids": "111,222",
            }
        },
    )
    s = client.get("/discord/status").json()
    assert s["enabled"] is True
    assert s["configured"] is True
    assert s["agent_id"] == agent["id"]
    assert s["allowed_count"] == 2
    # Connector was started (disabled) at boot → asks for a restart to connect.
    assert "restart" in (s["message"] or "").lower()


def test_discord_config_parsing_and_allowlist(client: TestClient) -> None:
    client.put(
        "/settings",
        json={"settings": {"discord_allowed_user_ids": " 111 ; 222, 333 "}},
    )
    # Read config straight from the DB via a session.
    engine = client.app.state.engine
    from sqlmodel import Session

    with Session(engine) as session:
        cfg = get_discord_config(session)
    assert cfg.allowed_user_ids == ["111", "222", "333"]
    assert cfg.is_allowed("222") is True
    assert cfg.is_allowed("999") is False
