"""ComfyUI adapter — talks to an external, local ComfyUI instance.

This is a thin HTTP adapter. ComfyUI is NOT bundled or copied; we only call its
local API. Generation uses a "workflow" graph in ComfyUI's API JSON format. The
user typically exports their own workflow from ComfyUI ("Save (API Format)")
with two placeholder text values so prompts can be injected:

    %positive_prompt%   and   %negative_prompt%

If no workflow file is configured, a minimal built-in SD1.5 txt2img template is
used (it requires a matching checkpoint to exist in ComfyUI). See the project
docs for the manual workflow configuration steps.
"""

from __future__ import annotations

import copy
import json
import time
import uuid
from pathlib import Path
from typing import Any

import httpx

from ..core.comfyui import ComfyUIConfig
from ..core.config import Settings
from ..core.errors import AppError

_POSITIVE_TOKEN = "%positive_prompt%"
_NEGATIVE_TOKEN = "%negative_prompt%"

_OFFLINE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpx.TimeoutException,
)

# Minimal built-in SD1.5 txt2img workflow (ComfyUI API format). This is a data
# graph, not ComfyUI source. Prompts are injected via the placeholder tokens.
DEFAULT_WORKFLOW: dict[str, Any] = {
    "3": {
        "class_type": "KSampler",
        "inputs": {
            "seed": 0,
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 1.0,
            "model": ["4", 0],
            "positive": ["6", 0],
            "negative": ["7", 0],
            "latent_image": ["5", 0],
        },
    },
    "4": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": "v1-5-pruned-emaonly.safetensors"},
    },
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {"width": 512, "height": 512, "batch_size": 1},
    },
    "6": {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": _POSITIVE_TOKEN, "clip": ["4", 1]},
    },
    "7": {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": _NEGATIVE_TOKEN, "clip": ["4", 1]},
    },
    "8": {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
    },
    "9": {
        "class_type": "SaveImage",
        "inputs": {"filename_prefix": "EvanoStudio", "images": ["8", 0]},
    },
}


def _inject(node: Any, prompt: str, negative: str) -> Any:
    if isinstance(node, dict):
        return {k: _inject(v, prompt, negative) for k, v in node.items()}
    if isinstance(node, list):
        return [_inject(v, prompt, negative) for v in node]
    if node == _POSITIVE_TOKEN:
        return prompt
    if node == _NEGATIVE_TOKEN:
        return negative
    return node


class ComfyUIService:
    """Adapter around a local ComfyUI HTTP API."""

    def __init__(self, config: ComfyUIConfig, settings: Settings) -> None:
        self._config = config
        self._base = config.base_url
        self._timeout = settings.comfyui_timeout_seconds
        self._poll_timeout = settings.comfyui_poll_timeout_seconds
        self._poll_interval = settings.comfyui_poll_interval_seconds

    def status(self) -> tuple[bool, str | None, str | None]:
        """Return (reachable, version, message). Never raises."""
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.get(f"{self._base}/system_stats")
                resp.raise_for_status()
                data = resp.json()
            version = (data.get("system") or {}).get("comfyui_version")
            return True, version, None
        except _OFFLINE_EXCEPTIONS:
            return False, None, f"ComfyUI is not reachable at {self._base}."
        except Exception as exc:  # noqa: BLE001
            return False, None, f"Unexpected error contacting ComfyUI: {exc}"

    def load_workflow(self) -> dict[str, Any]:
        path = self._config.default_workflow_path
        if path:
            file = Path(path).expanduser()
            if not file.exists():
                raise AppError(
                    f"Configured workflow file not found: {path}",
                    status_code=400,
                    code="workflow_missing",
                )
            try:
                return json.loads(file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise AppError(
                    f"Workflow file is not valid JSON: {exc}",
                    status_code=400,
                    code="workflow_invalid",
                ) from exc
        return copy.deepcopy(DEFAULT_WORKFLOW)

    def build_graph(self, prompt: str, negative: str) -> dict[str, Any]:
        return _inject(self.load_workflow(), prompt, negative)

    def generate(self, prompt: str, negative: str) -> tuple[bytes, str]:
        """Submit a prompt, wait for completion, and return (image_bytes, name)."""
        graph = self.build_graph(prompt, negative)
        client_id = uuid.uuid4().hex
        try:
            with httpx.Client(timeout=self._timeout) as client:
                submit = client.post(
                    f"{self._base}/prompt", json={"prompt": graph, "client_id": client_id}
                )
                if submit.status_code >= 400:
                    raise AppError(
                        f"ComfyUI rejected the workflow (HTTP {submit.status_code}). "
                        "Check that the workflow and its model/checkpoint are valid.",
                        status_code=502,
                        code="comfyui_rejected",
                    )
                prompt_id = submit.json().get("prompt_id")
                if not prompt_id:
                    raise AppError("ComfyUI did not return a prompt id.", status_code=502, code="comfyui_error")

                image_ref = self._await_image(client, prompt_id)
                view = client.get(
                    f"{self._base}/view",
                    params={
                        "filename": image_ref["filename"],
                        "subfolder": image_ref.get("subfolder", ""),
                        "type": image_ref.get("type", "output"),
                    },
                )
                view.raise_for_status()
                return view.content, image_ref["filename"]
        except _OFFLINE_EXCEPTIONS as exc:
            raise AppError(
                f"ComfyUI is not reachable at {self._base}.",
                status_code=503,
                code="comfyui_offline",
            ) from exc

    def _await_image(self, client: httpx.Client, prompt_id: str) -> dict[str, Any]:
        deadline = time.monotonic() + self._poll_timeout
        while time.monotonic() < deadline:
            history = client.get(f"{self._base}/history/{prompt_id}")
            history.raise_for_status()
            data = history.json()
            entry = data.get(prompt_id)
            if entry and entry.get("outputs"):
                for node_output in entry["outputs"].values():
                    images = node_output.get("images") or []
                    if images:
                        return images[0]
                raise AppError("ComfyUI finished but produced no image.", status_code=502, code="comfyui_no_image")
            time.sleep(self._poll_interval)
        raise AppError("Timed out waiting for ComfyUI to finish.", status_code=504, code="comfyui_timeout")
