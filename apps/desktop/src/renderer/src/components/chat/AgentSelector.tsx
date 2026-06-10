import type { Agent } from "../../lib/api/types";

interface AgentSelectorProps {
  agents: Agent[];
  selectedId: number | null;
  disabled?: boolean;
  onSelect: (id: number) => void;
}

/** Dropdown to choose which agent to chat with. */
export function AgentSelector({ agents, selectedId, disabled, onSelect }: AgentSelectorProps) {
  return (
    <label className="agent-selector">
      <span className="agent-selector-label">Agent</span>
      <select
        className="select"
        value={selectedId ?? ""}
        disabled={disabled || agents.length === 0}
        onChange={(e) => onSelect(Number(e.target.value))}
      >
        {agents.length === 0 ? <option value="">No agents</option> : null}
        {agents.map((agent) => (
          <option key={agent.id} value={agent.id}>
            {agent.name} · {agent.model_name}
            {agent.is_enabled ? "" : " (disabled)"}
          </option>
        ))}
      </select>
    </label>
  );
}
