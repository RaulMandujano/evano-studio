import type { FC } from "react";
import type { ViewId } from "../navigation";

import { EasyStartView } from "./EasyStartView";
import { OpenClawView } from "./OpenClawView";
import { OpenClawDashboardView } from "./OpenClawDashboardView";
import { OpenClawAgentsView } from "./OpenClawAgentsView";
import { TeamsView } from "./teams/TeamsView";
import { OfficeView } from "./OfficeView";
import { OrgChartView } from "./OrgChartView";
import { ChatsView } from "./ChatsView";
import { AfmView } from "./AfmView";
import { ChannelsView } from "./ChannelsView";
import { DashboardView } from "./DashboardView";
import { ModelsView } from "./ModelsView";
import { AgentsView } from "./AgentsView";
import { ChatView } from "./ChatView";
import { DocumentsView } from "./DocumentsView";
import { KnowledgeBaseView } from "./KnowledgeBaseView";
import { ImagesView } from "./ImagesView";
import { ToolsView } from "./ToolsView";
import { RoutinesView } from "./RoutinesView";
import { CalendarView } from "./CalendarView";
import { SettingsView } from "./SettingsView";
import { LogsView } from "./LogsView";

/** Maps every navigation id to the component that renders it. */
export const views: Record<ViewId, FC> = {
  "easy-start": EasyStartView,
  openclaw: OpenClawView,
  "openclaw-agents": OpenClawAgentsView,
  teams: TeamsView,
  office: OfficeView,
  "org-chart": OrgChartView,
  chats: ChatsView,
  afm: AfmView,
  "openclaw-dashboard": OpenClawDashboardView,
  channels: ChannelsView,
  dashboard: DashboardView,
  models: ModelsView,
  agents: AgentsView,
  chat: ChatView,
  documents: DocumentsView,
  knowledge: KnowledgeBaseView,
  images: ImagesView,
  tools: ToolsView,
  routines: RoutinesView,
  calendar: CalendarView,
  settings: SettingsView,
  logs: LogsView,
};
