import { Badge, type BadgeTone } from "./Badge";

export interface StatusCardProps {
  icon: string;
  title: string;
  status: string;
  /** Visual tone for the status pill. */
  tone?: BadgeTone;
  /** Optional one-line, honest description of what this will do later. */
  hint?: string;
}

/** A single dashboard status tile. Read-only — reflects state, does nothing. */
export function StatusCard({ icon, title, status, tone = "neutral", hint }: StatusCardProps) {
  return (
    <div className="status-card">
      <div className="status-card-top">
        <span className="status-card-icon" aria-hidden="true">
          {icon}
        </span>
        <Badge tone={tone} dot>
          {status}
        </Badge>
      </div>
      <h3 className="status-card-title">{title}</h3>
      {hint ? <p className="status-card-hint">{hint}</p> : null}
    </div>
  );
}
