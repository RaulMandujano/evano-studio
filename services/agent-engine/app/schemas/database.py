"""Schemas for the database status endpoint."""

from __future__ import annotations

from pydantic import BaseModel


class DatabaseStatusResponse(BaseModel):
    """Non-sensitive status of the local database."""

    connected: bool
    engine: str
    database_path: str | None
    file_exists: bool
    size_bytes: int | None
    tables: list[str]
    settings_count: int
    status_log_count: int
