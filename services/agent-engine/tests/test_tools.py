"""Tests for the agent tools: registry, execution, permissions, and security."""

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
        embedding_provider="hash",  # keep KB search offline/deterministic
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_list_tools(client: TestClient) -> None:
    tools = client.get("/tools").json()
    ids = {t["id"] for t in tools}
    assert {
        "list_allowed_files",
        "read_allowed_text_file",
        "create_markdown_document",
        "create_text_report",
        "search_knowledge_base",
        "generate_image_prompt",
    } <= ids
    by_id = {t["id"]: t for t in tools}
    # Computer-control tools exist (opt-in) but MUST require human approval; an
    # agent can never run them automatically. Workspace tools never require it.
    for cid in ("open_application", "open_url", "run_command"):
        assert by_id[cid]["requires_approval"] is True
    assert by_id["create_folder"]["requires_approval"] is False


def test_create_then_list_and_read(client: TestClient, tmp_path: Path) -> None:
    created = client.post(
        "/tools/test",
        json={
            "tool_id": "create_markdown_document",
            "params": {"title": "Tool Note", "content": "# Hi\n\nfrom a tool"},
        },
    ).json()
    assert created["ok"] is True
    file_name = created["result"]["file_name"]
    assert file_name == "Tool Note.md"
    # File is inside the workspace.
    assert Path(created["result"]["file_path"]).parent == (tmp_path / "workspace").resolve()

    listed = client.post("/tools/test", json={"tool_id": "list_allowed_files", "params": {}}).json()
    assert any(f["name"] == "Tool Note.md" for f in listed["result"]["files"])

    read = client.post(
        "/tools/test",
        json={"tool_id": "read_allowed_text_file", "params": {"file_name": "Tool Note.md"}},
    ).json()
    assert read["ok"] is True
    assert "from a tool" in read["result"]["content"]


def test_read_blocks_traversal(client: TestClient) -> None:
    result = client.post(
        "/tools/test",
        json={"tool_id": "read_allowed_text_file", "params": {"file_name": "../../etc/passwd"}},
    ).json()
    assert result["ok"] is False
    assert "path" in (result["message"] or "").lower()


def test_generate_image_prompt(client: TestClient) -> None:
    result = client.post(
        "/tools/test",
        json={
            "tool_id": "generate_image_prompt",
            "params": {"subject": "a red fox", "style": "watercolor"},
        },
    ).json()
    assert result["ok"] is True
    assert "red fox" in result["result"]["prompt"]
    assert "watercolor" in result["result"]["prompt"]


def test_missing_required_param(client: TestClient) -> None:
    result = client.post(
        "/tools/test",
        json={"tool_id": "create_text_report", "params": {"title": "No content"}},
    ).json()
    assert result["ok"] is False
    assert "content" in (result["message"] or "")


def test_unknown_tool(client: TestClient) -> None:
    result = client.post("/tools/test", json={"tool_id": "hack_the_planet", "params": {}}).json()
    assert result["ok"] is False
    assert "unknown" in (result["message"] or "").lower()


def test_agent_permission_enforced(client: TestClient) -> None:
    agent = client.post(
        "/agents", json={"name": "Limited", "model_name": "x", "enabled_tools": []}
    ).json()
    # Agent has no tools enabled → execution as that agent is forbidden.
    denied = client.post(
        "/tools/test",
        json={
            "tool_id": "generate_image_prompt",
            "params": {"subject": "cat"},
            "agent_id": agent["id"],
        },
    ).json()
    assert denied["ok"] is False
    assert "not enabled" in (denied["message"] or "").lower()

    # Grant the tool via the dedicated endpoint, then it works.
    updated = client.put(
        f"/agents/{agent['id']}/tools",
        json={"enabled_tools": ["generate_image_prompt"]},
    ).json()
    assert updated["enabled_tools"] == ["generate_image_prompt"]

    allowed = client.post(
        "/tools/test",
        json={
            "tool_id": "generate_image_prompt",
            "params": {"subject": "cat"},
            "agent_id": agent["id"],
        },
    ).json()
    assert allowed["ok"] is True


def test_set_tools_rejects_unknown(client: TestClient) -> None:
    agent = client.post("/agents", json={"name": "A", "model_name": "x"}).json()
    response = client.put(
        f"/agents/{agent['id']}/tools", json={"enabled_tools": ["not_a_tool"]}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unknown_tool"
