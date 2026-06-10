"""Knowledge base (RAG) endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from ..core.errors import AppError
from ..schemas.knowledge import (
    DeleteResponse,
    KnowledgeDocumentRead,
    KnowledgeImportRequest,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeStatusResponse,
    KnowledgeSyncResponse,
)
from ..services.knowledge_service import KnowledgeService
from .deps import get_knowledge_service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/status", response_model=KnowledgeStatusResponse, summary="Knowledge base status")
def get_status(service: KnowledgeService = Depends(get_knowledge_service)) -> KnowledgeStatusResponse:
    return service.status()


@router.get("/documents", response_model=list[KnowledgeDocumentRead], summary="List KB documents")
def list_documents(
    service: KnowledgeService = Depends(get_knowledge_service),
) -> list[KnowledgeDocumentRead]:
    return [KnowledgeDocumentRead.model_validate(d) for d in service.list_documents()]


@router.post(
    "/sync-agents",
    response_model=KnowledgeSyncResponse,
    summary="Mirror the KB into every OpenClaw agent's memory",
)
def sync_agents(service: KnowledgeService = Depends(get_knowledge_service)) -> KnowledgeSyncResponse:
    """Write each KB document as a memory file in every agent's workspace and
    reindex, so agents keep this knowledge on Discord and in delegated runs.
    Runs automatically after import/delete; this is the manual re-sync."""
    return KnowledgeSyncResponse(**service.sync_to_agents())


@router.post(
    "/documents/import",
    response_model=KnowledgeDocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Import a .txt/.md document into the knowledge base",
)
def import_document(
    payload: KnowledgeImportRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeDocumentRead:
    return KnowledgeDocumentRead.model_validate(service.import_document(payload))


@router.get(
    "/documents/{document_id}",
    response_model=KnowledgeDocumentRead,
    summary="Get a KB document",
)
def get_document(
    document_id: int,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeDocumentRead:
    document = service.get_document(document_id)
    if document is None:
        raise AppError("Document not found.", status_code=status.HTTP_404_NOT_FOUND, code="not_found")
    return KnowledgeDocumentRead.model_validate(document)


@router.delete(
    "/documents/{document_id}",
    response_model=DeleteResponse,
    summary="Delete a KB document and its chunks",
)
def delete_document(
    document_id: int,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> DeleteResponse:
    if not service.delete_document(document_id):
        raise AppError("Document not found.", status_code=status.HTTP_404_NOT_FOUND, code="not_found")
    return DeleteResponse(ok=True)


@router.post("/search", response_model=KnowledgeSearchResponse, summary="Search the knowledge base")
def search(
    payload: KnowledgeSearchRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeSearchResponse:
    available, message = service._chroma.availability()  # type: ignore[attr-defined]
    if not available:
        return KnowledgeSearchResponse(ok=False, results=[], message=message)
    try:
        results = service.search(payload.query, payload.top_k)
        return KnowledgeSearchResponse(ok=True, results=results)
    except Exception as exc:  # noqa: BLE001
        return KnowledgeSearchResponse(ok=False, results=[], message=f"Search failed: {exc}")
