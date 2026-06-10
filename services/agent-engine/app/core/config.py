"""Application configuration.

Settings are loaded from environment variables (prefixed ``EVANO_``) and an
optional ``.env`` file. Every setting has a safe, local default — no secrets are
required to run the backend.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings, driven by the environment."""

    model_config = SettingsConfigDict(
        env_prefix="EVANO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Identity
    app_name: str = "Evano Studio Agent Engine"
    version: str = "0.1.0"
    environment: str = "development"

    # Network — local only by design. Never bind to a public interface.
    host: str = "127.0.0.1"
    port: int = 8765

    # Logging
    log_level: str = "INFO"

    # CORS — restricted to localhost / 127.0.0.1 on any port so that only the
    # local Evano Studio desktop app can talk to this backend.
    cors_allow_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    # Local app data directory (configurable). The SQLite database lives under
    # ``<data_dir>/sqlite/evano.db`` unless ``database_url`` is set explicitly.
    # Defaults to a per-user folder so it never depends on the current directory.
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".evano-studio")

    # Optional explicit database URL. When set, it overrides the computed SQLite
    # path (e.g. "sqlite://" for an in-memory DB in tests).
    database_url: str | None = None

    # Ollama (local AI runtime). Local by default; never assume it is installed
    # or that any model is present. Timeouts keep the backend responsive when
    # Ollama is missing or slow.
    ollama_base_url: str = "http://localhost:11434"
    ollama_recommended_model: str = "gemma4"
    ollama_timeout_seconds: float = 4.0
    ollama_chat_timeout_seconds: float = 30.0

    # Knowledge base / RAG (ChromaDB local only — never Chroma Cloud).
    chroma_collection: str = "evano_knowledge"
    # Embedding provider: "default" (local MiniLM via onnxruntime, free, downloads
    # a ~80MB model once), "ollama" (uses a local Ollama embedding model), or
    # "hash" (pure-python, zero-download fallback; lower quality).
    embedding_provider: str = "default"
    embedding_model: str = "nomic-embed-text"  # used when provider == "ollama"
    # Chunking + retrieval.
    chunk_size: int = 1000
    chunk_overlap: int = 150
    rag_top_k: int = 4
    rag_max_context_chars: int = 4000

    # ComfyUI (optional, external local service for image generation). Disabled
    # by default; the rest of Evano Studio works without it. Configurable at
    # runtime via PUT /comfyui/settings (stored in the DB).
    comfyui_base_url: str = "http://127.0.0.1:8188"
    comfyui_enabled: bool = False
    comfyui_default_workflow_path: str = ""
    comfyui_timeout_seconds: float = 4.0
    comfyui_poll_timeout_seconds: float = 180.0
    comfyui_poll_interval_seconds: float = 1.0

    # Routines (local scheduler). Routines only run while this backend is running.
    routine_scheduler_enabled: bool = True
    routine_tick_seconds: int = 30
    # A scheduled run that's overdue by more than this is recorded as "missed"
    # (e.g. the app was closed) rather than silently executed late.
    routine_grace_seconds: int = 120

    @property
    def is_development(self) -> bool:
        return self.environment.lower() in {"development", "dev", "local"}

    @property
    def workspace_path(self) -> Path:
        """Root for user/agent-generated files. The ONLY writable docs location."""
        return self.data_dir / "workspace"

    @property
    def chroma_path(self) -> Path:
        """Local persistent ChromaDB directory (never cloud)."""
        return self.data_dir / "chroma"

    @property
    def resolved_database_url(self) -> str:
        """The effective SQLAlchemy URL (explicit override or computed SQLite)."""
        if self.database_url:
            return self.database_url
        db_file = self.data_dir / "sqlite" / "evano.db"
        return f"sqlite:///{db_file}"

    @property
    def sqlite_file_path(self) -> Path | None:
        """Filesystem path of the SQLite DB, or None for in-memory/non-file URLs."""
        url = self.resolved_database_url
        prefix = "sqlite:///"
        if url.startswith(prefix) and ":memory:" not in url:
            return Path(url[len(prefix) :])
        return None


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (read once per process)."""
    return Settings()
