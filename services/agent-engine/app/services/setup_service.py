"""Setup service — aggregates subsystem status for the Easy Start wizard.

Reuses the existing per-subsystem services so there is a single source of truth.
Each section is computed defensively: a failure in one subsystem (e.g. Ollama
offline) never breaks the overall response.
"""

from __future__ import annotations

import time

from sqlmodel import Session

from ..core.config import Settings
from ..schemas.setup import (
    SetupAgents,
    SetupBackend,
    SetupChroma,
    SetupComfyUI,
    SetupModels,
    SetupOllama,
    SetupSqlite,
    SetupStatusResponse,
    SetupWorkspace,
)
from .agent_service import AgentService
from .chroma_service import ChromaService
from .database_service import DatabaseService
from .image_service import ImageService
from .knowledge_service import KnowledgeService
from .ollama_service import OllamaService
from .workspace_service import WorkspaceService


class SetupService:
    def __init__(self, session: Session, settings: Settings, start_time: float) -> None:
        self._session = session
        self._settings = settings
        self._start_time = start_time

    def status(self) -> SetupStatusResponse:
        return SetupStatusResponse(
            backend=self._backend(),
            ollama=self._ollama_block(),
            models=self._models(),
            sqlite=self._sqlite(),
            workspace=self._workspace(),
            chromadb=self._chromadb(),
            comfyui=self._comfyui(),
            agents=self._agents(),
        )

    def _backend(self) -> SetupBackend:
        return SetupBackend(
            running=True,
            version=self._settings.version,
            uptime_seconds=round(max(0.0, time.monotonic() - self._start_time), 3),
        )

    def _ollama_block(self) -> SetupOllama:
        try:
            status = OllamaService(self._settings).get_status()
            return SetupOllama(
                status=status.status,
                reachable=status.reachable,
                version=status.version,
                recommended_model=status.recommended_model,
                recommended_available=status.recommended_available,
            )
        except Exception:  # noqa: BLE001
            return SetupOllama(
                status="error",
                reachable=False,
                recommended_model=self._settings.ollama_recommended_model,
                recommended_available=False,
            )

    def _models(self) -> SetupModels:
        try:
            result = OllamaService(self._settings).list_models()
            return SetupModels(count=result.count, installed=[m.name for m in result.models])
        except Exception:  # noqa: BLE001
            return SetupModels(count=0, installed=[])

    def _sqlite(self) -> SetupSqlite:
        try:
            status = DatabaseService(self._session, self._settings).status()
            return SetupSqlite(
                connected=status.connected,
                file_exists=status.file_exists,
                table_count=len(status.tables),
                path=status.database_path,
            )
        except Exception:  # noqa: BLE001
            return SetupSqlite(connected=False, file_exists=False)

    def _workspace(self) -> SetupWorkspace:
        status = WorkspaceService(self._session, self._settings).status()
        missing = [s.name for s in status.subdirs if not s.exists]
        return SetupWorkspace(
            configured=status.configured,
            path=status.path,
            exists=status.exists,
            ready=status.ready,
            missing_subdirs=missing,
        )

    def _chromadb(self) -> SetupChroma:
        try:
            chroma = ChromaService(self._settings)
            status = KnowledgeService(self._session, self._settings, chroma).status()
            return SetupChroma(
                available=status.available,
                document_count=status.document_count,
                message=status.message,
            )
        except Exception as exc:  # noqa: BLE001
            return SetupChroma(available=False, message=str(exc))

    def _comfyui(self) -> SetupComfyUI:
        try:
            status = ImageService(self._session, self._settings).status()
            return SetupComfyUI(
                enabled=status.enabled, reachable=status.reachable, message=status.message
            )
        except Exception as exc:  # noqa: BLE001
            return SetupComfyUI(enabled=False, reachable=False, message=str(exc))

    def _agents(self) -> SetupAgents:
        try:
            agents = AgentService(self._session).list_agents()
            with_tools = sum(1 for a in agents if a.enabled_tools)
            return SetupAgents(count=len(agents), with_tools=with_tools)
        except Exception:  # noqa: BLE001
            return SetupAgents(count=0, with_tools=0)
