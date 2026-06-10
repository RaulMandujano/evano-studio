import { useEffect, useState } from "react";
import type { AppInfo } from "../../../shared/api";

/**
 * Reads basic app/runtime info from the main process via the secure preload
 * bridge. Returns null until loaded (or if the bridge is unavailable, e.g. when
 * the renderer is opened outside Electron).
 */
export function useAppInfo(): AppInfo | null {
  const [info, setInfo] = useState<AppInfo | null>(null);

  useEffect(() => {
    let active = true;
    if (!window.evano?.app?.getInfo) return;

    window.evano.app
      .getInfo()
      .then((result) => {
        if (active) setInfo(result);
      })
      .catch(() => {
        /* Ignore — the dashboard simply won't show runtime details. */
      });

    return () => {
      active = false;
    };
  }, []);

  return info;
}
