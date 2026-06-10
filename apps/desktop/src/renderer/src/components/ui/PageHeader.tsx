import type { ReactNode } from "react";

interface PageHeaderProps {
  icon?: string;
  title: string;
  subtitle?: string;
  badge?: ReactNode;
}

export function PageHeader({ icon, title, subtitle, badge }: PageHeaderProps) {
  return (
    <header className="page-header">
      <div className="page-header-main">
        <h1 className="page-title">
          {icon ? (
            <span className="page-title-icon" aria-hidden="true">
              {icon}
            </span>
          ) : null}
          {title}
        </h1>
        {badge ? <div className="page-header-badge">{badge}</div> : null}
      </div>
      {subtitle ? <p className="page-subtitle">{subtitle}</p> : null}
    </header>
  );
}
