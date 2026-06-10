/// <reference types="vite/client" />

import type { EvanoApi } from "../../shared/api";

declare global {
  interface Window {
    /** Safe API exposed by the preload via contextBridge. */
    evano: EvanoApi;
  }
}

export {};
