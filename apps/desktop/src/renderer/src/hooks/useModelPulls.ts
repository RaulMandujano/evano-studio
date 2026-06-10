import { useCallback, useEffect, useRef, useState } from "react";
import { backendApi } from "../lib/api/client";
import type { PullStatus } from "../lib/api/types";

export interface ModelPulls {
  /** Latest known status per model that has been started this session. */
  pulls: Record<string, PullStatus>;
  /** Begin installing a model (non-blocking). */
  start: (model: string) => Promise<void>;
}

const POLL_INTERVAL_MS = 1200;

function errorStatus(model: string, message: string): PullStatus {
  return {
    model,
    state: "error",
    percent: 0,
    completed_bytes: 0,
    total_bytes: 0,
    detail: null,
    message,
    updated_at: null,
  };
}

/**
 * Manages model installs via status polling (the backend pulls in the
 * background). Calls `onSuccess` once per model that finishes successfully — use
 * it to refresh the installed/recommended lists.
 */
export function useModelPulls(onSuccess?: () => void): ModelPulls {
  const [pulls, setPulls] = useState<Record<string, PullStatus>>({});
  const pullsRef = useRef(pulls);
  pullsRef.current = pulls;

  const onSuccessRef = useRef(onSuccess);
  onSuccessRef.current = onSuccess;

  const completed = useRef<Set<string>>(new Set());

  const start = useCallback(async (model: string) => {
    try {
      const status = await backendApi.startModelPull(model);
      setPulls((prev) => ({ ...prev, [model]: status }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Couldn't start the install.";
      setPulls((prev) => ({ ...prev, [model]: errorStatus(model, message) }));
    }
  }, []);

  useEffect(() => {
    const id = window.setInterval(async () => {
      const active = Object.values(pullsRef.current).filter(
        (s) => s.state === "pending" || s.state === "downloading",
      );
      if (active.length === 0) return;

      for (const status of active) {
        try {
          const next = await backendApi.getPullStatus(status.model);
          setPulls((prev) => ({ ...prev, [status.model]: next }));
          if (next.state === "success" && !completed.current.has(status.model)) {
            completed.current.add(status.model);
            onSuccessRef.current?.();
          }
        } catch {
          /* Keep the last known status; try again next tick. */
        }
      }
    }, POLL_INTERVAL_MS);

    return () => window.clearInterval(id);
  }, []);

  return { pulls, start };
}
