/**
 * Local knowledge base (ChromaDB-backed RAG).
 *
 * Mirrors the FastAPI schemas in `services/agent-engine/app/schemas`.
 */

// ---- Knowledge base (RAG) -------------------------------------------------

/** Response from `GET /knowledge/status`. */
export interface KnowledgeStatus {
  available: boolean;
  engine: string;
  embedding: string;
  path: string | null;
  collection: string;
  document_count: number;
  chunk_count: number;
  message: string | null;
}

/** A knowledge-base document (from `GET /knowledge/documents`). */
export interface KnowledgeDocument {
  id: number;
  title: string;
  file_name: string;
  source_path: string;
  collection_name: string;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

/** Body for `POST /knowledge/documents/import`. */
export interface KnowledgeImportBody {
  title: string;
  file_name: string;
  content: string;
  file_type?: "txt" | "md";
  source_path?: string;
}

/** A single search hit (from `POST /knowledge/search`). */
export interface KnowledgeSearchResult {
  text: string;
  document_id: number | null;
  chunk_index: number | null;
  title: string | null;
  file_name: string | null;
  distance: number | null;
}

/** Response from `POST /knowledge/search`. */
export interface KnowledgeSearchResponse {
  ok: boolean;
  results: KnowledgeSearchResult[];
  message: string | null;
}


/** Response from `POST /knowledge/sync-agents`. */
export interface KnowledgeSyncResult {
  ok: boolean;
  agents_synced: number;
  files_written: number;
  message: string;
}
