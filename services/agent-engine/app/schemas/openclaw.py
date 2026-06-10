"""Schemas for the OpenClaw control endpoints."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class ToolPresence(BaseModel):
    installed: bool
    version: Optional[str] = None


class OpenClawConfigSummary(BaseModel):
    exists: bool
    path: str
    provider: Optional[str] = None
    model: Optional[str] = None


class GatewayInfo(BaseModel):
    running: bool
    port: int


class WebSearchInfo(BaseModel):
    provider: Optional[str] = None
    enabled: bool = False


class OpenClawStatusResponse(BaseModel):
    node: ToolPresence
    npm: ToolPresence
    ollama: ToolPresence
    openclaw: ToolPresence
    config: OpenClawConfigSummary
    gateway: GatewayInfo
    web_search: WebSearchInfo = WebSearchInfo()
    ready: bool


class WebSearchResult(BaseModel):
    ok: bool
    message: str = ""
    web_search: WebSearchInfo = WebSearchInfo()


class OpenClawInstallStatus(BaseModel):
    state: str  # idle | running | success | error
    message: str = ""
    log_tail: str = ""


class OpenClawConfigRequest(BaseModel):
    mode: Literal["free", "api"] = "free"
    model: str = "gemma4:latest"
    provider: Optional[str] = None  # for mode="api" (e.g. anthropic, openai)
    api_key: Optional[str] = None
    base_url: Optional[str] = None  # for mode="free" (Ollama URL)


class OpenClawConfigResult(BaseModel):
    ok: bool
    message: str = ""
    config: OpenClawConfigSummary


class GatewayActionResult(BaseModel):
    ok: bool
    message: str = ""
    running: bool = False


class DashboardUrlResponse(BaseModel):
    ok: bool
    url: Optional[str] = None
    message: str = ""


class ChannelInfo(BaseModel):
    slug: str
    name: str
    icon: str = "💬"
    connect: str = "token"  # token | login
    can_add: bool = True
    installed: bool = False
    configured: bool = False
    popular: bool = False


class ChannelsResponse(BaseModel):
    ok: bool
    message: str = ""
    channels: list[ChannelInfo] = []


class AddChannelRequest(BaseModel):
    channel: str
    token: str


class ChannelActionResult(BaseModel):
    ok: bool
    message: str = ""


class OpenClawAgent(BaseModel):
    id: str
    name: str = ""
    model: str = ""
    workspace: str = ""
    is_default: bool = False
    bindings: int = 0


class OpenClawAgentsResponse(BaseModel):
    ok: bool
    message: str = ""
    agents: list[OpenClawAgent] = []


class CreateOpenClawAgentRequest(BaseModel):
    name: str
    model: Optional[str] = None  # defaults to ollama/gemma4:latest (free)
    instructions: Optional[str] = None
    emoji: Optional[str] = None


class OpenClawAgentResult(BaseModel):
    ok: bool
    message: str = ""
    agent: Optional[OpenClawAgent] = None


class AgentActionResult(BaseModel):
    ok: bool
    message: str = ""


class FileHandoffRequest(BaseModel):
    from_agent_id: str
    to_agent_id: str
    file_name: str


class FileHandoffResult(BaseModel):
    ok: bool
    message: str = ""
    path: Optional[str] = None


class AgentChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # stable id → conversation continuity
    activity_task: Optional[str] = None  # short label shown in the Office view
    activity_kind: Optional[str] = None  # chat | team (anything else falls back to chat)


class AgentChatResult(BaseModel):
    ok: bool
    reply: str = ""
    model: str = ""
    session_id: str = ""
    message: str = ""


class AgentWorkFile(BaseModel):
    name: str
    path: str  # relative to the agent's workspace
    size_bytes: int = 0
    modified_at: int = 0  # epoch ms
    abs_path: str = ""


class AgentDocumentsGroup(BaseModel):
    agent_id: str
    name: str
    emoji: str = ""
    files: list[AgentWorkFile] = []


class AgentDocumentsResponse(BaseModel):
    ok: bool
    message: str = ""
    agents: list[AgentDocumentsGroup] = []


class AgentDocumentContent(BaseModel):
    ok: bool
    message: str = ""
    name: str = ""
    content: str = ""
    truncated: bool = False


class AgentDiscordStatus(BaseModel):
    ok: bool
    connected: bool
    account_id: str = ""
    gateway_running: bool = False
    message: str = ""


class ConnectDiscordRequest(BaseModel):
    bot_token: str


class AgentDiscordResult(BaseModel):
    ok: bool
    message: str = ""


class AgentFile(BaseModel):
    name: str
    label: str
    size: int = 0
    content: str = ""
    exists: bool = False


class AgentFilesResponse(BaseModel):
    ok: bool
    message: str = ""
    workspace: str = ""
    files: list[AgentFile] = []


class SaveAgentFileRequest(BaseModel):
    content: str = ""


class SessionSummary(BaseModel):
    session_id: str
    preview: str = ""
    message_count: int = 0
    updated_at: int = 0  # epoch ms
    size_bytes: int = 0
    # Where the chat came from: evano | team | discord | telegram | whatsapp |
    # slack | dashboard | subagent | cron | other
    origin: str = "other"


class AgentChats(BaseModel):
    agent_id: str
    name: str
    emoji: str = ""
    sessions: list[SessionSummary] = []


class AllChatsResponse(BaseModel):
    ok: bool
    message: str = ""
    agents: list[AgentChats] = []


class SessionsResponse(BaseModel):
    ok: bool
    message: str = ""
    sessions: list[SessionSummary] = []
    total_bytes: int = 0


class SessionMessage(BaseModel):
    role: str
    content: str


class SessionDetail(BaseModel):
    ok: bool
    message: str = ""
    messages: list[SessionMessage] = []


class ClearSessionsRequest(BaseModel):
    older_than_days: Optional[int] = None  # None/0 = clear all


class ClearSessionsResult(BaseModel):
    ok: bool
    message: str = ""
    deleted: int = 0
    freed_bytes: int = 0
