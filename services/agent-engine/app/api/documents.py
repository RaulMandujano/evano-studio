"""Document CRUD endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, status

from ..core.errors import AppError
from ..db.models import Document
from ..schemas.document import (
    AgentResponseToDocument,
    DeleteResponse,
    DocumentCreate,
    DocumentDetail,
    DocumentRead,
)
from ..services.document_service import DocumentService
from .deps import get_document_service

router = APIRouter(prefix="/documents", tags=["documents"])


def _to_read(document: Document) -> DocumentRead:
    path = Path(document.file_path)
    exists = path.exists()
    size = path.stat().st_size if exists else None
    return DocumentRead(
        id=document.id,  # type: ignore[arg-type]
        title=document.title,
        file_name=document.file_name,
        file_type=document.file_type,
        file_path=document.file_path,
        created_by_agent_id=document.created_by_agent_id,
        created_at=document.created_at,
        updated_at=document.updated_at,
        size_bytes=size,
        exists=exists,
    )


def _get_or_404(service: DocumentService, document_id: int) -> Document:
    document = service.get_document(document_id)
    if document is None:
        raise AppError("Document not found.", status_code=status.HTTP_404_NOT_FOUND, code="not_found")
    return document


@router.get("", response_model=list[DocumentRead], summary="List documents")
def list_documents(service: DocumentService = Depends(get_document_service)) -> list[DocumentRead]:
    return [_to_read(d) for d in service.list_documents()]


@router.post(
    "",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a document",
)
def create_document(
    payload: DocumentCreate,
    service: DocumentService = Depends(get_document_service),
) -> DocumentRead:
    return _to_read(service.create_document(payload))


@router.get("/{document_id}", response_model=DocumentDetail, summary="Read a document")
def get_document(
    document_id: int,
    service: DocumentService = Depends(get_document_service),
) -> DocumentDetail:
    document = _get_or_404(service, document_id)
    content = service.read_content(document)
    base = _to_read(document)
    return DocumentDetail(**base.model_dump(), content=content)


@router.delete("/{document_id}", response_model=DeleteResponse, summary="Delete a document")
def delete_document(
    document_id: int,
    service: DocumentService = Depends(get_document_service),
) -> DeleteResponse:
    if not service.delete_document(document_id):
        raise AppError("Document not found.", status_code=status.HTTP_404_NOT_FOUND, code="not_found")
    return DeleteResponse(ok=True)


@router.post(
    "/from-agent-response",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Save an agent response as a document",
)
def create_from_agent_response(
    payload: AgentResponseToDocument,
    service: DocumentService = Depends(get_document_service),
) -> DocumentRead:
    data = DocumentCreate(
        title=payload.title,
        content=payload.content,
        file_type=payload.file_type,
        file_name=payload.file_name,
        overwrite=payload.overwrite,
        created_by_agent_id=payload.agent_id,
    )
    return _to_read(service.create_document(data))
