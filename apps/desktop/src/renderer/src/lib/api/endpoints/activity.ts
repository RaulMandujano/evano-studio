/** activity endpoints — live "who is working on what" for the Office view. */
import { requestJson } from "../http";
import type { ActivitySnapshot } from "../types";

/** `GET /activity` — active work + recently finished work (in-memory presence). */
export function getActivitySnapshot(): Promise<ActivitySnapshot> {
  return requestJson<ActivitySnapshot>("/activity");
}
