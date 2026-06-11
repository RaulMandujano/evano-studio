/**
 * Navigation registry for the desktop shell.
 *
 * Single source of truth for the sidebar. Each view id maps to a React
 * component in `views/index.ts`. Keeping this typed means adding a view is a
 * compile-time-checked change.
 */

export type ViewId =
  | "easy-start"
  | "openclaw"
  | "openclaw-agents"
  | "chats"
  | "customer-service"
  | "teams"
  | "org-chart"
  | "office"
  | "openclaw-dashboard"
  | "channels"
  | "dashboard"
  | "models"
  | "agents"
  | "chat"
  | "afm"
  | "documents"
  | "knowledge"
  | "images"
  | "tools"
  | "routines"
  | "calendar"
  | "settings"
  | "logs";

export interface NavItem {
  id: ViewId;
  label: string;
  icon: string;
}

export interface NavGroup {
  title: string;
  items: NavItem[];
}

export const navGroups: NavGroup[] = [
  {
    title: "Start here",
    items: [
      { id: "openclaw", label: "Get Started", icon: "🦞" },
      { id: "openclaw-agents", label: "Agents", icon: "🤖" },
      { id: "chats", label: "Chats", icon: "💬" },
      { id: "customer-service", label: "Customer Service", icon: "🎧" },
      { id: "teams", label: "Teams", icon: "🤝" },
      { id: "org-chart", label: "Org Chart", icon: "🏛️" },
      { id: "office", label: "Office", icon: "🏢" },
      { id: "openclaw-dashboard", label: "Dashboard", icon: "🖥️" },
      { id: "channels", label: "Channels", icon: "🔌" },
    ],
  },
  {
    title: "Overview",
    items: [{ id: "dashboard", label: "Dashboard", icon: "🏠" }],
  },
  {
    title: "AI",
    items: [{ id: "models", label: "Models", icon: "🧠" }],
  },
  {
    title: "Workspace",
    items: [
      { id: "afm", label: "AFM", icon: "🗂️" },
      { id: "documents", label: "Documents", icon: "📄" },
      { id: "knowledge", label: "Knowledge Base", icon: "📚" },
      { id: "images", label: "Images", icon: "🎨" },
      { id: "tools", label: "Tools", icon: "🛠️" },
    ],
  },
  {
    title: "Automation",
    items: [
      { id: "routines", label: "Routines", icon: "🔁" },
      { id: "calendar", label: "Calendar", icon: "🗓️" },
    ],
  },
  {
    title: "Advanced",
    items: [{ id: "easy-start", label: "Evano Engine", icon: "🚀" }],
  },
  {
    title: "System",
    items: [
      { id: "settings", label: "Settings", icon: "⚙️" },
      { id: "logs", label: "Logs", icon: "📋" },
    ],
  },
];

/**
 * Views that are reachable (e.g. from the Evano Engine advanced wizard) but
 * intentionally NOT in the sidebar — the built-in engine predates OpenClaw.
 */
const hiddenNavItems: NavItem[] = [
  { id: "agents", label: "Built-in Agents", icon: "🤖" },
  { id: "chat", label: "Built-in Chat", icon: "💬" },
];

/** Flat lookup of id -> nav item (label + icon), incl. hidden-but-reachable views. */
export const navItemsById: Record<ViewId, NavItem> = [...navGroups.flatMap((group) => group.items), ...hiddenNavItems]
  .reduce(
    (acc, item) => {
      acc[item.id] = item;
      return acc;
    },
    {} as Record<ViewId, NavItem>,
  );
