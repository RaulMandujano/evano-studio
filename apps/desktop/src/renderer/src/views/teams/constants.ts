/** Shared constants for the Teams views. */
import type { StepStatus } from "../../lib/teamsStore";

export const DAYS = [
  { value: "mon", label: "Mon" }, { value: "tue", label: "Tue" }, { value: "wed", label: "Wed" },
  { value: "thu", label: "Thu" }, { value: "fri", label: "Fri" }, { value: "sat", label: "Sat" }, { value: "sun", label: "Sun" },
];

export const STATUS_META: Record<StepStatus, { tone: "neutral" | "pending" | "ok" | "danger"; label: string }> = {
  pending: { tone: "neutral", label: "Waiting" },
  working: { tone: "pending", label: "Working…" },
  done: { tone: "ok", label: "Done" },
  empty: { tone: "danger", label: "No output" },
  error: { tone: "danger", label: "Error" },
};

export type { StepStatus };
