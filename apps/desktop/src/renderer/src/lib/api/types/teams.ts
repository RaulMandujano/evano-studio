/**
 * Agent teams (saved multi-agent workflows).
 *
 * Mirrors the FastAPI schemas in `services/agent-engine/app/schemas`.
 */

/** One step in a saved team workflow: an agent + its concrete task. */
export interface TeamStep {
  agent_id: string;
  instruction: string;
}

/** A saved multi-agent workflow. */
export interface Team {
  id: number;
  name: string;
  steps: TeamStep[];
  /** Optional file that flows agent→agent through the workflow. */
  working_file: string | null;
  created_at: string;
  updated_at: string;
}

/** Body for creating/updating a team. */
export interface TeamCreate {
  name: string;
  steps: TeamStep[];
  working_file?: string | null;
}
