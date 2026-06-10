"""Support bundle builder.

Collects non-sensitive diagnostics into a single JSON file the user can share.
Privacy: NEVER includes chat messages, document contents, routine prompts, or
secrets — only statuses, names, counts, and our (already non-private) logs.
Nothing is uploaded; the file is written locally.
"""

from __future__ import annotations

import json
import platform
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.config import Settings
from ..core.logging import log_store
from .chroma_service import ChromaService
from .database_service import DatabaseService
from .image_service import ImageService
from .knowledge_service import KnowledgeService
from .ollama_service import OllamaService
from .routine_service import RoutineService


def _safe(label: str, fn) -> Any:
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Could not collect {label}: {exc}"}


def build_support_bundle(session, settings: Settings) -> dict[str, Any]:
    def database() -> Any:
        return DatabaseService(session, settings).status().model_dump(mode="json")

    def ollama() -> Any:
        service = OllamaService(settings)
        status = service.get_status().model_dump(mode="json")
        models = service.list_models()
        # Only model NAMES — never any content.
        status["installed_models"] = [m.name for m in models.models]
        return status

    def chroma() -> Any:
        knowledge = KnowledgeService(session, settings, ChromaService(settings))
        return knowledge.status().model_dump(mode="json")

    def comfyui() -> Any:
        return ImageService(session, settings).status().model_dump(mode="json")

    def routines() -> Any:
        items = RoutineService(session, settings).list_routines()
        by_status = Counter(r.status for r in items)
        # Names + schedule + status only — NO prompts (user content).
        summary = [
            {
                "name": r.name,
                "schedule_type": r.schedule_type,
                "status": r.status,
                "last_run_at": r.last_run_at.isoformat() if r.last_run_at else None,
                "next_run_at": r.next_run_at.isoformat() if r.next_run_at else None,
            }
            for r in items
        ]
        return {"total": len(items), "by_status": dict(by_status), "routines": summary}

    return {
        "generated_at": datetime.now().isoformat(),
        "app": {
            "name": settings.app_name,
            "version": settings.version,
            "environment": settings.environment,
        },
        "os": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "machine": platform.machine(),
        },
        "backend": {"reachable": True},
        "database": _safe("database status", database),
        "ollama": _safe("Ollama status", ollama),
        "chromadb": _safe("ChromaDB status", chroma),
        "comfyui": _safe("ComfyUI status", comfyui),
        "routines": _safe("routine summary", routines),
        "recent_logs": log_store.recent(limit=200),
        "privacy_note": (
            "This bundle excludes chat messages, document contents, routine prompts, "
            "and secrets by default. It is local only and is not uploaded anywhere."
        ),
    }


def write_support_bundle(settings: Settings, bundle: dict[str, Any]) -> Path:
    logs_dir = settings.data_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = logs_dir / f"support-bundle-{stamp}.json"
    path.write_text(json.dumps(bundle, indent=2, default=str), encoding="utf-8")
    return path
