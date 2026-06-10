import { useEffect, useRef, useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { AgentSelector } from "../components/chat/AgentSelector";
import { MessageList, type UiMessage, type UiToolFile } from "../components/chat/MessageList";
import { MessageInput } from "../components/chat/MessageInput";
import { ChatError } from "../components/chat/ChatError";
import { ApprovalCard } from "../components/chat/ApprovalCard";
import { AgentImagePanel } from "../components/chat/AgentImagePanel";
import { Button } from "../components/ui/Button";
import { useBackendResource } from "../hooks/useBackendResource";
import { backendApi } from "../lib/api/client";
import type {
  ActionResolveResponse,
  Agent,
  AgentChatMessage,
  ComfyUIStatus,
  PendingAction,
  ToolExecution,
} from "../lib/api/types";

/** Pull file info out of a tool execution result (file-creation tools only). */
function extractToolFile(exec: ToolExecution | null): UiToolFile | undefined {
  if (!exec || !exec.ok || !exec.result || typeof exec.result !== "object") return undefined;
  const r = exec.result as Record<string, unknown>;
  const absolutePath = typeof r.absolute_path === "string" ? r.absolute_path : "";
  if (!absolutePath) return undefined; // only file tools return an absolute path
  const relativePath = typeof r.relative_path === "string" ? r.relative_path : "";
  const name = typeof r.name === "string" ? r.name : relativePath || absolutePath;
  return { name, relativePath: relativePath || name, absolutePath };
}

/**
 * Chat page. Conversations are kept locally in memory (per agent, for this
 * session only) — simple and clean, no persistence layer for now.
 */
export function ChatView() {
  const agentsRes = useBackendResource<Agent[]>(backendApi.getAgents);
  const comfyuiRes = useBackendResource<ComfyUIStatus>(backendApi.getComfyUIStatus);
  const agents = agentsRes.data ?? [];
  const comfyuiReachable = Boolean(comfyuiRes.data?.enabled && comfyuiRes.data?.reachable);

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [conversations, setConversations] = useState<Record<number, UiMessage[]>>({});
  const [errors, setErrors] = useState<Record<number, string | null>>({});
  const [sendingAgentId, setSendingAgentId] = useState<number | null>(null);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [savingId, setSavingId] = useState<string | null>(null);
  const [showImagePanel, setShowImagePanel] = useState(false);
  const [pendingActions, setPendingActions] = useState<Record<number, PendingAction | null>>({});

  const idCounter = useRef(0);
  const nextId = () => `m${(idCounter.current += 1)}`;

  // Approve/deny a proposed computer action, then show what happened.
  const resolveAction = async (
    agentId: number,
    outcome: { approved: boolean; result: ActionResolveResponse | null; error?: string },
  ) => {
    setPendingActions((prev) => ({ ...prev, [agentId]: null }));
    let text: string;
    if (outcome.error) {
      text = `⚠️ ${outcome.error}`;
    } else if (!outcome.approved) {
      text = "❌ Acción rechazada / Action denied.";
    } else if (outcome.result?.ok) {
      const r = outcome.result.execution?.result as Record<string, unknown> | undefined;
      const out = (r?.stdout as string) || (r?.message as string) || "Done.";
      text = `✅ ${out}`;
    } else {
      text = `⚠️ ${outcome.result?.message ?? "The action failed."}`;
    }
    setConversations((prev) => ({
      ...prev,
      [agentId]: [...(prev[agentId] ?? []), { id: nextId(), role: "assistant", content: text }],
    }));
  };

  // Auto-select the first agent once the list loads.
  useEffect(() => {
    if (selectedId === null && agents.length > 0) {
      setSelectedId(agents[0].id);
    }
  }, [agents, selectedId]);

  const selectedAgent = agents.find((a) => a.id === selectedId) ?? null;
  const messages = selectedId !== null ? (conversations[selectedId] ?? []) : [];
  const error = selectedId !== null ? errors[selectedId] : null;
  const isSending = sendingAgentId !== null;

  const send = async (text: string) => {
    if (selectedAgent === null || isSending) return;
    const agentId = selectedAgent.id;

    // History = prior turns in this conversation (before the new message).
    const history: AgentChatMessage[] = (conversations[agentId] ?? []).map((m) => ({
      role: m.role,
      content: m.content,
    }));

    const userMessage: UiMessage = { id: nextId(), role: "user", content: text };
    setConversations((prev) => ({
      ...prev,
      [agentId]: [...(prev[agentId] ?? []), userMessage],
    }));
    setErrors((prev) => ({ ...prev, [agentId]: null }));
    setSendingAgentId(agentId);

    try {
      const result = await backendApi.chatWithAgent(agentId, text, history);
      if (result.ok && result.reply) {
        const sources = (result.sources ?? [])
          .map((s) => s.file_name ?? s.title)
          .filter((label): label is string => Boolean(label));
        const reply: UiMessage = {
          id: nextId(),
          role: "assistant",
          content: result.reply,
          sources: sources.length > 0 ? sources : undefined,
          tool: result.tool_execution ? result.tool_execution.tool_name : undefined,
          toolFile: extractToolFile(result.tool_execution),
        };
        setConversations((prev) => ({
          ...prev,
          [agentId]: [...(prev[agentId] ?? []), reply],
        }));
        // The agent proposed a sensitive action that needs approval.
        if (result.pending_action) {
          setPendingActions((prev) => ({ ...prev, [agentId]: result.pending_action }));
        }
      } else {
        setErrors((prev) => ({
          ...prev,
          [agentId]: result.message ?? "The model didn't return a response.",
        }));
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Request failed.";
      setErrors((prev) => ({ ...prev, [agentId]: message }));
    } finally {
      setSendingAgentId((current) => (current === agentId ? null : current));
    }
  };

  const saveResponse = async (message: UiMessage) => {
    if (selectedAgent === null || savingId) return;
    setSavingId(message.id);
    try {
      const title = `${selectedAgent.name} — ${new Date().toLocaleString()}`;
      await backendApi.saveAgentResponse({
        title,
        content: message.content,
        agent_id: selectedAgent.id,
        file_type: "md",
      });
      setSavedIds((prev) => new Set(prev).add(message.id));
    } catch (err) {
      const text = err instanceof Error ? err.message : "Couldn't save the document.";
      setErrors((prev) => ({ ...prev, [selectedAgent.id]: text }));
    } finally {
      setSavingId(null);
    }
  };

  const renderBody = () => {
    if (agentsRes.state === "checking") {
      return <p className="muted">Loading agents…</p>;
    }
    if (agentsRes.state !== "ready") {
      return (
        <Card className="notice-card">
          <h3>Can&apos;t reach the local backend</h3>
          <p className="muted">Start the Agent Engine, then refresh.</p>
        </Card>
      );
    }
    if (agents.length === 0) {
      return (
        <Card className="notice-card">
          <h3>No agents yet</h3>
          <p className="muted">Create an agent on the Agents page, then come back to chat.</p>
        </Card>
      );
    }

    return (
      <div className="chat-page">
        <div className="chat-toolbar">
          <AgentSelector
            agents={agents}
            selectedId={selectedId}
            disabled={isSending}
            onSelect={setSelectedId}
          />
          {selectedAgent && !selectedAgent.is_enabled ? (
            <Badge tone="neutral" dot>
              Disabled
            </Badge>
          ) : null}
          {selectedAgent ? (
            <Button onClick={() => setShowImagePanel((v) => !v)}>
              {showImagePanel ? "Hide image tools" : "🎨 Image tools"}
            </Button>
          ) : null}
        </div>

        <MessageList
          messages={messages}
          loading={sendingAgentId === selectedId && selectedId !== null}
          onSaveAssistant={saveResponse}
          savedIds={savedIds}
          savingId={savingId}
          emptyHint={
            selectedAgent
              ? `Chatting with ${selectedAgent.name} (${selectedAgent.model_name}).`
              : "Select an agent to begin."
          }
        />

        {error ? (
          <ChatError
            message={error}
            onDismiss={() =>
              selectedId !== null && setErrors((prev) => ({ ...prev, [selectedId]: null }))
            }
          />
        ) : null}

        {selectedId !== null && pendingActions[selectedId] ? (
          <ApprovalCard
            action={pendingActions[selectedId]!}
            onResolved={(outcome) => resolveAction(selectedId, outcome)}
          />
        ) : null}

        <MessageInput disabled={isSending || selectedAgent === null} onSend={send} />

        {showImagePanel && selectedAgent ? (
          <Card className="card-spaced">
            <AgentImagePanel agent={selectedAgent} comfyuiReachable={comfyuiReachable} />
          </Card>
        ) : null}
      </div>
    );
  };

  return (
    <div className="view">
      <PageHeader
        icon="💬"
        title="Chat"
        subtitle="Chat with your local agents. Conversations are kept in memory for this session."
        badge={<Badge tone="alpha">Live</Badge>}
      />
      {renderBody()}
    </div>
  );
}
