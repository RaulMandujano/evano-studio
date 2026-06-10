import { useCallback, useEffect, useRef, useState } from "react";
import { backendApi, backendBaseUrl } from "../lib/api/client";
import { ApiError, type HealthResponse } from "../lib/api/types";

/** The four states the dashboard cares about. */
export type EngineStatus = "checking" | "running" | "offline" | "error";

export interface AgentEngineState {
  status: EngineStatus;
  /** Health payload when running, otherwise null. */
  health: HealthResponse | null;
  /** Human-readable detail for offline/error states (null when running). */
  message: string | null;
  /** When the last check completed. */
  lastCheckedAt: Date | null;
  /** The backend URL being checked (for display). */
  baseUrl: string;
  /** True while a check is in flight. */
  isChecking: boolean;
  /** Re-run the health check. */
  refresh: () => void;
}

/**
 * Checks the local Agent Engine's `/health` on mount and on demand. Handles an
 * offline backend gracefully: a network/timeout failure becomes "offline" (not
 * a crash), while a reachable-but-bad backend becomes "error".
 *
 * Intentionally no auto-polling and no global state — kept simple and modular.
 */
export function useAgentEngineStatus(): AgentEngineState {
  const [status, setStatus] = useState<EngineStatus>("checking");
  const [health, setHealth] = useState<HealthResponse | null>(null);
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

  const check = useCallback(async () => {
    const id = ++requestId.current;
    setStatus("checking");
    setMessage(null);

    const apply = (fn: () => void) => {
      // Ignore results from stale checks or after unmount.
      if (mounted.current && id === requestId.current) fn();
    };

    try {
      const result = await backendApi.getHealth();
      apply(() => {
        if (result.status === "ok") {
          setHealth(result);
          setStatus("running");
        } else {
          setHealth(result);
          setStatus("error");
          setMessage(`Unexpected status from backend: "${result.status}".`);
        }
        setLastCheckedAt(new Date());
      });
    } catch (error) {
      apply(() => {
        setHealth(null);
        if (error instanceof ApiError && error.isUnreachable) {
          setStatus("offline");
        } else {
          setStatus("error");
        }
        setMessage(error instanceof Error ? error.message : "Unknown error.");
        setLastCheckedAt(new Date());
      });
    }
  }, []);

  useEffect(() => {
    void check();
  }, [check]);

  return {
    status,
    health,
    message,
    lastCheckedAt,
    baseUrl: backendBaseUrl,
    isChecking: status === "checking",
    refresh: () => void check(),
  };
}
