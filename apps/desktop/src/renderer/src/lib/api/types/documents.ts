/**
 * Documents created/managed in the workspace.
 *
 * Mirrors the FastAPI schemas in `services/agent-engine/app/schemas`.
 */

export type DocumentType = "md" | "txt" | "html";

/** A local document (from `GET /documents`). */
export interface DocumentInfo {
  id: number;
  title: string;
  file_name: string;
  file_type: DocumentType;
  file_path: string;
  created_by_agent_id: number | null;
  created_at: string;
  updated_at: string;
  size_bytes: number | null;
  exists: boolean;
}

/** A document with its content (from `GET /documents/{id}`). */
export interface DocumentDetail extends DocumentInfo {
  content: string;
}

/** Body for `POST /documents`. */
export interface DocumentCreate {
  title: string;
  content: string;
  file_type?: DocumentType;
  file_name?: string;
  overwrite?: boolean;
  created_by_agent_id?: number | null;
}

/** Body for `POST /documents/from-agent-response`. */
export interface SaveAgentResponseBody {
  title: string;
  content: string;
  agent_id?: number | null;
  file_type?: DocumentType;
  file_name?: string;
  overwrite?: boolean;
}

