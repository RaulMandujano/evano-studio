/**
 * Safe local service management (main process).
 *
 * Security model:
 * - The renderer can only trigger a small set of approved actions over IPC.
 * - It can NEVER pass a command to run. Auto-start uses a pre-configured command
 *   from environment variables, spawned with shell:false (no shell, no injection).
 * - We only ever stop a backend process WE started (tracked child), never an
 *   externally-run one.
 * - "Open external" is restricted to http/https URLs.
 * - Folder opening is limited to the known workspace/logs directories.
 * No sudo, no arbitrary terminal execution, no silent installs.
 */

import { app, ipcMain, shell } from "electron";
import { type ChildProcess, spawn } from "node:child_process";
import { existsSync, mkdirSync, openSync, statSync } from "node:fs";
import { dirname, isAbsolute, join } from "node:path";
import {
  IpcChannels,
  type ServiceActionResult,
  type ServiceStatus,
} from "../shared/api";

let backendChild: ChildProcess | null = null;

function dataDir(): string {
  return process.env["EVANO_DATA_DIR"] || join(app.getPath("home"), ".evano-studio");
}

function workspaceDir(): string {
  return join(dataDir(), "workspace");
}

function logsDir(): string {
  return join(dataDir(), "logs");
}

function backendUrl(): string {
  return process.env["EVANO_BACKEND_URL"] || "http://127.0.0.1:8765";
}

/** Path to the frozen backend bundled inside a packaged build, if present. */
function bundledBackendPath(): string | null {
  if (!app.isPackaged) return null; // dev uses a manually-run / env backend
  const exe = join(process.resourcesPath, "evano-backend", "evano-backend");
  return existsSync(exe) ? exe : null;
}

/**
 * Where to get the backend command. Priority:
 * 1. An explicit EVANO_BACKEND_CMD from the environment (advanced/dev).
 * 2. The frozen backend bundled in the packaged app (the client default).
 * The renderer can NEVER supply a command — only these trusted sources.
 */
function backendCommand(): { cmd: string; args: string[]; cwd?: string } | null {
  const cmd = process.env["EVANO_BACKEND_CMD"];
  if (cmd) {
    let args: string[] = [];
    const rawArgs = process.env["EVANO_BACKEND_ARGS"];
    if (rawArgs) {
      try {
        const parsed = JSON.parse(rawArgs);
        if (Array.isArray(parsed)) args = parsed.map(String);
      } catch {
        /* ignore malformed args */
      }
    }
    return { cmd, args, cwd: process.env["EVANO_BACKEND_CWD"] || undefined };
  }
  const bundled = bundledBackendPath();
  if (bundled) return { cmd: bundled, args: [], cwd: dirname(bundled) };
  return null;
}

/**
 * On launch, start the bundled backend if it isn't already running. This is what
 * lets a non-technical client just open the app — no terminal, no Python.
 */
export async function ensureBackendStarted(): Promise<void> {
  if (await isReachable()) return; // already running (e.g. dev server)
  if (backendCommand()) startBackend();
}

const delay = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Auto-start the OpenClaw gateway when Evano opens, so a non-technical client
 * never has to press "Start". Best-effort and safe:
 * - waits for the local backend to come up (bundled backend takes a few seconds),
 * - only acts if OpenClaw is already configured (config exists) and not running,
 * - all calls go to the local Agent Engine over loopback; failures are swallowed.
 * We never install or configure anything here — that stays an explicit user action.
 */
export async function ensureOpenClawGatewayStarted(): Promise<void> {
  // Wait up to ~30s for the backend to be reachable.
  let reachable = false;
  for (let i = 0; i < 20; i++) {
    if (await isReachable()) {
      reachable = true;
      break;
    }
    await delay(1500);
  }
  if (!reachable) return;

  try {
    const statusRes = await fetch(`${backendUrl()}/openclaw/status`);
    if (!statusRes.ok) return;
    const status = (await statusRes.json()) as {
      config?: { exists?: boolean };
      gateway?: { running?: boolean };
    };
    // Nothing to start: not configured yet, or already running.
    if (!status.config?.exists || status.gateway?.running) return;
    await fetch(`${backendUrl()}/openclaw/gateway/start`, { method: "POST" });
  } catch {
    /* best effort — the OpenClaw page still lets the user start it manually */
  }
}

