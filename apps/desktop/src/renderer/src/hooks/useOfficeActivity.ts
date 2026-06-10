import { useEffect, useState } from "react";
import { backendApi } from "../lib/api/client";
import type { ActivitySnapshot } from "../lib/api/types";

export type OfficeState = "checking" | "ready" | "offline";

export interface OfficeActivity {
  state: OfficeState;
  snapshot: ActivitySnapshot | null;
}

/**
 * Poll the live activity feed while the Office view is mounted.
 *
 * Polling only runs while the view is on screen (the interval dies with the
 * component), so the rest of the app keeps its "no background polling" rule.
 */
export function useOfficeActivity(intervalMs = 2500): OfficeActivity {
  const [state, setState] = useState<OfficeState>("checking");
  const [snapshot, setSnapshot] = useState<ActivitySnapshot | null>(null);

  useEffect(() => {
    let stopped = false;
    let timer: number | undefined;

    const tick = async (): Promise<void> => {
      try {
        const snap = await backendApi.getActivitySnapshot();
        if (!stopped) {
          setSnapshot(snap);
          setState("ready");
        }
      } catch {
        if (!stopped) setState("offline");
      }
      if (!stopped) timer = window.setTimeout(() => void tick(), intervalMs);
    };

    void tick();
    return () => {
      stopped = true;
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [intervalMs]);

  return { state, snapshot };
}
