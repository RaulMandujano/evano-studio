import { createContext, useContext, type ReactNode } from "react";
import type { ViewId } from "./navigation";

/**
 * Lightweight navigation context so any view can switch the active page (e.g.
 * the Easy Start wizard linking to Models, Agents, or Settings). Avoids passing
 * an `onNavigate` prop through the `Record<ViewId, FC>` view registry.
 */
const NavigateContext = createContext<(view: ViewId) => void>(() => {});

export function NavigateProvider({
  navigate,
  children,
}: {
  navigate: (view: ViewId) => void;
  children: ReactNode;
}) {
  return <NavigateContext.Provider value={navigate}>{children}</NavigateContext.Provider>;
}

/** Returns a function that switches the active view. */
export function useNavigate(): (view: ViewId) => void {
  return useContext(NavigateContext);
}
