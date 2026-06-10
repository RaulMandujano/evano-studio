"""OpenClaw control endpoints — detect, install, configure, operate."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..core.config import Settings
from ..db.session import get_session

from ..schemas.openclaw import (
    AddChannelRequest,
    AgentActionResult,
    AgentChatRequest,
    AgentChatResult,
    AgentDiscordResult,
    AgentDiscordStatus,
    AgentDocumentContent,
    AgentDocumentsResponse,
    AgentFilesResponse,
    AllChatsResponse,
    ConnectDiscordRequest,
    ChannelActionResult,
    ChannelsResponse,
    ClearSessionsRequest,
    ClearSessionsResult,
    CreateOpenClawAgentRequest,
    FileHandoffRequest,
    FileHandoffResult,
    DashboardUrlResponse,
    GatewayActionResult,
    OpenClawAgentResult,
    OpenClawAgentsResponse,
    OpenClawConfigRequest,
    OpenClawConfigResult,
    OpenClawInstallStatus,
    OpenClawStatusResponse,
    SaveAgentFileRequest,
    SessionDetail,
    SessionsResponse,
    WebSearchResult,
)
from ..services.activity_service import track
from ..services.chroma_service import ChromaService
from ..services.knowledge_service import KnowledgeService
from ..services.openclaw_service import OpenClawService
from .deps import get_app_settings

router = APIRouter(prefix="/openclaw", tags=["openclaw"])


def get_openclaw_service() -> OpenClawService:
    return OpenClawService()


@router.get("/status", response_model=OpenClawStatusResponse, summary="OpenClaw + prereqs status")
def openclaw_status(service: OpenClawService = Depends(get_openclaw_service)) -> dict:
    return service.status()


@router.post("/install", response_model=OpenClawInstallStatus, summary="Install OpenClaw (npm -g)")
def openclaw_install(service: OpenClawService = Depends(get_openclaw_service)) -> dict:
    return service.start_install()


@router.get("/install/status", response_model=OpenClawInstallStatus, summary="Install progress")
def openclaw_install_status(service: OpenClawService = Depends(get_openclaw_service)) -> dict:
    return service.install_status()


@router.post("/config", response_model=OpenClawConfigResult, summary="Configure OpenClaw")
def openclaw_config(
    payload: OpenClawConfigRequest,
    service: OpenClawService = Depends(get_openclaw_service),
) -> dict:
    """Configure OpenClaw via its own non-interactive onboarding: free (Ollama /
    Gemma 4, no key) or a paid API key. Writes ~/.openclaw/openclaw.json."""
    return service.write_config(
        mode=payload.mode, model=payload.model, api_key=payload.api_key,
        provider=payload.provider, base_url=payload.base_url,
    )


@router.post("/gateway/start", response_model=GatewayActionResult, summary="Start the gateway")
def openclaw_gateway_start(service: OpenClawService = Depends(get_openclaw_service)) -> dict:
    return service.gateway_start()


@router.post("/gateway/stop", response_model=GatewayActionResult, summary="Stop the gateway")
def openclaw_gateway_stop(service: OpenClawService = Depends(get_openclaw_service)) -> dict:
    return service.gateway_stop()


@router.get("/dashboard", response_model=DashboardUrlResponse, summary="Get dashboard URL")
def openclaw_dashboard(service: OpenClawService = Depends(get_openclaw_service)) -> dict:
    """Return the token-authenticated OpenClaw dashboard URL (starts the gateway
    if needed). The desktop embeds it in a panel so clients never leave Evano."""
    return service.dashboard_url()


@router.post("/file-handoff", response_model=FileHandoffResult, summary="Pass a file between agents")
def openclaw_file_handoff(
    payload: FileHandoffRequest,
    service: OpenClawService = Depends(get_openclaw_service),
) -> dict:
    """Copy a working file from one agent's folder to another's (file flows in a team)."""
    return service.handoff_file(
        from_agent_id=payload.from_agent_id,
        to_agent_id=payload.to_agent_id,
        file_name=payload.file_name,
    )


@router.post("/web-search/enable", response_model=WebSearchResult, summary="Enable free web search")
def openclaw_enable_web_search(service: OpenClawService = Depends(get_openclaw_service)) -> dict:
    """Turn on free DuckDuckGo web search (no API key) so agents can search the net."""
    return service.enable_web_search()


@router.get("/channels", response_model=ChannelsResponse, summary="List chat channels")
def openclaw_channels(service: OpenClawService = Depends(get_openclaw_service)) -> dict:
    return service.list_channels()


@router.post("/channels/add", response_model=ChannelActionResult, summary="Connect a channel")
def openclaw_channels_add(
    payload: AddChannelRequest,
    service: OpenClawService = Depends(get_openclaw_service),
) -> dict:
    """Connect a messaging platform (Discord, Telegram, Slack, …) with a token."""
    return service.add_channel(channel=payload.channel, token=payload.token)


@router.get("/agents", response_model=OpenClawAgentsResponse, summary="List OpenClaw agents")
def openclaw_agents(service: OpenClawService = Depends(get_openclaw_service)) -> dict:
    return service.list_agents()


@router.post("/agents", response_model=OpenClawAgentResult, summary="Create an OpenClaw agent")
def openclaw_agent_create(
    payload: CreateOpenClawAgentRequest,
    service: OpenClawService = Depends(get_openclaw_service),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> dict:
    """Create an isolated OpenClaw agent (Gemma 4 by default) with optional
    instructions and identity — it then runs inside OpenClaw. When AFM is
    configured, the new agent's folder is created inside the AFM root."""
    from ..services.afm_service import AFMService

    afm = AFMService(session, settings)
    workspace = str(afm.agent_target_dir(payload.name)) if afm.is_configured() else None
    return service.create_agent(
        name=payload.name, model=payload.model,
        instructions=payload.instructions, emoji=payload.emoji,
        workspace=workspace,
    )


