"""Ollama HTTP client: status, models, chat (+ native tool calling), pulls."""
from __future__ import annotations

import logging
import time

import httpx

from ...core.config import Settings
from ...schemas.ollama import (
    ChatTestResponse,
    OllamaModel,
    OllamaModelsResponse,
    OllamaStatusResponse,
    PullStatusResponse,
    RecommendedModel,
    RecommendedModelsResponse,
)
from ._offline import _OFFLINE_EXCEPTIONS
from .catalog import RECOMMENDED_MODELS
from .pull import _pull_manager
from .turn import AgenticTurn

logger = logging.getLogger("evano.agent_engine.ollama")

class OllamaService:
    """Reads status/models from a local Ollama and runs a one-shot chat test."""

    def __init__(self, settings: Settings) -> None:
        self._base = settings.ollama_base_url.rstrip("/")
        self._timeout = settings.ollama_timeout_seconds
        self._chat_timeout = settings.ollama_chat_timeout_seconds
        self._recommended = settings.ollama_recommended_model

    # ---- helpers --------------------------------------------------------- #

    def _offline_message(self) -> str:
        return (
            f"Ollama is not reachable at {self._base}. "
            "Make sure Ollama is installed and running."
        )

    @staticmethod
    def _parse_models(payload: dict) -> list[OllamaModel]:
        result: list[OllamaModel] = []
        for entry in payload.get("models") or []:
            details = entry.get("details") or {}
            result.append(
                OllamaModel(
                    name=entry.get("name") or entry.get("model") or "unknown",
                    size_bytes=entry.get("size"),
                    modified_at=entry.get("modified_at"),
                    family=details.get("family"),
                    parameter_size=details.get("parameter_size"),
                    digest=entry.get("digest"),
                )
            )
        return result

    def _matches_recommended(self, model_name: str) -> bool:
        rec = self._recommended.lower()
        name = model_name.lower()
        return name == rec or name.split(":")[0] == rec

    def _recommended_available(self, models: list[OllamaModel]) -> bool:
        return any(self._matches_recommended(m.name) for m in models)

    def _installed_recommended_name(self, models: list[OllamaModel]) -> str | None:
        for model in models:
            if self._matches_recommended(model.name):
                return model.name
        return None

    # ---- public API ------------------------------------------------------ #

    def get_status(self) -> OllamaStatusResponse:
        try:
            with httpx.Client(timeout=self._timeout) as client:
                version_resp = client.get(f"{self._base}/api/version")
                version_resp.raise_for_status()
                version = version_resp.json().get("version")

                tags_resp = client.get(f"{self._base}/api/tags")
                tags_resp.raise_for_status()
                models = self._parse_models(tags_resp.json())

            return OllamaStatusResponse(
                status="running",
                reachable=True,
                base_url=self._base,
                version=version,
                model_count=len(models),
                recommended_model=self._recommended,
                recommended_available=self._recommended_available(models),
                message=None,
            )
        except _OFFLINE_EXCEPTIONS:
            return OllamaStatusResponse(
                status="offline",
                reachable=False,
                base_url=self._base,
                recommended_model=self._recommended,
                message=self._offline_message(),
            )
        except Exception as exc:  # noqa: BLE001 - report, don't crash
            logger.warning("Ollama status error: %s", exc)
            return OllamaStatusResponse(
                status="error",
                reachable=False,
                base_url=self._base,
                recommended_model=self._recommended,
                message=f"Unexpected error talking to Ollama: {exc}",
            )

    def list_models(self) -> OllamaModelsResponse:
        try:
            with httpx.Client(timeout=self._timeout) as client:
                tags_resp = client.get(f"{self._base}/api/tags")
                tags_resp.raise_for_status()
                models = self._parse_models(tags_resp.json())

            return OllamaModelsResponse(
                reachable=True,
                models=models,
                count=len(models),
                recommended_model=self._recommended,
                recommended_available=self._recommended_available(models),
                message=None if models else "No models installed yet.",
            )
        except _OFFLINE_EXCEPTIONS:
            return OllamaModelsResponse(
                reachable=False,
                recommended_model=self._recommended,
                message=self._offline_message(),
            )
        except Exception as exc:  # noqa: BLE001
            return OllamaModelsResponse(
                reachable=False,
                recommended_model=self._recommended,
                message=f"Unexpected error talking to Ollama: {exc}",
            )

    def chat_test(self, model: str | None, prompt: str) -> ChatTestResponse:
        # First make sure Ollama is reachable and choose a model to use.
        try:
            with httpx.Client(timeout=self._timeout) as client:
                tags_resp = client.get(f"{self._base}/api/tags")
                tags_resp.raise_for_status()
                models = self._parse_models(tags_resp.json())
        except _OFFLINE_EXCEPTIONS:
            return ChatTestResponse(ok=False, model=model, message=self._offline_message())
        except Exception as exc:  # noqa: BLE001
            return ChatTestResponse(
                ok=False, model=model, message=f"Unexpected error talking to Ollama: {exc}"
            )

        chosen = (
            model
            or self._installed_recommended_name(models)
            or (models[0].name if models else None)
        )
        if not chosen:
            return ChatTestResponse(
                ok=False,
                model=None,
                message=(
                    "No model available. Install a model in Ollama "
                    f"(e.g. the recommended '{self._recommended}') and try again."
                ),
            )

        return self.chat(chosen, [{"role": "user", "content": prompt}])

    def chat(
        self,
        model: str,
        messages: list[dict],
        temperature: float | None = None,
    ) -> ChatTestResponse:
        """Send a non-streaming chat request to Ollama for ``model``.

        ``messages`` is a list of {"role", "content"} dicts (may include a
        leading system message). Returns ok=False with a message on any failure.
        """
        payload: dict = {"model": model, "messages": messages, "stream": False}
        if temperature is not None:
            payload["options"] = {"temperature": temperature}
        try:
            start = time.monotonic()
            with httpx.Client(timeout=self._chat_timeout) as client:
                resp = client.post(f"{self._base}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
            latency_ms = int((time.monotonic() - start) * 1000)
            reply = (data.get("message") or {}).get("content")
            return ChatTestResponse(
                ok=True, model=model, reply=reply, latency_ms=latency_ms, message=None
            )
        except _OFFLINE_EXCEPTIONS:
            return ChatTestResponse(ok=False, model=model, message=self._offline_message())
        except httpx.HTTPStatusError as exc:
            return ChatTestResponse(
                ok=False,
                model=model,
                message=(
                    f"Ollama returned HTTP {exc.response.status_code} for model "
                    f"'{model}'. Is the model installed?"
                ),
            )
        except Exception as exc:  # noqa: BLE001
            return ChatTestResponse(
                ok=False, model=model, message=f"Unexpected error during chat: {exc}"
            )

    def chat_agentic(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float | None = None,
    ) -> AgenticTurn:
        """Non-streaming chat that supports native tool calling.

        Returns ``supports_tools=False`` (without raising) when the model can't
        do tool calling, so the caller can fall back to the deterministic router.
        """
        payload: dict = {"model": model, "messages": messages, "stream": False}
        if tools:
            payload["tools"] = tools
        if temperature is not None:
            payload["options"] = {"temperature": temperature}
        try:
            start = time.monotonic()
            with httpx.Client(timeout=self._chat_timeout) as client:
                resp = client.post(f"{self._base}/api/chat", json=payload)
            latency_ms = int((time.monotonic() - start) * 1000)

            if resp.status_code >= 400:
                err = ""
                try:
                    err = str(resp.json().get("error", ""))
                except Exception:  # noqa: BLE001
                    err = resp.text
                if "does not support tools" in err.lower():
                    return AgenticTurn(ok=False, supports_tools=False, message=err)
                return AgenticTurn(
                    ok=False,
                    message=f"Ollama returned HTTP {resp.status_code} for '{model}'. {err}".strip(),
                )

            data = resp.json()
            msg = data.get("message") or {}
            calls: list[dict] = []
            for tc in msg.get("tool_calls") or []:
                fn = tc.get("function") or {}
                calls.append({"name": fn.get("name"), "arguments": fn.get("arguments") or {}})
            return AgenticTurn(
                ok=True,
                content=msg.get("content") or "",
                tool_calls=calls,
                raw_message=msg,
                latency_ms=latency_ms,
            )
        except _OFFLINE_EXCEPTIONS:
            return AgenticTurn(ok=False, message=self._offline_message())
        except Exception as exc:  # noqa: BLE001
            return AgenticTurn(ok=False, message=f"Unexpected error during chat: {exc}")

    # ---- model management ------------------------------------------------ #

    def get_recommended(self) -> RecommendedModelsResponse:
        """Return curated recommendations with an ``installed`` flag for each."""
        installed_names: list[str] = []
        reachable = False
        message: str | None = None
        try:
            with httpx.Client(timeout=self._timeout) as client:
                tags_resp = client.get(f"{self._base}/api/tags")
                tags_resp.raise_for_status()
                installed_names = [m.name for m in self._parse_models(tags_resp.json())]
            reachable = True
        except _OFFLINE_EXCEPTIONS:
            message = self._offline_message()
        except Exception as exc:  # noqa: BLE001
            message = f"Unexpected error talking to Ollama: {exc}"

        def is_installed(tag: str) -> bool:
            base = tag.lower().split(":")[0]
            for name in installed_names:
                lname = name.lower()
                if lname == tag.lower() or lname.split(":")[0] == base:
                    return True
            return False

        models = [
            RecommendedModel(**entry, installed=reachable and is_installed(entry["model"]))
            for entry in RECOMMENDED_MODELS
        ]
        return RecommendedModelsResponse(
            reachable=reachable,
            recommended_model=self._recommended,
            models=models,
            message=message,
        )

    def start_pull(self, model: str) -> PullStatusResponse:
        """Begin installing a model in the background. Does not block."""
        return _pull_manager.start(self._base, model, connect_timeout=self._timeout)

    def get_pull_status(self, model: str) -> PullStatusResponse:
        """Return the latest progress for a model pull (idle if untracked)."""
        return _pull_manager.get(model)
