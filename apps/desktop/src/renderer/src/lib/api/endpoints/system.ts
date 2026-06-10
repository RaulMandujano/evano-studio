/** system endpoints. */
import { requestJson } from "../http";
import type {
  SetupStatus,
  WorkspaceStatus,
  SystemInfo,
  DiscordStatus,
  SettingsResponse,
} from "../types";

/** `GET /setup/status` — aggregated onboarding status for Easy Start. */
export function getSetupStatus(): Promise<SetupStatus> {
  return requestJson<SetupStatus>("/setup/status", { timeoutMs: 8000 });
}

/** `GET /workspace/status` — current workspace configuration + structure. */
export function getWorkspaceStatus(): Promise<WorkspaceStatus> {
  return requestJson<WorkspaceStatus>("/workspace/status");
}

/** `POST /workspace/configure` — set/reset the workspace and create subfolders. */
export function configureWorkspace(path: string): Promise<WorkspaceStatus> {
  return requestJson<WorkspaceStatus>("/workspace/configure", { method: "POST", body: { path } });
}

/** `GET /system/info` — runtime info incl. default workspace path. */
export function getSystemInfo(): Promise<SystemInfo> {
  return requestJson<SystemInfo>("/system/info");
}

/** `GET /discord/status` — Discord channel availability + state. */
export function getDiscordStatus(): Promise<DiscordStatus> {
  return requestJson<DiscordStatus>("/discord/status");
}

export function getSettings(): Promise<SettingsResponse> {
  return requestJson<SettingsResponse>("/settings");
}

/** `PUT /settings` — create/update settings. */
export function updateSettings(settings: Record<string, string>): Promise<SettingsResponse> {
  return requestJson<SettingsResponse>("/settings", { method: "PUT", body: { settings } });
}

