import { app, BrowserWindow, dialog, ipcMain, nativeTheme, session, shell } from "electron";
import { existsSync, readFileSync, statSync } from "node:fs";
import { basename, extname, isAbsolute, join } from "node:path";
import {
  IpcChannels,
  type AppInfo,
  type PickFolderResult,
  type PickTextFileResult,
  type RevealResult,
} from "../shared/api";
import {
  ensureBackendStarted,
  ensureOpenClawGatewayStarted,
  registerServiceHandlers,
  stopManagedBackend,
} from "./services";

/** electron-vite sets this only while the dev server is running. */
const RENDERER_DEV_URL = process.env["ELECTRON_RENDERER_URL"];
const isDev = Boolean(RENDERER_DEV_URL);

const MAX_IMPORT_BYTES = 5 * 1024 * 1024; // 5 MB cap for text imports

function createMainWindow(): void {
  const window = new BrowserWindow({
    width: 1240,
    height: 820,
    minWidth: 960,
    minHeight: 640,
    show: false,
    backgroundColor: "#0a0c11",
    title: "Evano Studio",
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, "../preload/index.js"),
      // ---- Security defaults (see apps/desktop/README.md + docs/SECURITY.md) ----
      contextIsolation: true, // renderer + preload run in isolated worlds
      nodeIntegration: false, // no Node.js APIs in the renderer
      sandbox: true, // renderer runs in an OS sandbox
      webSecurity: true, // keep the browser security model on
      webviewTag: true, // allow <webview> to embed the local OpenClaw dashboard
    },
  });

  // Lock down any <webview> the renderer attaches: strip preload/node access and
  // only allow it to load the local OpenClaw dashboard over loopback. The
  // dashboard sets X-Frame-Options: DENY, so a top-level <webview> (not an
  // iframe) is the safe way to embed it inside Evano.
  window.webContents.on("will-attach-webview", (event, webPreferences, params) => {
    delete webPreferences.preload;
    webPreferences.nodeIntegration = false;
    webPreferences.contextIsolation = true;
    let host: string;
    try {
      host = new URL(params.src).hostname;
    } catch {
      event.preventDefault();
      return;
    }
    if (host !== "127.0.0.1" && host !== "localhost") event.preventDefault();
  });

  // Avoid a white flash; show once the renderer has painted.
  window.once("ready-to-show", () => window.show());

  // Nothing should pop out a new window yet.
  window.webContents.setWindowOpenHandler(() => ({ action: "deny" }));

  // Block navigation away from our own app (no external/unknown origins).
  window.webContents.on("will-navigate", (event, url) => {
    if (RENDERER_DEV_URL && url.startsWith(RENDERER_DEV_URL)) return;
    event.preventDefault();
  });

  if (RENDERER_DEV_URL) {
    void window.loadURL(RENDERER_DEV_URL);
  } else {
    void window.loadFile(join(__dirname, "../renderer/index.html"));
  }
}

/**
 * Safe IPC handlers. For now this only returns basic, non-sensitive runtime
 * info — proof that the secure bridge works, without any real functionality.
 */
function registerIpcHandlers(): void {
  ipcMain.handle(IpcChannels.appGetInfo, (): AppInfo => {
    return {
      name: app.getName(),
      version: app.getVersion(),
      platform: process.platform,
      versions: {
        electron: process.versions.electron ?? "",
        node: process.versions.node,
        chrome: process.versions.chrome ?? "",
      },
    };
  });

  // Reveal a document in the OS file manager. This only *shows* the file
  // (it never opens/executes it). We validate the input is a real, absolute,
  // existing path before handing it to the shell.
  ipcMain.handle(
    IpcChannels.documentsReveal,
    (_event, rawPath: unknown): RevealResult => {
      if (typeof rawPath !== "string" || !isAbsolute(rawPath) || !existsSync(rawPath)) {
        return { ok: false, error: "Invalid or missing path." };
      }
      shell.showItemInFolder(rawPath);
      return { ok: true };
    },
  );

  // Pick and read a local .txt/.md file for knowledge-base import. The user
  // explicitly chooses the file; we enforce extension + size limits and only
  // return its text content (the backend never reads arbitrary paths).
  ipcMain.handle(
    IpcChannels.knowledgePickTextFile,
    async (): Promise<PickTextFileResult> => {
      const win = BrowserWindow.getFocusedWindow() ?? undefined;
      const result = await dialog.showOpenDialog(win!, {
        properties: ["openFile"],
        filters: [{ name: "Text", extensions: ["txt", "md", "markdown"] }],
      });
      if (result.canceled || result.filePaths.length === 0) {
        return { ok: false, canceled: true };
      }
      const filePath = result.filePaths[0];
      const ext = extname(filePath).toLowerCase();
      if (![".txt", ".md", ".markdown"].includes(ext)) {
        return { ok: false, error: "Only .txt and .md files are supported." };
      }
      try {
        if (statSync(filePath).size > MAX_IMPORT_BYTES) {
          return { ok: false, error: "File is too large (max 5 MB)." };
        }
        const content = readFileSync(filePath, "utf-8");
        return { ok: true, fileName: basename(filePath), path: filePath, content };
      } catch (error) {
        return { ok: false, error: error instanceof Error ? error.message : "Read failed." };
      }
    },
  );

  // Pick a folder (used to choose the workspace directory in Settings).
  ipcMain.handle(IpcChannels.systemPickFolder, async (): Promise<PickFolderResult> => {
    const win = BrowserWindow.getFocusedWindow() ?? undefined;
    const result = await dialog.showOpenDialog(win!, {
      properties: ["openDirectory", "createDirectory"],
    });
    if (result.canceled || result.filePaths.length === 0) {
      return { ok: false, canceled: true };
    }
    return { ok: true, path: result.filePaths[0] };
  });
}

/**
 * Enforce a strict Content-Security-Policy in production. In development the
 * Vite dev server / HMR needs a relaxed policy, so we only apply this when not
 * running against the dev server.
 */
function applyContentSecurityPolicy(): void {
  if (isDev) return;
  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        "Content-Security-Policy": [
          [
            "default-src 'self'",
            "script-src 'self'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data:",
            "font-src 'self' data:",
            // Allow the renderer to reach the local Agent Engine over loopback.
            "connect-src 'self' http://127.0.0.1:* http://localhost:* ws://127.0.0.1:* ws://localhost:*",
            "object-src 'none'",
            "base-uri 'none'",
            "frame-ancestors 'none'",
          ].join("; "),
        ],
      },
    });
  });
}

app.whenReady().then(() => {
  // Evano's UI is dark by design. Force a dark color scheme so embedded content
  // that follows the OS theme (the OpenClaw dashboard <webview>) renders dark too
  // and matches — instead of showing a bright white panel.
  nativeTheme.themeSource = "dark";
  applyContentSecurityPolicy();
  registerIpcHandlers();
  registerServiceHandlers();
  // Auto-start the bundled backend (packaged builds) so clients need no terminal.
  void ensureBackendStarted();
  // Then bring OpenClaw up on its own (if already installed + configured), so the
  // client opens Evano and everything is running — no buttons to press.
  void ensureOpenClawGatewayStarted();
  createMainWindow();

  app.on("activate", () => {
    // macOS: re-open a window when the dock icon is clicked and none are open.
    if (BrowserWindow.getAllWindows().length === 0) createMainWindow();
  });
});

app.on("window-all-closed", () => {
  // macOS apps usually stay active until Cmd+Q.
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  // Shut down a backend we started (never an externally-run one).
  stopManagedBackend();
});
