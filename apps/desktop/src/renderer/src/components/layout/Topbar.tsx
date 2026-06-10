import { useSyncExternalStore } from "react";
import type { ViewId } from "../../navigation";
import { navItemsById } from "../../navigation";
import { useNavigate } from "../../navigation-context";
import { teamsStore } from "../../lib/teamsStore";
import { Badge } from "../ui/Badge";

interface TopbarProps {
  active: ViewId;
}

export function Topbar({ active }: TopbarProps) {
  const current = navItemsById[active];
  const navigate = useNavigate();
  const teams = useSyncExternalStore(teamsStore.subscribe, teamsStore.getSnapshot);

  return (
    <header className="topbar">
      <div className="topbar-title">
        <span className="topbar-icon" aria-hidden="true">
          {current.icon}
        </span>
        {current.label}
      </div>
      <div className="topbar-actions">
        {teams.running && active !== "teams" ? (
          <button className="topbar-team-pill" onClick={() => navigate("teams")} title="A team is working — click to view">
            <span className="topbar-spinner" aria-hidden="true" /> Team working…
          </button>
        ) : null}
        <Badge tone="ok" dot>
          Free by default
        </Badge>
      </div>
    </header>
  );
}
