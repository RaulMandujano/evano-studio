"""Schemas for the document endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

DocumentType = Literal["md", "txt", "html"]


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = ""
    file_type: DocumentType = "md"
    # Optional explicit file name; otherwise derived from the title. It is always
    # sanitized server-side and confined to the workspace.
    file_name: Optional[str] = None
    overwrite: bool = False
    created_by_agent_id: Optional[int] = None


class AgentResponseToDocument(BaseModel):
    """Save an agent's chat response as a document."""

    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    agent_id: Optional[int] = None
    file_type: DocumentType = "md"
    file_name: Optional[str] = None
    overwrite: bool = False


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    file_name: str
    file_type: str
    file_path: str
    created_by_agent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    size_bytes: Optional[int] = None
    exists: bool = True


class DocumentDetail(DocumentRead):
    content: str


class DeleteResponse(BaseModel):
    ok: bool