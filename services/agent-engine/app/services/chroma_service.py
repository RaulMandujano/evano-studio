"""ChromaDB service — local persistent vector store (never Chroma Cloud).

ChromaDB and the embedding function are imported lazily so the rest of the
backend keeps working (and reports a clear local-setup error) if ChromaDB isn't
installed. Collections are cached per process so the embedding model loads once.
"""

from __future__ import annotations

from typing import Any

from ..core.config import Settings
from ..core.errors import AppError

# Cache collections by (path, collection, provider, model) so we don't rebuild
# the client / reload the embedding model on every request.
_COLLECTIONS: dict[tuple, Any] = {}


def _collection_for(settings: Settings) -> Any:
    key = (
        str(settings.chroma_path),
        settings.chroma_collection,
        settings.embedding_provider,
        settings.embedding_model,
    )
    if key in _COLLECTIONS:
        return _COLLECTIONS[key]

    try:
        import chromadb
    except ImportError as exc:  # pragma: no cover - depends on env
        raise AppError(
            "ChromaDB is not installed. Install it locally with: pip install chromadb",
            status_code=503,
            code="chromadb_unavailable",
        ) from exc

    from .embeddings import build_embedding_function

    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(settings.chroma_path))
    embedding_function = build_embedding_function(settings)
    collection = client.get_or_create_collection(
        settings.chroma_collection, embedding_function=embedding_function
    )
    _COLLECTIONS[key] = collection
    return collection


class ChromaService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def availability(self) -> tuple[bool, str | None]:
        """Return (available, message). Never raises; never touches the cloud."""
        try:
            _collection_for(self._settings)
            return True, None
        except AppError as exc:
            return False, exc.message
        except Exception as exc:  # noqa: BLE001
            return False, f"ChromaDB could not be initialized locally: {exc}"

    def count(self) -> int:
        return _collection_for(self._settings).count()

    def add_chunks(
        self,
        document_id: int,
        chunks: list[str],
        *,
        title: str,
        file_name: str,
    ) -> None:
        if not chunks:
            return
        collection = _collection_for(self._settings)
        ids = [f"doc{document_id}-chunk{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": document_id,
                "chunk_index": i,
                "title": title,
                "file_name": file_name,
            }
            for i in range(len(chunks))
        ]
        collection.add(ids=ids, documents=chunks, metadatas=metadatas)

    def search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        collection = _collection_for(self._settings)
        result = collection.query(query_texts=[query], n_results=top_k)
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        hits: list[dict[str, Any]] = []
        for text, meta, distance in zip(documents, metadatas, distances):
            meta = meta or {}
            hits.append(
                {
                    "text": text,
                    "document_id": meta.get("document_id"),
                    "chunk_index": meta.get("chunk_index"),
                    "title": meta.get("title"),
                    "file_name": meta.get("file_name"),
                    "distance": float(distance) if distance is not None else None,
                }
            )
        return hits

    def delete_document(self, document_id: int) -> None:
        collection = _collection_for(self._settings)
        collection.delete(where={"document_id": document_id})

    def get_document_text(self, document_id: int) -> str:
        """Reassemble a document's full text from its stored chunks, in order."""
        collection = _collection_for(self._settings)
        result = collection.get(where={"document_id": document_id})
        documents = result.get("documents") or []
        metadatas = result.get("metadatas") or []
        ordered = sorted(
            zip(documents, metadatas),
            key=lambda pair: (pair[1] or {}).get("chunk_index", 0),
        )
        return "\n".join(text for text, _ in ordered)
