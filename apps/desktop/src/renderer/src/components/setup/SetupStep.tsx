import type { BadgeTone } from "../ui/Badge";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";

export type StepState = "ok" | "warn" | "optional" | "error" | "pending";

export interface SetupStepAction {
  label: string;
  onClick: () => void;
}

export interface SetupStepProps {
  index: number;
  title: string;
  state: StepState;
  statusLabel: string;
  explanation: string;
  detail?: string;
  action?: SetupStepAction;
}

const STATE_META: Record<StepState, { icon: string; tone: BadgeTone }> = {
  ok: { icon: "✓", tone: "ok" },
  warn: { icon: "⚠", tone: "pending" },
  optional: { icon: "○", tone: "info" },
  error: { icon: "✕", tone: "danger" },
  pending: { icon: "…", tone: "neutral" },
};

/** One row in the Easy Start checklist. */
export function SetupStep({
  index,
  title,
  state,
  statusLabel,
  explanation,
  detail,
  action,
}: SetupStepProps) {
  const meta = STATE_META[state];
  return (
    <div className={`setup-step setup-step--${state}`}>
      <div className={`setup-step-marker setup-step-marker--${state}`} aria-hidden="true">
        {meta.icon}
      </div>
      <div className="setup-step-body">
        <div className="setup-step-head">
          <h3 className="setup-step-title">
            <span className="setup-step-num">{index}.</span> {title}
          </h3>
          <Badge tone={meta.tone} dot>
            {statusLabel}
          </Badge>
        </div>
        <p className="setup-step-explain muted">{explanation}</p>
        {detail ? <p className="setup-step-detail mono">{detail}</p> : null}
        {action ? (
          <div className="setup-step-action">
            <Button onClick={action.onClick}>{action.label}</Button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
