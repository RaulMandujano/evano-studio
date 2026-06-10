/** knowledge endpoints. */
import { requestJson } from "../http";
import type {
  KnowledgeStatus,
  KnowledgeDocument,
  KnowledgeImportBody,
  KnowledgeSearchResponse,
  KnowledgeSyncResult,
} from "../types";


/** `GET /knowledge/status` — local ChromaDB status. */
export function getKnowledgeStatus(): Promise<KnowledgeStatus> {
  return requestJson<KnowledgeStatus>("/knowledge/status");
}

/** `GET /knowledge/documents` — list KB documents. */
export function getKnowledgeDocuments(): Promise<KnowledgeDocument[]> {
  return requestJson<KnowledgeDocument[]>("/knowledge/documents");
}

/** `POST /knowledge/documents/import` — import + index a text document. */
export function importKnowledgeDocument(body: KnowledgeImportBody): Promise<KnowledgeDocument> {
  // Embedding/indexing can take a while (first run downloads a model).
  return requestJson<KnowledgeDocument>("/knowledge/documents/import", {
    method: "POST",
    body,
    timeoutMs: 180_000,
  });
}

/** `DELETE /knowledge/documents/{id}` — delete a KB document and its chunks. */
export function deleteKnowledgeDocument(id: number): Promise<{ ok: boolean }> {
  return requestJson<{ ok: boolean }>(`/knowledge/documents/${id}`, { method: "DELETE" });
}

/** `POST /knowledge/search` — semantic search over the knowledge base. */
export function searchKnowledge(query: string, topK?: number): Promise<KnowledgeSearchResponse> {
  return requestJson<KnowledgeSearchResponse>("/knowledge/search", {
    method: "POST",
    body: { query, top_k: topK },
    timeoutMs: 60_000,
  });
}


/** `POST /knowledge/sync-agents` — mirror the KB into every agent's memory so
 *  the knowledge also works on Discord and in delegated (Org Chart) runs. */
export function syncKnowledgeToAgents(): Promise<KnowledgeSyncResult> {
  return requestJson<KnowledgeSyncResult>("/knowledge/sync-agents", {
    method: "POST",
    timeoutMs: 120_000,
  });
}
