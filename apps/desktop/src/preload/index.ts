import { contextBridge, ipcRenderer } from "electron";
import { IpcChannels, type EvanoApi } from "../shared/api";

/**
 * The ONLY surface exposed to the renderer. Each method is explicit and maps to
 * a single safe IPC channel. We never expose `ipcRenderer`, `require`, or any
 * Node API directly. See docs/SECURITY.md.
 */
const api: EvanoApi = {
  app: {
    getInfo: () => ipcRenderer.invoke(IpcChannels.appGetInfo),
  },
  documents: {
    revealPath: (path: string) => ipcRenderer.invoke(IpcChannels.documentsReveal, path),
  },
  knowledge: {
    pickTextFile: () => ipcRenderer.invoke(IpcChannels.knowledgePickTextFile),
  },
  system: {
    pickFolder: () => ipcRenderer.invoke(IpcChannels.systemPickFolder),
  },
  services: {
    getStatus: () => ipcRenderer.invoke(IpcChannels.servicesGetStatus),
    startBackend: () => ipcRenderer.invoke(IpcChannels.servicesStartBackend),
    stopBackend: () => ipcRenderer.invoke(IpcChannels.servicesStopBackend),
    openExternal: (url: string) => ipcRenderer.invoke(IpcChannels.servicesOpenExternal, url),
    openWorkspace: () => ipcRenderer.invoke(IpcChannels.servicesOpenWorkspace),
    openWorkspacePath: (path: string) =>
      ipcRenderer.invoke(IpcChannels.servicesOpenWorkspacePath, path),
    openLogs: () => ipcRenderer.invoke(IpcChannels.servicesOpenLogs),
  },
};

contextBridge.exposeInMainWorld("evano", api);
