/**
 * Routines and the calendar (scheduled agent/team tasks).
 *
 * Mirrors the FastAPI schemas in `services/agent-engine/app/schemas`.
 */

// ---- Routines / calendar --------------------------------------------------

export type ScheduleType = "manual" | "once" | "daily" | "weekly";

/** A routine (from `GET /routines`). Time fields are naive-local ISO strings. */
export interface Routine {
  id: number;
  name: string;
  agent_id: number;
  openclaw_agent_id: string | null;
  team_id: number | null;
  prompt: string;
  schedule_type: ScheduleType;
  schedule_value: string;
  start_at: string | null;
  end_at: string | null;
  is_enabled: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

/** Body for `POST /routines`. */
export interface RoutineCreate {
  name: string;
  agent_id?: number;
  openclaw_agent_id?: string | null;
  team_id?: number | null;
  prompt: string;
  schedule_type: ScheduleType;
  schedule_value?: string;
  start_at?: string | null;
  end_at?: string | null;
  is_enabled?: boolean;
}

export type RoutineUpdate = Partial<RoutineCreate>;

/** A logged routine execution. */
export interface RoutineRun {
  id: number;
  routine_id: number;
  trigger: string;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  output: string;
  document_path: string | null;
  error: string | null;
  created_at: string;
}

/** A routine with its recent runs (from `GET /routines/{id}`). */
export interface RoutineDetail extends Routine {
  recent_runs: RoutineRun[];
}

/** A calendar event (from `GET /calendar/events`). */
export interface CalendarEvent {
  routine_id: number;
  routine_name: string;
  type: string; // "scheduled" | "success" | "error" | "missed"
  time: string;
  status: string;
  message: string | null;
}

/** Response from `GET /calendar/events`. */
export interface CalendarEventsResponse {
  events: CalendarEvent[];
}

