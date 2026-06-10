/**
 * Helpers for the Office view — turning the agent roster + live activity into
 * "workers" that sit at desks, hang out in the break room, or are off duty.
 */
import type { ActivityKind, Agent, AgentActivity, OpenClawAgent } from "./api/types";

/** One person in the office, regardless of where the agent runs. */
export interface OfficeWorker {
  /** Namespaced id matching the backend tracker: openclaw:<slug> | builtin:<id>. */
  key: string;
  name: string;
  avatar: string;
  source: "openclaw" | "builtin";
  /** What they're doing right now (undefined → in the break room). */
  working?: AgentActivity;
  /** Built-in agents can be disabled → shown as off duty. */
  offDuty: boolean;
}

const AVATARS = ["🧑‍💻", "👩‍💼", "🧑‍🔬", "👨‍🎨", "🧑‍🏫", "👩‍🔧", "🕵️", "🧑‍🚀", "👨‍🍳", "🧙"];

/** Deterministic avatar per agent so each worker always looks the same. */
export function avatarFor(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
  return AVATARS[hash % AVATARS.length];
}

export const KIND_META: Record<ActivityKind, { icon: string; label: string }> = {
  chat: { icon: "💬", label: "Chatting" },
  team: { icon: "🤝", label: "Team work" },
  routine: { icon: "🔁", label: "Routine" },
};

/** Merge the agent rosters with the live activity into office workers. */
export function buildWorkers(
  openclawAgents: OpenClawAgent[],
  builtinAgents: Agent[],
  active: AgentActivity[],
): OfficeWorker[] {
  const activeByKey = new Map(active.map((a) => [a.agent_id, a]));
  const workers: OfficeWorker[] = [];

  for (const agent of openclawAgents) {
    const key = `openclaw:${agent.id}`;
    workers.push({
      key,
      name: agent.name || agent.id,
      avatar: avatarFor(agent.name || agent.id),
      source: "openclaw",
      working: activeByKey.get(key),
      offDuty: false,
    });
  }
  for (const agent of builtinAgents) {
    const key = `builtin:${agent.id}`;
    workers.push({
      key,
      name: agent.name,
      avatar: avatarFor(agent.name),
      source: "builtin",
      working: activeByKey.get(key),
      offDuty: !agent.is_enabled,
    });
  }

  // Activity from agents not in the roster (e.g. just deleted) still gets a desk
  // while it runs, so nothing happening is ever invisible.
  for (const activity of active) {
    if (!workers.some((w) => w.key === activity.agent_id)) {
      workers.push({
        key: activity.agent_id,
        name: activity.agent_name,
        avatar: avatarFor(activity.agent_name),
        source: activity.agent_id.startsWith("builtin:") ? "builtin" : "openclaw",
        working: activity,
        offDuty: false,
      });
    }
  }
  return workers;
}

/** Short relative time, e.g. "just now", "3m ago", "2h ago". */
export function timeAgo(iso: string | null): string {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const seconds = Math.max(0, Math.floor((Date.now() - then) / 1000));
  if (seconds < 15) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}
