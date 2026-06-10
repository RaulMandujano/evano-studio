"""FastAPI application factory and entrypoint.

Run in development::

    uvicorn app.main:app --reload --host 127.0.0.1 --port 8765

or::

    python -m app.main
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlmodel import Session

from .api.router import api_router
from .core.config import Settings, get_settings
from .core.errors import register_exception_handlers
from .core.logging import configure_logging
from .db.session import create_db_engine, init_db
from .services.database_service import record_status
from .services.discord_connector import DiscordConnector
from .services.routine_runner import RoutineScheduler

logger = logging.getLogger("evano.agent_engine")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize the database and log lifecycle events."""
    settings: Settings = app.state.settings
    app.state.start_time = time.monotonic()

    # Create the engine and ensure tables exist (lightweight migration).
    engine = create_db_engine(settings)
    init_db(engine)
    app.state.engine = engine
    logger.info("Database ready at %s", settings.resolved_database_url)

    # Record a non-sensitive startup event for local diagnostics.
    with Session(engine) as session:
        record_status(
            session,
            service="agent-engine",
            status="started",
            message=f"v{settings.version}",
        )

    # Start the local routine scheduler (runs only while the backend runs).
    scheduler: RoutineScheduler | None = None
    if settings.routine_scheduler_enabled:
        scheduler = RoutineScheduler(engine, settings)
        scheduler.start()
    app.state.scheduler = scheduler

    # Optional Discord channel (off unless enabled+configured in settings).
    discord = DiscordConnector(engine, settings)
    app.state.discord = discord
    discord.start()

    logger.info(
        "%s starting (env=%s) on http://%s:%s",
        settings.app_name,
        settings.environment,
        settings.host,
        settings.port,
    )
    yield
    logger.info("%s shutting down", settings.app_name)
    if scheduler is not None:
        scheduler.stop()
    discord.stop()
    engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        summary="Local backend for Evano Studio. Local-only, privacy-first.",
        lifespan=lifespan,
    )
    # Make settings available to lifespan and dependencies.
    app.state.settings = settings
    # Sensible fallback so uptime works even before lifespan runs (e.g. tests).
    app.state.start_time = time.monotonic()
    # The engine is created during lifespan startup (keeps imports side-effect free).
    app.state.engine = None

    # Local-only CORS: only the desktop app on localhost/127.0.0.1 may call us.
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=settings.cors_allow_origin_regex,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    @app.get("/", tags=["meta"], summary="Service root")
    def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": settings.version,
            "docs": "/docs",
        }

    return app


app = create_app()


def run() -> None:
    """Entry point for ``python -m app.main`` and the ``agent-engine`` script."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
    )


if __name__ == "__main__":
    run()
