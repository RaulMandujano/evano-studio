/** Display helpers for routines. */

import type { BadgeTone } from "../components/ui/Badge";
import type { Routine } from "./api/types";

const DAY_LABELS: Record<string, string> = {
  mon: "Mon",
  tue: "Tue",
  wed: "Wed",
  thu: "Thu",
  fri: "Fri",
  sat: "Sat",
  sun: "Sun",
};

export function formatDateTime(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function scheduleSummary(routine: Routine): string {
  switch (routine.schedule_type) {
    case "manual":
      return "Manual only";
    case "once":
      return routine.start_at ? `Once · ${formatDateTime(routine.start_at)}` : "Once";
    case "daily":
      return `Daily at ${routine.schedule_value}`;
    case "weekly": {
      const [day, time] = routine.schedule_value.split(" ");
      return `Weekly · ${DAY_LABELS[day] ?? day} ${time ?? ""}`.trim();
    }
    default:
      return routine.schedule_type;
  }
}

/** Maps a routine or run status to a badge tone. */
export function statusTone(status: string): BadgeTone {
  switch (status) {
    case "success":
    case "done":
      return "ok";
    case "error":
      return "danger";
    case "missed":
      return "pending";
    case "scheduled":
    case "running":
      return "info";
    default:
      return "neutral";
  }
}
