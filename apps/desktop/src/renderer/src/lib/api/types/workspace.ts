/**
 * Workspace folder + onboarding setup status.
 *
 * Mirrors the FastAPI schemas in `services/agent-engine/app/schemas`.
 */

// ---- Workspace / setup ----------------------------------------------------

/** A standard workspace subfolder and whether it exists. */
export interface WorkspaceSubdir {
  name: string;
  exists: boolean;
}

/** Response from `GET /workspace/status` and `POST /workspace/configure`. */
export interface WorkspaceStatus {
  path: string;
  configured: boolean;
  exists: boolean;
  is_default: boolean;
  default_path: string;
  subdirs: WorkspaceSubdir[];
  ready: boolean;
  message: string | null;
}

/** Aggregated onboarding status (from `GET /setup/status`). */
export interface SetupStatus {
  backend: { running: boolean; version: string; uptime_seconds: number };
  ollama: {
    status: string;
    reachable: boolean;
    version: string | null;
    recommended_model: string;
    recommended_available: boolean;
  };
  models: { count: number; installed: string[] };
  sqlite: { connected: boolean; file_exists: boolean; table_count: number; path: string | null };
  workspace: {
    configured: boolean;
    path: string;
    exists: boolean;
    ready: boolean;
    missing_subdirs: string[];
  };
  chromadb: { available: boolean; document_count: number; message: string | null };
  comfyui: { enabled: boolean; reachable: boolean; message: string | null };
  agents: { count: number; with_tools: number };
}

