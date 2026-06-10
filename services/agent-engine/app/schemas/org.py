"""Schemas for the org chart (who manages whom)."""

from __future__ import annotations

from pydantic import BaseModel


class OrgAgent(BaseModel):
    id: str
    name: str
    emoji: str = ""
    model: str = ""
    workspace: str = ""
    is_default: bool = False


class OrgLinkItem(BaseModel):
    agent_id: str
    parent_agent_id: str = ""  # empty → top level (no manager)


class OrgChartResponse(BaseModel):
    ok: bool
    message: str = ""
    agents: list[OrgAgent]
    links: list[OrgLinkItem]


class OrgSaveRequest(BaseModel):
    links: list[OrgLinkItem]


class OrgActionResult(BaseModel):
    ok: bool
    message: str = ""
