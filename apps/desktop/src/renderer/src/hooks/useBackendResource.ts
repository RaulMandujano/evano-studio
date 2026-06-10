import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../lib/api/types";

/** Loading lifecycle for a backend GET request. */
export type ResourceState = "checking" | "ready" | "offline" | "error";

export interface BackendResource<T> {
  state: ResourceState;
  data: T | null;
  message: string | null;
  lastCheckedAt: Date | null;
  isLoading: boolean;
  refresh: () => void;
}

/**
 * Generic fetch-on-mount + manual-refresh hook for a backend resource.
 *
 * - `ready`   — the request succeeded (inspect `data`).
 * - `offline` — the backend couldn't be reached (network/timeout).
 * - `error`   — the backend responded with an error.
 *
 * `fetcher` MUST be a stable reference (e.g. a module-level function), otherwise
 * the effect will re-run on every render.
 */
export function useBackendResource<T>(fetcher: () => Promise<T>): BackendResource<T> {
  const [state, setState] = useState<ResourceState>("checking");
  const [data, setData] = useState<T | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [lastCheckedAt, setLastCheckedAt] = useState<Date | null>(null);

  const mounted = useRef(true);
  const requestId = useRef(0);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const run = useCallback(async () => {
    const id = ++requestId.current;
    setState("checking");
    setMessage(null);

    const apply = (fn: () => void) => {
      if (mounted.current && id === requestId.current) fn();
    };

    try {
      const result = await fetcher();
      apply(() => {
        setData(result);
        setState("ready");
        setLastCheckedAt(new Date());
      });
    } catch (error) {
      apply(() => {
        setData(null);
        setState(error instanceof ApiError && error.isUnreachable ? "offline" : "error");
        setMessage(error instanceof Error ? error.message : "Unknown error.");
        setLastCheckedAt(new Date());
      });
    }
  }, [fetcher]);

  useEffect(() => {
    void run();
  }, [run]);

  return {
    state,
    data,
    message,
    lastCheckedAt,
    isLoading: state === "checking",
    refresh: () => void run(),
  };
}
