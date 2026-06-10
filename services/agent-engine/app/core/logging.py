"""Logging configuration + an in-memory log store for the desktop Logs page.

Logs go to stdout, a local file (``<data_dir>/logs/agent-engine.log``), and a
bounded in-memory ring buffer the API can read. We only ever log statuses, ids,
names, and counts — never chat messages, document contents, or secrets
(see docs/SECURITY.md).
"""

from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Optional

from .config import Settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

# Map an "evano.agent_engine.<suffix>" logger to a friendly area for the UI.
_AREA_BY_SUFFIX = {
    "ollama": "Ollama",
    "models": "Models",
    "agents": "Agents",
    "documents": "Documents",
    "knowledge": "Knowledge",
    "images": "Images",
    "routines": "Routines",
    "errors": "Errors",
    "tools": "Tools",
}


def area_for(logger_name: str) -> str:
    if logger_name.startswith("evano.agent_engine"):
        suffix = logger_name.rsplit(".", 1)[-1]
        return _AREA_BY_SUFFIX.get(suffix, "System")
    if logger_name.startswith("uvicorn") or logger_name.startswith("httpx"):
        return "Backend"
    return "Other"


class LogRecordStore:
    """Thread-safe ring buffer of recent structured log entries."""

    def __init__(self, capacity: int = 500) -> None:
        self._buffer: deque[dict[str, Any]] = deque(maxlen=capacity)
        self._lock = Lock()

    def add(self, entry: dict[str, Any]) -> None:
        with self._lock:
            self._buffer.append(entry)

    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()

    def recent(
        self,
        limit: int = 200,
        level: Optional[str] = None,
        area: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        with self._lock:
            items = list(self._buffer)
        if level:
            threshold = logging.getLevelName(level.upper())
            if isinstance(threshold, int):
                items = [e for e in items if e["levelno"] >= threshold]
        if area:
            items = [e for e in items if e["area"].lower() == area.lower()]
        return items[-limit:]


# Process-wide store read by GET /logs and the support bundle.
log_store = LogRecordStore()


class _RingBufferHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_store.add(
                {
                    "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                    "level": record.levelname,
                    "levelno": record.levelno,
                    "area": area_for(record.name),
                    "logger": record.name,
                    "message": record.getMessage(),
                }
            )
        except Exception:  # noqa: BLE001 - logging must never raise
            pass


def configure_logging(settings: Settings) -> None:
    """Configure root logging. Idempotent across create_app() calls."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Remove handlers we previously added, so repeated setup doesn't stack.
    for handler in list(root.handlers):
        if getattr(handler, "_evano", False):
            root.removeHandler(handler)
            try:
                handler.close()
            except Exception:  # noqa: BLE001
                pass
    log_store.clear()

    formatter = logging.Formatter(_LOG_FORMAT)

    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    stream._evano = True  # type: ignore[attr-defined]
    root.addHandler(stream)

    try:
        logs_dir = settings.data_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(logs_dir / "agent-engine.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler._evano = True  # type: ignore[attr-defined]
        root.addHandler(file_handler)
    except Exception:  # noqa: BLE001 - file logging is best-effort
        pass

    ring = _RingBufferHandler()
    ring._evano = True  # type: ignore[attr-defined]
    root.addHandler(ring)

    # Keep noisy third-party loggers at WARNING.
    logging.getLogger("httpx").setLevel(logging.WARNING)
