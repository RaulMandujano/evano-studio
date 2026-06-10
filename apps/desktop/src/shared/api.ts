/**
 * Shared IPC contract between the Electron main process and the renderer.
 *
 * This file contains ONLY plain types + channel names — no Electron or Node
 * imports — so it is safe to include from the preload (privileged) and the
 * renderer (sandboxed) without leaking capabilities across the boundary.
 */

export interface AppInfo {
  name: string;
  version: string;
  platform: string;
  versions: {
    electron: string;
    node: string;
    chrome: string;
  };
}

/** Result of an OS reveal request. */
export interface RevealResult {
  ok: boolean;
  error?: string;
}

/** Result of picking and reading a local text file. */
export interface PickTextFileResult {
  ok: boolean;
  canceled?: boolean;
  fileName?: string;
  path?: string;
  content?: string;
  error?: string;
}

/** Result of picking a folder. */
export interface PickFolderResult {
  ok: boolean;
  canceled?: boolean;
  path?: string;
  error?: string;
}

/** Status of the local backend service (as seen by the main process). */
export interface BackendServiceStatus {
  url: string;
  reachable: boolean;
  /** True only if Evano Studio itself started the backend process. */
  managed: boolean;
  /** True when a configured auto-start command is available and usable. */
  canStart: boolean;
}

/** Overall local service status + key local paths. */
export interface ServiceStatus {
  backend: BackendServiceStatus;
  dataDir: string;
  workspaceDir: string;
  logsDir: string;
}

/** Result of a service action (start/stop/open). */
export interface ServiceActionResult {
  ok: boolean;
  reason?: string;
  error?: string;
}

/** The minimal, safe API exposed on `window.evano` via contextBridge. */
export interface EvanoApi {
  app: {
    /** Returns basic, non-sensitive app + runtime info. */
    getInfo: () => Promise<AppInfo>;
  };
  documents: {
    /** Reveal a file in the OS file manager (does not open/execute it). */
    revealPath: (path: string) => Promise<RevealResult>;
  };
  knowledge: {
    /** Open a picker for a .txt/.md file and return its contents. */
    pickTextFile: () => Promise<PickTextFileResult>;
  };
  system: {
    /** Open a folder picker (for choosing the workspace directory). */
    pickFolder: () => Promise<PickFolderResult>;
  };
  services: {
    /** Get local service status (backend reachability + paths). */
    getStatus: () => Promise<ServiceStatus>;
    /** Start the backend — only if an auto-start command is configured. */
    startBackend: () => Promise<ServiceActionResult>;
    /** Stop the backend — only if Evano Studio started it. */
    stopBackend: () => Promise<ServiceActionResult>;
    /** Open an http/https URL in the default browser (validated). */
    openExternal: (url: string) => Promise<ServiceActionResult>;
    /** Open the default workspace folder in the OS file manager. */
    openWorkspace: () => Promise<ServiceActionResult>;
    /**
     * Open a specific (configured) workspace folder. The path comes from the
     * backend (the single source of truth); it's validated as an existing
     * absolute directory before opening.
     */
    openWorkspacePath: (path: string) => Promise<ServiceActionResult>;
    /** Open the logs folder in the OS file manager. */
    openLogs: () => Promise<ServiceActionResult>;
  };
}

/** Centralized IPC channel names so main and preload can't drift apart. */
export const IpcChannels = {
  appGetInfo: "app:get-info",
  documentsReveal: "documents:reveal-path",
  knowledgePickTextFile: "knowledge:pick-text-file",
  systemPickFolder: "system:pick-folder",
  servicesGetStatus: "services:get-status",
  servicesStartBackend: "services:start-backend",
  servicesStopBackend: "services:stop-backend",
  servicesOpenExternal: "services:open-external",
  servicesOpenWorkspace: "services:open-workspace",
  servicesOpenWorkspacePath: "services:open-workspace-path",
  servicesOpenLogs: "services:open-logs",
} as const;
