"""ComfyUI settings/status and image generation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..core.comfyui import get_comfyui_config, set_comfyui_config
from ..core.config import Settings
from ..db.session import get_session
from ..schemas.image import (
    ComfyUISettingsRead,
    ComfyUISettingsUpdate,
    ComfyUIStatusResponse,
    ImageGenerateRequest,
    ImageGenerationRead,
    PromptTestRequest,
    PromptTestResponse,
)
from ..services.image_service import ImageService
from .deps import get_app_settings, get_image_service

comfyui_router = APIRouter(prefix="/comfyui", tags=["comfyui"])
images_router = APIRouter(prefix="/images", tags=["images"])


@comfyui_router.get("/status", response_model=ComfyUIStatusResponse, summary="ComfyUI status")
def comfyui_status(service: ImageService = Depends(get_image_service)) -> ComfyUIStatusResponse:
    return service.status()


@comfyui_router.put("/settings", response_model=ComfyUISettingsRead, summary="Update ComfyUI settings")
def update_comfyui_settings(
    payload: ComfyUISettingsUpdate,
    session=Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> ComfyUISettingsRead:
    set_comfyui_config(
        session,
        base_url=payload.base_url,
        enabled=payload.enabled,
        default_workflow_path=payload.default_workflow_path,
    )
    config = get_comfyui_config(session, settings)
    return ComfyUISettingsRead(
        base_url=config.base_url,
        enabled=config.enabled,
        default_workflow_path=config.default_workflow_path,
    )


@comfyui_router.post("/prompt/test", response_model=PromptTestResponse, summary="Test ComfyUI connectivity + workflow")
def comfyui_prompt_test(
    payload: PromptTestRequest,
    service: ImageService = Depends(get_image_service),
) -> PromptTestResponse:
    return service.test_prompt(payload.prompt, payload.negative_prompt)


@images_router.get("", response_model=list[ImageGenerationRead], summary="Image generation history")
def list_images(service: ImageService = Depends(get_image_service)) -> list[ImageGenerationRead]:
    return [ImageGenerationRead.model_validate(i) for i in service.list_images()]


@images_router.post("/generate", response_model=ImageGenerationRead, summary="Generate an image (local ComfyUI)")
def generate_image(
    payload: ImageGenerateRequest,
    service: ImageService = Depends(get_image_service),
) -> ImageGenerationRead:
    """Generate an image via the local ComfyUI. Returns a record with status
    success/error — failures (disabled/unreachable/etc.) are reported, not raised."""
    return ImageGenerationRead.model_validate(service.generate(payload))
