"""Database models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import ConfigDict
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from ..utils.time import utc_now
from .base import TimestampMixin


class AppSetting(TimestampMixin, table=True):
    """A single key/value application setting (local preferences/config).

    Values are stored as text. Structured values can be JSON-encoded by callers.
    """

    __tablename__ = "app_settings"

    key: str = Field(primary_key=True, index=True)
    value: str = Field(default="")


class ServiceStatusLog(SQLModel, table=True):
    """An append-only record of service lifecycle/status events.

    Used for local diagnostics (e.g. "started"). Must never contain secrets or
    private user content (see docs/SECURITY.md).
    """

    __tablename__ = "service_status_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    service: str = Field(index=True)
    status: str
    message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)


class Agent(TimestampMixin, table=True):
    """A local AI agent configuration powered by an Ollama model."""

    # `model_name` starts with the protected "model_" prefix; allow it.
    model_config = ConfigDict(protected_namespaces=())  # type: ignore[assignment]

    __tablename__ = "agents"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = Field(default="")
    system_prompt: str = Field(default="")
    model_name: str
    temperature: float = Field(default=0.7)
    is_enabled: bool = Field(default=True)
    knowledge_enabled: bool = Field(default=False)
    image_enabled: bool = Field(default=False)
    # IDs of tools this agent is explicitly allowed to use (deny-by-default).
    enabled_tools: list[str] = Field(default_factory=list, sa_column=Column(JSON))


class Document(TimestampMixin, table=True):
    """A local document created by a user or an agent, stored in the workspace."""

    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    file_name: str = Field(index=True)
    file_type: str  # "md" | "txt" | "html"
    file_path: str  # absolute path inside the workspace
    created_by_agent_id: Optional[int] = Field(default=None, index=True)


class KnowledgeDocument(TimestampMixin, table=True):
    """A document imported into the local knowledge base (ChromaDB-backed)."""

    __tablename__ = "knowledge_documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    file_name: str = Field(index=True)
    source_path: str = Field(default="")
    collection_name: str = Field(index=True)
    chunk_count: int = Field(default=0)


class Routine(TimestampMixin, table=True):
    """A locally scheduled agent task. Runs only while the backend is running."""

    __tablename__ = "routines"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    # Built-in Evano agent (0 / unused when this routine targets an OpenClaw agent).
    agent_id: int = Field(default=0, index=True)
    # When set, the routine runs an OpenClaw agent (by its OpenClaw id) instead.
    openclaw_agent_id: Optional[str] = Field(default=None, index=True)
    # When set, the routine runs a whole saved Team workflow (autonomous flow).
    team_id: Optional[int] = Field(default=None, index=True)
    prompt: str = Field(default="")
    schedule_type: str  # manual | once | daily | weekly
    schedule_value: str = Field(default="")  # e.g. "09:00" or "mon 09:00"
    # Routine time fields are naive LOCAL datetimes (a local desktop scheduler).
    start_at: Optional[datetime] = Field(default=None)
    end_at: Optional[datetime] = Field(default=None)
    is_enabled: bool = Field(default=True)
    last_run_at: Optional[datetime] = Field(default=None)
    next_run_at: Optional[datetime] = Field(default=None, index=True)
    status: str = Field(default="idle")


class Team(TimestampMixin, table=True):
    """A saved multi-agent workflow: ordered OpenClaw agents, each with a task.

    Steps is a JSON list of {"agent_id": str, "instruction": str} — the agent at
    position N runs its instruction using the previous step's output as input, so
    a team completes a real task as a pipeline.
    """

    __tablename__ = "teams"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    steps: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    # Optional shared file that flows agent→agent: each step works on it in its
    # own workspace, then it's copied to the next agent's workspace.
    working_file: Optional[str] = Field(default=None)


class ImageGeneration(TimestampMixin, table=True):
    """Metadata for a local image generation request (via local ComfyUI)."""

    __tablename__ = "image_generations"

    id: Optional[int] = Field(default=None, primary_key=True)
    prompt: str
    negative_prompt: Optional[str] = Field(default=None)
    workflow_name: Optional[str] = Field(default=None)
    status: str = Field(default="pending")  # pending | success | error
    output_path: Optional[str] = Field(default=None)
    error: Optional[str] = Field(default=None)
    created_by_agent_id: Optional[int] = Field(default=None, index=True)


class ToolExecutionLog(SQLModel, table=True):
    """An append-only record of every tool execution (visible to the user).

    Tools are how agents take real local actions, so each run is logged for
    transparency: when, which agent (if any), which tool, a short action
    summary, whether it succeeded, and a brief detail. Never stores file
    contents or other private payloads — only metadata (see docs/SECURITY.md).
    """

    __tablename__ = "tool_execution_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: Optional[int] = Field(default=None, index=True)
    agent_name: Optional[str] = Field(default=None)
    tool_id: str = Field(index=True)
    tool_name: str = Field(default="")
    # How the tool was invoked: "manual" (test page) | "agent" (chat intent).
    source: str = Field(default="manual")
    action: str = Field(default="")  # short human-readable summary
    status: str = Field(default="success")  # success | error
    detail: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)


class PendingAction(SQLModel, table=True):
    """A sensitive computer-control action an agent proposed, awaiting human
    approval (human-in-the-loop). Nothing runs until a person approves it."""

    __tablename__ = "pending_actions"

    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: Optional[int] = Field(default=None, index=True)
    agent_name: Optional[str] = Field(default=None)
    tool_id: str = Field(index=True)
    tool_name: str = Field(default="")
    summary: str = Field(default="")  # human-readable description
    preview: str = Field(default="")  # the exact app/url/command to be run
    args: dict = Field(default_factory=dict, sa_column=Column(JSON))
    status: str = Field(default="pending", index=True)  # pending|approved|denied|done|error
    result: Optional[str] = Field(default=None)
    error: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)
    resolved_at: Optional[datetime] = Field(default=None)


class OrgLink(TimestampMixin, table=True):
    """One reporting line in the org chart: agent_id reports to parent_agent_id.

    Both ids are OpenClaw agent ids. Agents with no row are top-level. The chart
    is applied to OpenClaw as real delegation permissions (subagents.allowAgents),
    so a manager can only command its direct reports — deny-by-default.
    """

    __tablename__ = "org_links"

    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: str = Field(index=True, unique=True)
    parent_agent_id: str = Field(index=True)


class RoutineRun(TimestampMixin, table=True):
    """A logged execution of a routine (visible output, no hidden actions)."""

    __tablename__ = "routine_runs"

    id: Optional[int] = Field(default=None, primary_key=True)
    routine_id: int = Field(index=True)
    trigger: str  # manual | scheduled
    status: str  # success | error | missed
    started_at: Optional[datetime] = Field(default=None)
    finished_at: Optional[datetime] = Field(default=None)
    output: str = Field(default="")
    document_path: Optional[str] = Field(default=None)
    error: Optional[str] = Field(default=None)
