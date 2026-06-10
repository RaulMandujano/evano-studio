"""Background model pulls (streams NDJSON progress from Ollama /api/pull)."""
from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime

import httpx

from ...schemas.ollama import PullStatusResponse
from ...utils.time import utc_now
from ._offline import _OFFLINE_EXCEPTIONS

models_logger = logging.getLogger("evano.agent_engine.models")

@dataclass
class _PullProgress:
    """Internal, mutable progress record for a model pull."""

    model: str
    state: str = "pending"
    percent: float = 0.0
    completed_bytes: int = 0
    total_bytes: int = 0
    detail: str | None = None
    message: str | None = None
    updated_at: datetime = field(default_factory=utc_now)

    def to_schema(self) -> PullStatusResponse:
        return PullStatusResponse(
            model=self.model,
            state=self.state,  # type: ignore[arg-type]
            percent=self.percent,
            completed_bytes=self.completed_bytes,
            total_bytes=self.total_bytes,
            detail=self.detail,
            message=self.message,
            updated_at=self.updated_at,
        )


class OllamaPullManager:
    """Process-wide registry that runs model pulls in background threads.

    All pull logic lives here. Pulls stream NDJSON progress from Ollama's
    ``/api/pull`` and update an in-memory record that the API polls. Threads are
    daemonic, so they don't block shutdown.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pulls: dict[str, _PullProgress] = {}

    def get(self, model: str) -> PullStatusResponse:
        with self._lock:
            progress = self._pulls.get(model)
            if progress is None:
                return PullStatusResponse(model=model, state="idle")
            return progress.to_schema()

    def start(self, base_url: str, model: str, connect_timeout: float) -> PullStatusResponse:
        with self._lock:
            existing = self._pulls.get(model)
            if existing is not None and existing.state in ("pending", "downloading"):
                return existing.to_schema()
            progress = _PullProgress(model=model, state="pending", detail="starting")
            self._pulls[model] = progress

        thread = threading.Thread(
            target=self._run, args=(base_url, model, connect_timeout), daemon=True
        )
        thread.start()
        models_logger.info("model pull started: %s", model)
        return self.get(model)

    def _update(self, model: str, **changes: object) -> None:
        with self._lock:
            progress = self._pulls.get(model)
            if progress is None:
                return
            for key, value in changes.items():
                setattr(progress, key, value)
            progress.updated_at = utc_now()

    def _run(self, base_url: str, model: str, connect_timeout: float) -> None:
        # Long downloads: allow a generous read timeout but fail fast on connect.
        timeout = httpx.Timeout(connect=connect_timeout, read=60.0, write=60.0, pool=None)
        try:
            with httpx.Client(timeout=timeout) as client:
                with client.stream(
                    "POST", f"{base_url}/api/pull", json={"model": model, "stream": True}
                ) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line:
                            continue
                        self._handle_line(model, line)
            # If the stream ended without an explicit error, consider it done.
            with self._lock:
                progress = self._pulls.get(model)
                if progress and progress.state not in ("error", "success"):
                    progress.state = "success"
                    progress.percent = 100.0
                    progress.detail = "success"
                    progress.updated_at = utc_now()
            models_logger.info("model pull finished: %s", model)
        except _OFFLINE_EXCEPTIONS:
            self._update(
                model,
                state="error",
                message=f"Ollama is not reachable at {base_url}. Is it running?",
            )
            models_logger.warning("model pull failed (Ollama unreachable): %s", model)
        except httpx.HTTPStatusError as exc:
            self._update(
                model,
                state="error",
                message=f"Ollama returned HTTP {exc.response.status_code} for '{model}'.",
            )
            models_logger.warning(
                "model pull failed: %s (HTTP %s)", model, exc.response.status_code
            )
        except Exception as exc:  # noqa: BLE001 - record, don't crash the thread
            self._update(model, state="error", message=f"Pull failed: {exc}")
            models_logger.warning("model pull failed: %s (%s)", model, exc)

    def _handle_line(self, model: str, line: str) -> None:
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            return

        if "error" in data:
            self._update(model, state="error", message=str(data["error"]))
            return

        status_text = data.get("status")
        total = data.get("total")
        completed = data.get("completed")
        changes: dict[str, object] = {"state": "downloading"}
        if status_text:
            changes["detail"] = status_text
        if isinstance(total, int) and total > 0:
            changes["total_bytes"] = total
            if isinstance(completed, int):
                changes["completed_bytes"] = completed
                changes["percent"] = round(completed / total * 100, 1)
        if status_text == "success":
            changes["state"] = "success"
            changes["percent"] = 100.0
        self._update(model, **changes)


# Process-wide singleton (the backend is a single local process).
_pull_manager = OllamaPullManager()
