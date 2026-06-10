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
 * Session-wide cache for `cacheKey`-enabled resources (stale-while-revalidate):
 * revisiting a tab renders the last data INSTANTLY and refreshes silently in
 * the background — no more spinner on every tab switch.
 */
const resourceCache = new Map<string, unknown>();

/**
 * Generic fetch-on-mount + manual-refresh hook for a backend resource.
 *
 * - `ready`   — the request succeeded (inspect `data`).
 * - `offline` — the backend couldn't be reached (network/timeout).
 * - `error`   — the backend responded with an error.
 *
 * `fetcher` MUST be a stable reference (e.g. a module-level function), otherwise
 * the effect will re-run on every render.
 *
 * Pass a `cacheKey` to opt in to stale-while-revalidate: the previous result is
 * shown immediately while a fresh fetch runs in the background.
 */
export function useBackendResource<T>(fetcher: () => Promise<T>, cacheKey?: string): BackendResource<T> {
  const cached = cacheKey !== undefined ? (resourceCache.get(cacheKey) as T | undefined) : undefined;
  const [state, setState] = useState<ResourceState>(cached !== undefined ? "ready" : "checking");
  const [data, setData] = useState<T | null>(cached ?? null);
  const [message, setMessage] = useState<string | null>(null);
  const [lastCheckedAt, setLastCheckedAt] = useState<Date | null>(null);

  const mounted = useRef(true);
  const requestId = useRef(0);
  const hasData = useRef(cached !== undefined);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const run = useCallback(async () => {
    const id = ++requestId.current;
    // Silent revalidate when we already have something to show.
    if (!hasData.current) setState("checking");
    setMessage(null);

    const apply = (fn: () => void) => {
      if (mounted.current && id === requestId.current) fn();
    };

    try {
      const result = await fetcher();
      if (cacheKey !== undefined) resourceCache.set(cacheKey, result);
      hasData.current = true;
      apply(() => {
        setData(result);
        setState("ready");
        setLastCheckedAt(new Date());
      });
    } catch (error) {
      hasData.current = false;
      if (cacheKey !== undefined) resourceCache.delete(cacheKey);
      apply(() => {
        setData(null);
        setState(error instanceof ApiError && error.isUnreachable ? "offline" : "error");
        setMessage(error instanceof Error ? error.message : "Unknown error.");
        setLastCheckedAt(new Date());
      });
    }
  }, [fetcher, cacheKey]);

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
