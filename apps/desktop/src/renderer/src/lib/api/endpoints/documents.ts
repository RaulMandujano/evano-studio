/** documents endpoints. */
import { requestJson } from "../http";
import type {
  DocumentInfo,
  DocumentCreate,
  DocumentDetail,
  SaveAgentResponseBody,
} from "../types";


/** `GET /documents` — list documents. */
export function getDocuments(): Promise<DocumentInfo[]> {
  return requestJson<DocumentInfo[]>("/documents");
}

/** `POST /documents` — create a document. */
export function createDocument(body: DocumentCreate): Promise<DocumentInfo> {
  return requestJson<DocumentInfo>("/documents", { method: "POST", body });
}

/** `GET /documents/{id}` — read a document (with content). */
export function getDocument(id: number): Promise<DocumentDetail> {
  return requestJson<DocumentDetail>(`/documents/${id}`);
}

/** `DELETE /documents/{id}` — delete a document (and its file). */
export function deleteDocument(id: number): Promise<{ ok: boolean }> {
  return requestJson<{ ok: boolean }>(`/documents/${id}`, { method: "DELETE" });
}

/** `POST /documents/from-agent-response` — save an agent reply as a document. */
export function saveAgentResponse(body: SaveAgentResponseBody): Promise<DocumentInfo> {
  return requestJson<DocumentInfo>("/documents/from-agent-response", {
    method: "POST",
    body,
  });
}

