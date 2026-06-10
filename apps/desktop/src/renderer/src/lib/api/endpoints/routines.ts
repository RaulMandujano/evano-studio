/** routines endpoints. */
import { requestJson } from "../http";
import type {
  Routine,
  RoutineCreate,
  RoutineDetail,
  RoutineUpdate,
  RoutineRun,
  CalendarEventsResponse,
} from "../types";


/** `GET /routines` — list routines. */
export function getRoutines(): Promise<Routine[]> {
  return requestJson<Routine[]>("/routines");
}

/** `POST /routines` — create a routine. */
export function createRoutine(body: RoutineCreate): Promise<Routine> {
  return requestJson<Routine>("/routines", { method: "POST", body });
}

/** `GET /routines/{id}` — routine detail with recent runs. */
export function getRoutineDetail(id: number): Promise<RoutineDetail> {
  return requestJson<RoutineDetail>(`/routines/${id}`);
}

/** `PUT /routines/{id}` — update a routine. */
export function updateRoutine(id: number, body: RoutineUpdate): Promise<Routine> {
  return requestJson<Routine>(`/routines/${id}`, { method: "PUT", body });
}

/** `DELETE /routines/{id}` — delete a routine. */
export function deleteRoutine(id: number): Promise<{ ok: boolean }> {
  return requestJson<{ ok: boolean }>(`/routines/${id}`, { method: "DELETE" });
}

/** `POST /routines/{id}/run-now` — run immediately (longer timeout). */
export function runRoutineNow(id: number): Promise<RoutineRun> {
  return requestJson<RoutineRun>(`/routines/${id}/run-now`, {
    method: "POST",
    timeoutMs: 120_000,
  });
}

/** `GET /calendar/events` — events for the calendar. */
export function getCalendarEvents(): Promise<CalendarEventsResponse> {
  return requestJson<CalendarEventsResponse>("/calendar/events");
}

