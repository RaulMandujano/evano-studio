import { PageHeader } from "./PageHeader";
import { Card } from "./Card";
import { Badge } from "./Badge";

interface PlaceholderViewProps {
  icon: string;
  title: string;
  description: string;
  /** Honest list of what this section will do in a future phase. */
  planned: string[];
}

/**
 * Generic, honest placeholder for views that aren't built yet. It clearly says
 * the feature is upcoming and lists what it will do — no fake controls.
 */
export function PlaceholderView({ icon, title, description, planned }: PlaceholderViewProps) {
  return (
    <div className="view">
      <PageHeader
        icon={icon}
        title={title}
        subtitle={description}
        badge={<Badge tone="pending">Coming in a later phase</Badge>}
      />

      <Card className="placeholder-card">
        <p className="placeholder-lead">Planned for this section</p>
        <ul className="planned-list">
          {planned.map((item) => (
            <li key={item} className="planned-item">
              <span className="planned-dot" aria-hidden="true" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
        <p className="placeholder-note">
          This is the desktop shell only. No functionality is wired up here yet —
          it will be implemented in an upcoming phase.
        </p>
      </Card>
    </div>
  );
}
