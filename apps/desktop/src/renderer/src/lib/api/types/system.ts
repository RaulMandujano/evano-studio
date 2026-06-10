/**
 * System info and app settings.
 *
 * Mirrors the FastAPI schemas in `services/agent-engine/app/schemas`.
 */

// ---- System / settings ----------------------------------------------------

/** Subset of `GET /system/info` used by the desktop. */
export interface SystemInfo {
  service: string;
  version: string;
  workspace_path: string;
}

/** Response from `GET /settings`. */
export interface SettingsResponse {
  settings: Record<string, string>;
}

