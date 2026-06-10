"""Request-scoped dependencies for the API layer."""

from __future__ import annotations

import time

from fastapi import Depends, Request
from sqlmodel import Session

from ..core.config import Settings, get_settings
from ..db.session import get_session
from ..services.afm_service import AFMService
from ..services.agent_service import AgentService
from ..services.chroma_service import ChromaService
from ..services.database_service import DatabaseService
from ..services.document_service import DocumentService
from ..services.image_service import ImageService
from ..services.knowledge_service import KnowledgeService
from ..services.ollama_service import OllamaService
from ..services.org_service import OrgService
from ..services.routine_service import RoutineService
from ..services.settings_service import SettingsService
from ..services.setup_service import SetupService
from ..services.system_service import SystemService
from ..services.team_service import TeamService
from ..services.tool_service import ToolService
from ..services.workspace_service import WorkspaceService


def get_app_settings(request: Request) -> Settings:
    """Return the Settings instance the app was created with (fallback: global)."""
    settings = getattr(request.app.state, "settings", None)
    return settings if settings is not None else get_settings()


def get_system_service(
    request: Request,
    settings: Settings = Depends(get_app_settings),
) -> SystemService:
    """Build a SystemService using the app's recorded start time.

    Falls back to "now" if the start time hasn't been set (e.g. when the app's
    lifespan didn't run), which simply yields ~0 uptime rather than an error.
    """
    start_time = getattr(request.app.state, "start_time", None)
    if start_time is None:
        start_time = time.monotonic()
    return SystemService(settings=settings, start_time=start_time)


def get_settings_service(session: Session = Depends(get_session)) -> SettingsService:
    return SettingsService(session=session)


def get_database_service(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> DatabaseService:
    return DatabaseService(session=session, settings=settings)


def get_ollama_service(settings: Settings = Depends(get_app_settings)) -> OllamaService:
    return OllamaService(settings=settings)


def get_agent_service(session: Session = Depends(get_session)) -> AgentService:
    return AgentService(session=session)


def get_team_service(session: Session = Depends(get_session)) -> TeamService:
    return TeamService(session=session)


def get_org_service(session: Session = Depends(get_session)) -> OrgService:
    return OrgService(session=session)


def get_afm_service(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> AFMService:
    return AFMService(session=session, settings=settings)


def get_document_service(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> DocumentService:
    return DocumentService(session=session, settings=settings)


def get_chroma_service(settings: Settings = Depends(get_app_settings)) -> ChromaService:
    return ChromaService(settings=settings)


def get_knowledge_service(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
    chroma: ChromaService = Depends(get_chroma_service),
) -> KnowledgeService:
    return KnowledgeService(session=session, settings=settings, chroma=chroma)


def get_tool_service(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> ToolService:
    return ToolService(session=session, settings=settings)


def get_routine_service(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> RoutineService:
    return RoutineService(session=session, settings=settings)


def get_image_service(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> ImageService:
    return ImageService(session=session, settings=settings)


def get_workspace_service(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> WorkspaceService:
    return WorkspaceService(session=session, settings=settings)


def get_setup_service(
    request: Request,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> SetupService:
    start_time = getattr(request.app.state, "start_time", None)
    if start_time is None:
        start_time = time.monotonic()
    return SetupService(session=session, settings=settings, start_time=start_time)
