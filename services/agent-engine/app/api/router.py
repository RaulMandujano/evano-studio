"""Aggregates all API routers into a single router for the app to include."""

from __future__ import annotations

from fastapi import APIRouter

from . import (
    actions,
    activity,
    afm,
    agents,
    database,
    discord,
    documents,
    health,
    images,
    knowledge,
    logs,
    ollama,
    openclaw,
    org,
    routines,
    settings,
    setup,
    system,
    teams,
    tools,
    version,
    workspace,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(version.router)
api_router.include_router(system.router)
api_router.include_router(setup.router)
api_router.include_router(workspace.router)
api_router.include_router(settings.router)
api_router.include_router(database.router)
api_router.include_router(ollama.router)
api_router.include_router(agents.router)
api_router.include_router(teams.router)
api_router.include_router(documents.router)
api_router.include_router(knowledge.router)
api_router.include_router(tools.router)
api_router.include_router(actions.router)
api_router.include_router(routines.router)
api_router.include_router(routines.calendar_router)
api_router.include_router(images.comfyui_router)
api_router.include_router(images.images_router)
api_router.include_router(logs.logs_router)
api_router.include_router(logs.support_router)
api_router.include_router(discord.router)
api_router.include_router(openclaw.router)
api_router.include_router(activity.router)
api_router.include_router(org.router)
api_router.include_router(afm.router)
