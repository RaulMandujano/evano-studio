"""Database service — reports local database status (no HTTP here)."""

from __future__ import annotations

from sqlalchemy import func, inspect
from sqlmodel import Session, select

from ..core.config import Settings
from ..db.models import AppSetting, ServiceStatusLog
from ..schemas.database import DatabaseStatusResponse


class DatabaseService:
    """Provides non-sensitive information about the local database."""

    def __init__(self, session: Session, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    def _count(self, model: type) -> int:
        result = self._session.exec(select(func.count()).select_from(model)).one()
        return int(result)

    def status(self) -> DatabaseStatusResponse:
        # If we have a working session, we are connected.
        engine = self._session.get_bind()
        tables = sorted(inspect(engine).get_table_names())

        db_path = self._settings.sqlite_file_path
        file_exists = bool(db_path and db_path.exists())
        size_bytes = db_path.stat().st_size if file_exists and db_path else None

        return DatabaseStatusResponse(
            connected=True,
            engine="sqlite",
            database_path=str(db_path) if db_path else None,
            file_exists=file_exists,
            size_bytes=size_bytes,
            tables=tables,
            settings_count=self._count(AppSetting),
            status_log_count=self._count(ServiceStatusLog),
        )


def record_status(session: Session, *, service: str, status: str, message: str | None = None) -> None:
    """Append a service status log entry (used at startup)."""
    session.add(ServiceStatusLog(service=service, status=status, message=message))
    session.commit()
