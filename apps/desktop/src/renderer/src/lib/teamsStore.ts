/**
 * Team run store — lives OUTSIDE the React tree so a workflow run (and its
 * in-progress state) survives switching tabs. The view subscribes via
 * useSyncExternalStore; the relay loop keeps running even when TeamsView is
 * unmounted, and the latest progress is shown when the user returns.
 */
import { backendApi } from "./api/client";

export type StepStatus = "pending" | "working" | "done" | "empty" | "error";

export interface RunStep {
  agentId: string;
  agentName: string;
  instruction: string;
  status: StepStatus;
  output: string;
}

export interface RunState {
  teamId: number | null;
  teamName: string;
  steps: RunStep[];
  running: boolean;
  note: string | null;
}

interface TeamDef {
  id: number;
  name: string;
  steps: { agent_id: string; instruction: string }[];
  working_file?: string | null;
}

let state: RunState = { teamId: null, teamName: "", steps: [], running: false, note: null };
const listeners = new Set<() => void>();

function emit(): void {
  listeners.forEach((l) => l());
}
function set(patch: Partial<RunState>): void {
  state = { ...state, ...patch };
  emit();
}

function randomId(): string {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID().slice(0, 8)
    : Math.random().toString(36).slice(2, 10);
}

const DIRECTIVE =
  "\nIMPORTANT: Reply with ONLY the finished result of your task — the actual deliverable. " +
  "Do NOT describe your plan, do NOT say \"I will…\", do NOT ask questions or add preamble. Just produce the result.";

function fileNote(workingFile: string | null | undefined, first: boolean): string {
  if (!workingFile) return "";
  return first
    ? `\nUse your file tools to write your result into the file \`${workingFile}\` in your workspace (create it).`
    : `\nThe file \`${workingFile}\` is already in your workspace (your teammate left it there). Read it, do your task, and SAVE your changes back to \`${workingFile}\` with your file tools.`;
}

function firstMessage(team: string, agent: string, instruction: string, input: string, workingFile?: string | null): string {
  return [
    `You are "${agent}", one member of the team "${team}". The team completes a task as a relay.`,
    instruction ? `Your task: ${instruction}` : "Do your part of the team's work.",
    input ? `\nInput / goal to start from:\n${input}` : "",
    fileNote(workingFile, true),
    DIRECTIVE,
  ].filter(Boolean).join("\n");
}

function handoffMessage(team: string, agent: string, instruction: string, prevName: string, prevOutput: string, workingFile?: string | null): string {
  return [
    `You are "${agent}", one member of the team "${team}".`,
    instruction ? `Your task: ${instruction}` : "Continue the team's work.",
    `\nYour teammate "${prevName}" already did their part and gave you this result:\n---\n${prevOutput}\n---`,
    "\nDo YOUR task using their result above as your input.",
    fileNote(workingFile, false),
    DIRECTIVE,
  ].filter(Boolean).join("\n");
}

/** One agent turn, retried once if it comes back empty (robustness). */
async function runStep(
  id: string,
  message: string,
  base: string,
  activityTask: string,
): Promise<{ reply: string; failed: boolean }> {
  let reply = "";
  let failed = false;
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const r = await backendApi.chatOpenClawAgent(id, message, `${base}-${attempt}`, {
        task: activityTask,
        kind: "team",
      });
      reply = r.ok ? r.reply : r.message || "No reply.";
      failed = !r.ok;
    } catch (e) {
      return { reply: e instanceof Error ? e.message : "Request failed.", failed: true };
    }
    const empty = failed || !reply.trim() || reply.trim() === "(no reply)";
    if (!empty) return { reply, failed: false };
  }
  return { reply, failed };
}

export const teamsStore = {
  subscribe(cb: () => void): () => void {
    listeners.add(cb);
    return () => {
      listeners.delete(cb);
    };
  },
  getSnapshot(): RunState {
    return state;
  },
  reset(): void {
    if (state.running) return;
    set({ teamId: null, teamName: "", steps: [], running: false, note: null });
  },
  async run(team: TeamDef, input: string, names: Record<string, string>): Promise<void> {
    if (state.running) return;
    const nameOf = (id: string) => names[id] || id;
    if (team.steps.length < 2) return;

    const runId = randomId();
    set({
      teamId: team.id,
      teamName: team.name,
      note: null,
      running: true,
      steps: team.steps.map((s) => ({
        agentId: s.agent_id,
        agentName: nameOf(s.agent_id),
        instruction: s.instruction,
        status: "pending",
        output: "",
      })),
    });

    let context = "";
    let prevName = "";
    let prevId = "";
    for (let i = 0; i < team.steps.length; i++) {
      const { agent_id: id, instruction } = team.steps[i];
      set({ steps: state.steps.map((st, idx) => (idx === i ? { ...st, status: "working" } : st)) });
      // Pass the working file from the previous agent's folder into this one's.
      if (team.working_file && prevId) {
        try {
          await backendApi.handoffOpenClawFile({ from_agent_id: prevId, to_agent_id: id, file_name: team.working_file });
        } catch {
          /* best-effort — the agent prompt still references the file */
        }
      }
      const message =
        i === 0
          ? firstMessage(team.name, nameOf(id), instruction, input, team.working_file)
          : handoffMessage(team.name, nameOf(id), instruction, prevName, context, team.working_file);
      const stepLabel = `Team "${team.name}" — step ${i + 1}/${team.steps.length}: ${instruction || "do their part"}`;
      const { reply, failed } = await runStep(id, message, `evano-team-${runId}-${i}`, stepLabel);
      const empty = failed || !reply.trim() || reply.trim() === "(no reply)";
      set({
        steps: state.steps.map((st, idx) =>
          idx === i ? { ...st, status: empty ? (failed ? "error" : "empty") : "done", output: reply } : st,
        ),
      });
      if (empty) {
        set({
          running: false,
          note: failed
            ? `Stopped — ${nameOf(id)} couldn't respond. Make sure Ollama is running.`
            : `Stopped — ${nameOf(id)} returned no output (even after a retry). Give that step a clearer task.`,
        });
        return;
      }
      context = reply;
      prevName = nameOf(id);
      prevId = id;
    }
    set({ running: false, note: "✓ Workflow finished — final result below." });

    // File the run into the AFM Teams folder (best-effort, never blocks the UI).
    try {
      await backendApi.archiveTeamRun({
        team_name: team.name,
        steps: state.steps.map((st) => ({ agent_id: st.agentId, output: st.output })),
        final: context,
      });
    } catch {
      /* archiving is a convenience — the result is already on screen */
    }
  },
};
