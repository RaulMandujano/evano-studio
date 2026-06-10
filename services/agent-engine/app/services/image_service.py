"""Image generation orchestration (ComfyUI). Saves files into the workspace.

ComfyUI is optional: if it's disabled/unreachable, generation records a clean
error instead of failing the whole app.
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlmodel import Session, select

from ..core.comfyui import get_comfyui_config
from ..core.config import Settings
from ..core.errors import AppError
from ..core.paths import resolve_within, sanitize_filename
from ..core.workspace import effective_workspace
from ..db.models import ImageGeneration
from ..schemas.image import (
    ComfyUIStatusResponse,
    ImageGenerateRequest,
    PromptTestResponse,
)
from .comfyui_service import ComfyUIService

logger = logging.getLogger("evano.agent_engine.images")


class ImageService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._config = get_comfyui_config(session, settings)
        self._adapter = ComfyUIService(self._config, settings)

    # ---- status / test --------------------------------------------------- #

    def status(self) -> ComfyUIStatusResponse:
        reachable, version, message = self._adapter.status()
        return ComfyUIStatusResponse(
            enabled=self._config.enabled,
            base_url=self._config.base_url,
            reachable=reachable,
            version=version,
            default_workflow_path=self._config.default_workflow_path,
            message=message,
        )

    def test_prompt(self, prompt: str, negative: str) -> PromptTestResponse:
        if not self._config.enabled:
            return PromptTestResponse(ok=False, reachable=False, message="ComfyUI is disabled in settings.")
        reachable, _version, message = self._adapter.status()
        if not reachable:
            return PromptTestResponse(ok=False, reachable=False, message=message)
        try:
            graph = self._adapter.build_graph(prompt, negative)
        except AppError as exc:
            return PromptTestResponse(ok=False, reachable=True, message=exc.message)
        return PromptTestResponse(
            ok=True,
            reachable=True,
            message=f"Reachable and workflow is valid ({len(graph)} nodes). No image generated in test.",
        )

    # ---- generation ------------------------------------------------------ #

    def list_images(self) -> list[ImageGeneration]:
        return list(
            self._session.exec(
                select(ImageGeneration).order_by(ImageGeneration.created_at.desc())
            ).all()
        )

    def generate(self, data: ImageGenerateRequest) -> ImageGeneration:
        record = ImageGeneration(
            prompt=data.prompt,
            negative_prompt=data.negative_prompt or None,
            workflow_name=data.workflow_name,
            status="pending",
            created_by_agent_id=data.agent_id,
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)

        if not self._config.enabled:
            return self._fail(record, "ComfyUI is disabled. Enable it in settings first.")

        try:
            image_bytes, _src_name = self._adapter.generate(data.prompt, data.negative_prompt or "")
        except AppError as exc:
            return self._fail(record, exc.message)
        except Exception as exc:  # noqa: BLE001
            return self._fail(record, f"Image generation failed: {exc}")

        try:
            root = effective_workspace(self._session, self._settings)
            root.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            name = sanitize_filename(f"image-{record.id}-{stamp}.png")
            target = resolve_within(root, name)
            target.write_bytes(image_bytes)
        except Exception as exc:  # noqa: BLE001
            return self._fail(record, f"Could not save the image: {exc}")

        record.status = "success"
        record.output_path = str(target)
        record.updated_at = datetime.now()
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        logger.info("image generated: id=%s -> %s", record.id, target)
        return record

    def _fail(self, record: ImageGeneration, message: str) -> ImageGeneration:
        record.status = "error"
        record.error = message
        record.updated_at = datetime.now()
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        logger.info("image generation failed: id=%s msg=%s", record.id, message)
        return record
