"""Local, free embedding functions for ChromaDB.

Three options, all local — never a paid/cloud embedding API:

- "default": Chroma's built-in MiniLM (all-MiniLM-L6-v2) via onnxruntime. Free and
  local; downloads a ~80MB model file the first time it is used.
- "ollama": uses a local Ollama embedding model (e.g. ``nomic-embed-text``).
  Requires that model to be pulled in Ollama.
- "hash": pure-python deterministic embeddings (no downloads, lower quality).
  A zero-setup fallback and what the tests use.
"""

from __future__ import annotations

import hashlib

import httpx

# ChromaDB provides the EmbeddingFunction base class. It's optional: in packaged
# "lite" builds chromadb isn't bundled, so we fall back to a stub base and the
# knowledge base simply reports unavailable. When chromadb IS installed (normal
# dev/server runs) the real base is used — behavior is unchanged.
try:
    from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

    _CHROMA_AVAILABLE = True
except Exception:  # noqa: BLE001 - chromadb not bundled
    _CHROMA_AVAILABLE = False
    Documents = list  # type: ignore[assignment,misc]
    Embeddings = list  # type: ignore[assignment,misc]

    class EmbeddingFunction:  # type: ignore[no-redef]
        """Stub base used only when chromadb isn't installed (KB unavailable)."""

from ..core.config import Settings


class HashEmbeddingFunction(EmbeddingFunction):
    """Deterministic bag-of-words hashing embedder (stable across processes)."""

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def __call__(self, input: Documents) -> Embeddings:
        vectors: Embeddings = []
        for text in input:
            vector = [0.0] * self.dim
            for token in str(text).lower().split():
                digest = hashlib.md5(token.encode("utf-8")).hexdigest()
                vector[int(digest, 16) % self.dim] += 1.0
            vectors.append(vector)
        return vectors

    @staticmethod
    def name() -> str:
        return "evano-hash"

    def get_config(self) -> dict:
        return {"dim": self.dim}

    @staticmethod
    def build_from_config(config: dict) -> "HashEmbeddingFunction":
        return HashEmbeddingFunction(dim=config.get("dim", 256))


class OllamaEmbeddingFunction(EmbeddingFunction):
    """Embeddings via a local Ollama model's /api/embeddings endpoint."""

    def __init__(self, base_url: str, model: str, timeout: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def __call__(self, input: Documents) -> Embeddings:
        vectors: Embeddings = []
        with httpx.Client(timeout=self.timeout) as client:
            for text in input:
                resp = client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": str(text)},
                )
                resp.raise_for_status()
                vectors.append(resp.json()["embedding"])
        return vectors

    @staticmethod
    def name() -> str:
        return "evano-ollama"

    def get_config(self) -> dict:
        return {"base_url": self.base_url, "model": self.model, "timeout": self.timeout}

    @staticmethod
    def build_from_config(config: dict) -> "OllamaEmbeddingFunction":
        return OllamaEmbeddingFunction(
            base_url=config["base_url"], model=config["model"], timeout=config.get("timeout", 30.0)
        )


def build_embedding_function(settings: Settings) -> EmbeddingFunction:
    """Construct the configured embedding function."""
    provider = settings.embedding_provider.lower()
    if provider == "hash":
        return HashEmbeddingFunction()
    if provider == "ollama":
        return OllamaEmbeddingFunction(
            base_url=settings.ollama_base_url,
            model=settings.embedding_model,
            timeout=settings.ollama_chat_timeout_seconds,
        )
    # Default: Chroma's local MiniLM (downloads once, runs via onnxruntime).
    from chromadb.utils import embedding_functions

    return embedding_functions.DefaultEmbeddingFunction()


def embedding_label(settings: Settings) -> str:
    provider = settings.embedding_provider.lower()
    if provider == "ollama":
        return f"ollama:{settings.embedding_model}"
    if provider == "hash":
        return "hash (fallback)"
    return "default (all-MiniLM-L6-v2, local)"
