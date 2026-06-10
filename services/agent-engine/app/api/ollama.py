"""Ollama integration endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..schemas.ollama import (
    ChatTestRequest,
    ChatTestResponse,
    OllamaModelsResponse,
    OllamaStatusResponse,
    PullRequest,
    PullStatusResponse,
    RecommendedModelsResponse,
)
from ..services.ollama_service import OllamaService
from .deps import get_ollama_service

router = APIRouter(prefix="/ollama", tags=["ollama"])


@router.get("/status", response_model=OllamaStatusResponse, summary="Ollama runtime status")
def get_ollama_status(
    service: OllamaService = Depends(get_ollama_service),
) -> OllamaStatusResponse:
    return service.get_status()


@router.get("/models", response_model=OllamaModelsResponse, summary="Installed Ollama models")
def get_ollama_models(
    service: OllamaService = Depends(get_ollama_service),
) -> OllamaModelsResponse:
    return service.list_models()


@router.post("/chat/test", response_model=ChatTestResponse, summary="One-shot local chat test")
def post_ollama_chat_test(
    payload: ChatTestRequest,
    service: OllamaService = Depends(get_ollama_service),
) -> ChatTestResponse:
    return service.chat_test(payload.model, payload.prompt)


@router.get(
    "/models/recommended",
    response_model=RecommendedModelsResponse,
    summary="Curated free models the user can install",
)
def get_recommended_models(
    service: OllamaService = Depends(get_ollama_service),
) -> RecommendedModelsResponse:
    return service.get_recommended()


@router.post(
    "/models/pull",
    response_model=PullStatusResponse,
    summary="Start installing a model (runs in the background)",
)
def post_pull_model(
    payload: PullRequest,
    service: OllamaService = Depends(get_ollama_service),
) -> PullStatusResponse:
    """Begin a background pull and return the initial status. The user explicitly
    chooses the model — nothing is auto-installed. Poll the status endpoint for
    progress."""
    return service.start_pull(payload.model)


@router.get(
    "/models/pull/status",
    response_model=PullStatusResponse,
    summary="Poll the progress of a model pull",
)
def get_pull_status(
    model: str,
    service: OllamaService = Depends(get_ollama_service),
) -> PullStatusResponse:
    return service.get_pull_status(model)
