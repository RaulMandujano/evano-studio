"""Tests for the ready-made agent templates."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(data_dir=tmp_path, environment="test", embedding_provider="hash")
    with TestClient(create_app(settings)) as c:
        yield c


def test_templates_listed_and_valid(client: TestClient) -> None:
    templates = client.get("/agents/templates").json()
    ids = {t["id"] for t in templates}
    assert {"office-assistant", "writer", "researcher", "computer-assistant"} <= ids
    # Every template's tools are real tools.
    tool_ids = {t["id"] for t in client.get("/tools").json()}
    for t in templates:
        assert t["enabled_tools"], t["id"]
        assert set(t["enabled_tools"]) <= tool_ids, t["id"]


def test_create_agent_from_template(client: TestClient) -> None:
    template = next(t for t in client.get("/agents/templates").json() if t["id"] == "office-assistant")
    created = client.post(
        "/agents",
        json={
            "name": template["name"],
            "model_name": "gemma4",
            "system_prompt": template["system_prompt"],
            "temperature": template["temperature"],
            "knowledge_enabled": template["knowledge_enabled"],
            "enabled_tools": template["enabled_tools"],
        },
    ).json()
    assert created["enabled_tools"] == template["enabled_tools"]
    assert "create_folder" in created["enabled_tools"]


def test_templates_route_not_shadowed_by_agent_id(client: TestClient) -> None:
    # "/agents/templates" must resolve to the templates route, not GET /agents/{id}.
    assert client.get("/agents/templates").status_code == 200