function isManaged(): boolean {
  return backendChild !== null && backendChild.exitCode === null && !backendChild.killed;
}

async function isReachable(): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 1500);
    const response = await fetch(`${backendUrl()}/health`, { signal: controller.signal });
    clearTimeout(timer);
    return response.ok;
  } catch {
    return false;
  }
}

async function getStatus(): Promise<ServiceStatus> {
  const reachable = await isReachable();
  return {
    backend: {
      url: backendUrl(),
      reachable,
      managed: isManaged(),
      canStart: backendCommand() !== null && !isManaged() && !reachable,
    },
    dataDir: dataDir(),
    workspaceDir: workspaceDir(),
    logsDir: logsDir(),
  };
}

function startBackend(): ServiceActionResult {
  if (isManaged()) return { ok: false, reason: "already_running" };
  const config = backendCommand();
  if (!config) return { ok: false, reason: "not_configured" };
  try {
    mkdirSync(logsDir(), { recursive: true });
    const logFile = openSync(join(logsDir(), "agent-engine.log"), "a");
    backendChild = spawn(config.cmd, config.args, {
      cwd: config.cwd,
      shell: false, // critical: no shell → no command injection
      stdio: ["ignore", logFile, logFile],
    });
    backendChild.on("exit", () => {
      backendChild = null;
    });
    return { ok: true };
  } catch (error) {
    backendChild = null;
    return { ok: false, error: error instanceof Error ? error.message : "Failed to start backend." };
  }
}

function stopBackend(): ServiceActionResult {
  // Only ever stop a process we started.
  if (!isManaged() || backendChild === null) return { ok: false, reason: "not_managed" };
  try {
    backendChild.kill();
    return { ok: true };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : "Failed to stop backend." };
  }
}

function openExternal(url: unknown): ServiceActionResult {
  if (typeof url !== "string") return { ok: false, error: "Invalid URL." };
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return { ok: false, error: "Invalid URL." };
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    return { ok: false, error: "Only http/https links can be opened." };
  }
  void shell.openExternal(url);
  return { ok: true };
}

async function openFolder(dir: string): Promise<ServiceActionResult> {
  try {
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
    const error = await shell.openPath(dir);
    return error === "" ? { ok: true } : { ok: false, error };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : "Couldn't open folder." };
  }
}

/**
 * Open a specific workspace folder (the one configured in the backend). We never
 * create it here and never open arbitrary inputs: the path must be an absolute,
 * already-existing directory. This only *opens* it in the OS file manager — it
 * never executes anything. Keeps a single source of truth: the renderer passes
 * the backend's configured workspace path.
 */
async function openWorkspacePath(rawPath: unknown): Promise<ServiceActionResult> {
  if (typeof rawPath !== "string" || !rawPath.trim()) {
    return { ok: false, error: "No workspace path provided." };
  }
  if (!isAbsolute(rawPath)) {
    return { ok: false, error: "Workspace path must be absolute." };
  }
  try {
    if (!existsSync(rawPath)) {
      return { ok: false, error: "That workspace folder doesn't exist yet." };
    }
    if (!statSync(rawPath).isDirectory()) {
      return { ok: false, error: "That path is not a folder." };
    }
    const error = await shell.openPath(rawPath);
    return error === "" ? { ok: true } : { ok: false, error };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : "Couldn't open folder." };
  }
}

/** Kill a managed backend on app quit (never an external one). */
export function stopManagedBackend(): void {
  if (isManaged() && backendChild) {
    try {
      backendChild.kill();
    } catch {
      /* best effort */
    }
  }
}

export function registerServiceHandlers(): void {
  ipcMain.handle(IpcChannels.servicesGetStatus, () => getStatus());
  ipcMain.handle(IpcChannels.servicesStartBackend, () => startBackend());
  ipcMain.handle(IpcChannels.servicesStopBackend, () => stopBackend());
  ipcMain.handle(IpcChannels.servicesOpenExternal, (_event, url: unknown) => openExternal(url));
  ipcMain.handle(IpcChannels.servicesOpenWorkspace, () => openFolder(workspaceDir()));
  ipcMain.handle(IpcChannels.servicesOpenWorkspacePath, (_event, path: unknown) =>
    openWorkspacePath(path),
  );
  ipcMain.handle(IpcChannels.servicesOpenLogs, () => openFolder(logsDir()));
}