@router.delete("/agents/{agent_id}", response_model=AgentActionResult, summary="Delete an OpenClaw agent")
def openclaw_agent_delete(
    agent_id: str,
    service: OpenClawService = Depends(get_openclaw_service),
) -> dict:
    return service.delete_agent(agent_id)


@router.post("/agents/{agent_id}/chat", response_model=AgentChatResult, summary="Chat with an OpenClaw agent")
def openclaw_agent_chat(
    agent_id: str,
    payload: AgentChatRequest,
    service: OpenClawService = Depends(get_openclaw_service),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> dict:
    """Run one agent turn natively (no dashboard). Pass a stable session_id to keep
    conversation continuity. Can take a while on local models. If the local
    knowledge base has relevant content, it is prepended as context (RAG)."""
    knowledge = KnowledgeService(session, settings, ChromaService(settings))
    message = knowledge.context_block(payload.message) + payload.message

    task = (payload.activity_task or "").strip() or "Answering a chat"
    kind = payload.activity_kind if payload.activity_kind in ("chat", "team") else "chat"
    with track(agent_id=f"openclaw:{agent_id}", agent_name=agent_id, kind=kind, task=task) as outcome:
        result = service.agent_chat(
            agent_id=agent_id, message=message, session_id=payload.session_id
        )
        outcome["ok"] = bool(result.get("ok"))
        if not outcome["ok"]:
            outcome["note"] = result.get("message") or ""
    return result


@router.get("/documents", response_model=AgentDocumentsResponse, summary="Agent work files, grouped")
def openclaw_agent_documents(service: OpenClawService = Depends(get_openclaw_service)) -> dict:
    """The files agents created in their workspaces (reports, drafts, team
    working files) — excluding config/memory/skills. Powers the Documents tab."""
    return service.list_agent_documents()


@router.get("/documents/content", response_model=AgentDocumentContent, summary="Read an agent work file")
def openclaw_agent_document_content(
    agent_id: str,
    path: str,
    service: OpenClawService = Depends(get_openclaw_service),
) -> dict:
    """Bounded text preview of a work file (path is relative to the agent's
    workspace; traversal and config files are refused)."""
    return service.read_agent_document(agent_id, path)


@router.delete("/documents/content", response_model=AgentActionResult, summary="Delete an agent work file")
def openclaw_agent_document_delete(
    agent_id: str,
    path: str,
    service: OpenClawService = Depends(get_openclaw_service),
) -> dict:
    return service.delete_agent_document(agent_id, path)


@router.get("/chats", response_model=AllChatsResponse, summary="All conversations, grouped by agent")
def openclaw_all_chats(service: OpenClawService = Depends(get_openclaw_service)) -> dict:
    """Every saved conversation of every agent, with where it came from
    (Evano app, a team run, Discord, the dashboard, …). Powers the Chats tab."""
    return service.list_all_chats()


@router.get("/agents/{agent_id}/discord", response_model=AgentDiscordStatus, summary="Agent's Discord link")
def openclaw_agent_discord_status(
    agent_id: str,
    service: OpenClawService = Depends(get_openclaw_service),
) -> dict:
    """Is this agent connected to Discord as its own bot?"""
    return service.agent_discord_status(agent_id)


@router.post("/agents/{agent_id}/discord", response_model=AgentDiscordResult, summary="Connect agent to Discord")
def openclaw_agent_discord_connect(
    agent_id: str,
    payload: ConnectDiscordRequest,
    service: OpenClawService = Depends(get_openclaw_service),
) -> dict:
    """Make this agent a Discord bot: register its bot token as the agent's own
    channel account, bind it, and reload the gateway. The token is never logged."""
    return service.connect_agent_discord(agent_id=agent_id, bot_token=payload.bot_token)


@router.delete("/agents/{agent_id}/discord", response_model=AgentDiscordResult, summary="Disconnect agent from Discord")
def openclaw_agent_discord_disconnect(
    agent_id: str,
    service: OpenClawService = Depends(get_openclaw_service),
) -> dict:
    return service.disconnect_agent_discord(agent_id)


@router.get("/agents/{agent_id}/sessions", response_model=SessionsResponse, summary="Conversation history")
def openclaw_agent_sessions(
    agent_id: str,
    service: OpenClawService = Depends(get_openclaw_service),
) -> dict:
    """List saved conversations for an agent (persisted by OpenClaw on disk)."""
    return service.list_sessions(agent_id)


@router.get("/agents/{agent_id}/sessions/{session_id}", response_model=SessionDetail, summary="Load a conversation")
def openclaw_agent_session(
    agent_id: str,
    session_id: str,
    service: OpenClawService = Depends(get_openclaw_service),
) -> dict:
    return service.get_session(agent_id, session_id)


@router.delete("/agents/{agent_id}/sessions/{session_id}", response_model=AgentActionResult, summary="Delete a conversation")
def openclaw_agent_session_delete(
    agent_id: str,
    session_id: str,
    service: OpenClawService = Depends(get_openclaw_service),
) -> dict:
    return service.delete_session(agent_id, session_id)


@router.post("/agents/{agent_id}/sessions/clear", response_model=ClearSessionsResult, summary="Clear conversation history")
def openclaw_agent_sessions_clear(
    agent_id: str,
    payload: ClearSessionsRequest,
    service: OpenClawService = Depends(get_openclaw_service),
) -> dict:
    """Delete all conversations (or only those older than N days) to free disk."""
    return service.clear_sessions(agent_id, older_than_days=payload.older_than_days)


@router.get("/agents/{agent_id}/files", response_model=AgentFilesResponse, summary="Agent config files")
def openclaw_agent_files(
    agent_id: str,
    service: OpenClawService = Depends(get_openclaw_service),
) -> dict:
    """Read the agent's workspace config files (IDENTITY/AGENTS/SOUL/…)."""
    return service.get_agent_files(agent_id)


@router.put("/agents/{agent_id}/files/{name}", response_model=AgentActionResult, summary="Save an agent config file")
def openclaw_agent_file_save(
    agent_id: str,
    name: str,
    payload: SaveAgentFileRequest,
    service: OpenClawService = Depends(get_openclaw_service),
) -> dict:
    return service.save_agent_file(agent_id=agent_id, name=name, content=payload.content)
