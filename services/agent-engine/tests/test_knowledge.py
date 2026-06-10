"""Tests for the local knowledge base (RAG).

Uses the pure-python "hash" embedding provider so tests are fully offline and
don't download any model.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(
        data_dir=tmp_path,
        environment="test",
        embedding_provider="hash",
        chunk_size=200,
        chunk_overlap=40,
        ollama_base_url="http://127.0.0.1:9",  # offline → deterministic chat
        ollama_timeout_seconds=0.5,
        ollama_chat_timeout_seconds=0.5,
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def _import(client: TestClient, title: str, content: str) -> dict:
    response = client.post(
        "/knowledge/documents/import",
        json={"title": title, "file_name": f"{title}.txt", "content": content},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_status_available(client: TestClient) -> None:
    body = client.get("/knowledge/status").json()
    assert body["available"] is True
    assert body["engine"].startswith("chromadb")
    assert body["collection"] == "evano_knowledge"
    assert body["embedding"].startswith("hash")


def test_import_list_get_delete(client: TestClient) -> None:
    doc = _import(
        client,
        "Handbook",
        "The return policy is 30 days. " * 30,  # long enough to chunk
    )
    assert doc["chunk_count"] >= 2
    assert doc["collection_name"] == "evano_knowledge"

    assert len(client.get("/knowledge/documents").json()) == 1
    assert client.get(f"/knowledge/documents/{doc['id']}").json()["title"] == "Handbook"

    status = client.get("/knowledge/status").json()
    assert status["document_count"] == 1
    assert status["chunk_count"] >= 2

    assert client.delete(f"/knowledge/documents/{doc['id']}").json() == {"ok": True}
    assert client.get("/knowledge/documents").json() == []
    assert client.get("/knowledge/status").json()["chunk_count"] == 0


def test_search_returns_relevant_chunk(client: TestClient) -> None:
    _import(client, "Pets", "Cats are independent animals that like to nap in the sun.")
    _import(client, "Tech", "ChromaDB is a local vector database for retrieval augmented generation.")

    body = client.post("/knowledge/search", json={"query": "vector database rag", "top_k": 1}).json()
    assert body["ok"] is True
    assert len(body["results"]) == 1
    assert body["results"][0]["title"] == "Tech"


def test_empty_document_rejected(client: TestClient) -> None:
    # Whitespace-only content passes min_length but has no usable text → 400.
    response = client.post(
        "/knowledge/documents/import",
        json={"title": "Empty", "file_name": "empty.txt", "content": "   "},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "empty_document"

    # Truly empty content fails schema validation → 422.
    invalid = client.post(
        "/knowledge/documents/import",
        json={"title": "Empty", "file_name": "empty.txt", "content": ""},
    )
    assert invalid.status_code == 422


def test_agent_rag_attaches_sources(client: TestClient) -> None:
    _import(client, "Warranty", "The warranty lasts 12 months from the purchase date.")
    agent = client.post(
        "/agents",
        json={"name": "KB Bot", "model_name": "any:tag", "knowledge_enabled": True},
    ).json()

    reply = client.post(
        f"/agents/{agent['id']}/chat",
        json={"message": "how long is the warranty"},
    ).json()

    # Ollama is offline (ok=False), but RAG context is gathered before the call,
    # so grounding sources are attached to the response.
    assert reply["ok"] is False
    assert reply["sources"] is not None
    assert len(reply["sources"]) >= 1
    assert reply["sources"][0]["snippet"]
