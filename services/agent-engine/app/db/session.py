"""Engine creation, lightweight initialization, and the session dependency.

Migration strategy: this project uses a **lightweight create-on-startup**
approach (``SQLModel.metadata.create_all``) rather than Alembic. ``create_all``
only creates tables that don't already exist, so it is safe to run on every
startup. A full migration tool (e.g. Alembic) can be added later if/when the
schema needs to evolve in backward-incompatible ways.
"""

from __future__ import annotations

from typing import Iterator

from fastapi import Request
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from ..core.config import Settings

# Import models so they are registered on SQLModel.metadata before create_all().
from . import models  # noqa: F401


def _is_memory_url(url: str) -> bool:
    return ":memory:" in url or url == "sqlite://"


def create_db_engine(settings: Settings) -> Engine:
    """Create a SQLAlchemy engine for the configured SQLite database.

    Ensures the parent directory exists for file-based databases, and uses a
    shared static pool for in-memory databases (so tests see one connection).
    """
    url = settings.resolved_database_url
    # SQLite + FastAPI's threadpool requires disabling the same-thread check.
    connect_args = {"check_same_thread": False}

    if _is_memory_url(url):
        return create_engine(url, connect_args=connect_args, poolclass=StaticPool)

    db_path = settings.sqlite_file_path
    if db_path is not None:
        db_path.parent.mkdir(parents=True, exist_ok=True)

    return create_engine(url, connect_args=connect_args)


def init_db(engine: Engine) -> None:
    """Create any missing tables, then apply small additive migrations.

    Safe to call on every startup. ``create_all`` only creates missing tables, so
    new columns on existing tables are added here with idempotent ALTERs.
    """
    SQLModel.metadata.create_all(engine)
    _apply_additive_migrations(engine)


def _apply_additive_migrations(engine: Engine) -> None:
    """Add columns introduced after a table already existed (idempotent)."""
    from sqlalchemy import text

    # (table, column, column definition)
    additions = [
        ("agents", "enabled_tools", "TEXT DEFAULT '[]'"),
        ("routines", "openclaw_agent_id", "TEXT"),
        ("routines", "team_id", "INTEGER"),
        ("teams", "working_file", "TEXT"),
    ]
    with engine.connect() as conn:
        for table, column, definition in additions:
            existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
            if existing and column not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
        conn.commit()


def get_session(request: Request) -> Iterator[Session]:
    """FastAPI dependency yielding a session bound to the app's engine."""
    engine: Engine | None = getattr(request.app.state, "engine", None)
    if engine is None:
        raise RuntimeError("Database engine is not initialized.")
    with Session(engine) as session:
        yield session
