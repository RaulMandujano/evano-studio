"""System service — builds health/version/system responses.

Pure logic, no HTTP. This keeps the API layer thin and the logic testable.
"""

from __future__ import annotations

import platform
import time

from ..core.config import Settings
from ..schemas.system import (
    FeatureFlags,
    HealthResponse,
    SystemInfoResponse,
    VersionResponse,
)
from ..utils.time import utc_now


class SystemService:
    """Reports basic, non-sensitive service and runtime information."""

    def __init__(self, settings: Settings, start_time: float) -> None:
        self._settings = settings
        self._start_time = start_time

    def uptime_seconds(self) -> float:
        """Seconds since the service started (monotonic, never negative)."""
        return round(max(0.0, time.monotonic() - self._start_time), 3)

    def health(self) -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=self._settings.app_name,
            version=self._settings.version,
            uptime_seconds=self.uptime_seconds(),
        )

    def version(self) -> VersionResponse:
        return VersionResponse(
            name=self._settings.app_name,
            version=self._settings.version,
            environment=self._settings.environment,
        )

    def system_info(self) -> SystemInfoResponse:
        return SystemInfoResponse(
            service=self._settings.app_name,
            version=self._settings.version,
            environment=self._settings.environment,
            python_version=platform.python_version(),
            platform=platform.platform(),
            timestamp=utc_now(),
            uptime_seconds=self.uptime_seconds(),
            # Backend integrations that are wired up. Runtime status for each is
            # reported by its own endpoint (e.g. /ollama/status, /comfyui/status).
            features=FeatureFlags(database=True, ollama=True, chromadb=True, comfyui=True),
            workspace_path=str(self._settings.workspace_path),
        )
