import { useState } from "react";
import { Sidebar } from "./components/layout/Sidebar";
import { Topbar } from "./components/layout/Topbar";
import { views } from "./views";
import type { ViewId } from "./navigation";
import { NavigateProvider } from "./navigation-context";

/**
 * App shell. Holds the currently selected view in state and renders the matching
 * component. This is intentionally a simple in-app view switcher (no router
 * dependency) — appropriate for a single-window desktop app at this stage.
 *
 * New users land on the OpenClaw guided setup (the main "easy install" flow);
 * views can navigate to each other via the navigation context.
 */
export function App() {
  const [active, setActive] = useState<ViewId>("openclaw");
  const ActiveView = views[active];

  return (
    <NavigateProvider navigate={setActive}>
      <div className="app">
        <Sidebar active={active} onNavigate={setActive} />
        <div className="app-main">
          <Topbar active={active} />
          <main className="app-content">
            <ActiveView />
          </main>
        </div>
      </div>
    </NavigateProvider>
  );
}
