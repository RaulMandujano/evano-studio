"""Schemas for the knowledge base (RAG) endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

KnowledgeFileType = Literal["txt", "md"]


class KnowledgeStatusResponse(BaseModel):
    available: bool
    engine: str = "chromadb (local persistent)"
    embedding: str
    path: Optional[str] = None
    collection: str
    document_count: int = 0
    chunk_count: int = 0
    message: Optional[str] = None


class KnowledgeDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    file_name: str
    source_path: str
    collection_name: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class KnowledgeImportRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    file_name: str = Field(min_length=1)
    content: str = Field(min_length=1)
    file_type: KnowledgeFileType = "txt"
    source_path: str = ""


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: Optional[int] = Field(default=None, ge=1, le=20)


class SearchResultItem(BaseModel):
    text: str
    document_id: Optional[int] = None
    chunk_index: Optional[int] = None
    title: Optional[str] = None
    file_name: Optional[str] = None
    distance: Optional[float] = None


class KnowledgeSearchResponse(BaseModel):
    ok: bool
    results: list[SearchResultItem] = Field(default_factory=list)
    message: Optional[str] = None


class DeleteResponse(BaseModel):
    ok: bool


class KnowledgeSyncResponse(BaseModel):
    """Result of mirroring the KB into OpenClaw agent memories."""

    ok: bool
    agents_synced: int = 0
    files_written: int = 0
    message: str = ""
