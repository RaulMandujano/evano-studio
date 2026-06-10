import { navGroups, type ViewId } from "../../navigation";
import { useAppInfo } from "../../hooks/useAppInfo";

interface SidebarProps {
  active: ViewId;
  onNavigate: (id: ViewId) => void;
}

export function Sidebar({ active, onNavigate }: SidebarProps) {
  const info = useAppInfo();

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="sidebar-logo" aria-hidden="true">
          E
        </span>
        <span className="sidebar-brand-text">
          Evano <strong>Studio</strong>
        </span>
      </div>

      <nav className="sidebar-nav" aria-label="Primary">
        {navGroups.map((group) => (
          <div key={group.title} className="nav-group">
            <p className="nav-group-title">{group.title}</p>
            <ul>
              {group.items.map((item) => {
                const isActive = item.id === active;
                return (
                  <li key={item.id}>
                    <button
                      type="button"
                      className={`nav-item${isActive ? " is-active" : ""}`}
                      aria-current={isActive ? "page" : undefined}
                      onClick={() => onNavigate(item.id)}
                    >
                      <span className="nav-item-icon" aria-hidden="true">
                        {item.icon}
                      </span>
                      <span className="nav-item-label">{item.label}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <span className="badge badge--alpha">
          <span className="badge-dot" aria-hidden="true" />
          Alpha
        </span>
        <span className="sidebar-version">
          {info ? `v${info.version}` : "v0.0.0"}
        </span>
      </div>
    </aside>
  );
}
