import { useEffect, useState } from "react";
import { Card } from "../ui/Card";
import { Button } from "../ui/Button";
import { useBackendResource } from "../../hooks/useBackendResource";
import { backendApi } from "../../lib/api/client";
import type { ToolSpec, ToolTestResponse } from "../../lib/api/types";

/** A safe UI to run individual tools with custom params and view the result. */
export function ToolsTester() {
  const toolsRes = useBackendResource<ToolSpec[]>(backendApi.getTools);
  const tools = toolsRes.data ?? [];

  const [selectedId, setSelectedId] = useState<string>("");
  const [params, setParams] = useState<Record<string, string>>({});
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<ToolTestResponse | null>(null);

  // Default to the first tool once loaded.
  useEffect(() => {
    if (!selectedId && tools.length > 0) setSelectedId(tools[0].id);
  }, [tools, selectedId]);

  const selected = tools.find((t) => t.id === selectedId) ?? null;

  const onSelect = (id: string) => {
    setSelectedId(id);
    setParams({});
    setResult(null);
  };

  const run = async () => {
    if (!selected) return;
    setRunning(true);
    setResult(null);
    try {
      // Coerce integer params; leave others as strings.
      const payload: Record<string, unknown> = {};
      for (const p of selected.parameters) {
        const raw = params[p.name] ?? "";
        if (p.type === "integer" && raw !== "") payload[p.name] = Number(raw);
        else payload[p.name] = raw;
      }
      setResult(await backendApi.testTool(selected.id, payload));
    } catch (e) {
      setResult({ ok: false, result: null, message: e instanceof Error ? e.message : "Failed." });
    } finally {
      setRunning(false);
    }
  };

  return (
    <Card>
      <h3 className="settings-section-title">Tools test</h3>
      <p className="muted form-hint">
        Run a tool directly to see what it does. File tools stay inside the workspace.
      </p>

      <div className="form-row">
        <label htmlFor="tool-select">Tool</label>
        <select
          id="tool-select"
          className="select"
          value={selectedId}
          onChange={(e) => onSelect(e.target.value)}
        >
          {tools.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name} — {t.category}
            </option>
          ))}
        </select>
      </div>

      {selected ? (
        <>
          <p className="muted form-hint">{selected.description}</p>
          {selected.parameters.map((p) => (
            <div key={p.name} className="form-row">
              <label htmlFor={`param-${p.name}`}>
                {p.name}
                {p.required ? " *" : ""} <span className="muted">({p.type})</span>
              </label>
              {p.type === "text" ? (
                <textarea
                  id={`param-${p.name}`}
                  rows={3}
                  value={params[p.name] ?? ""}
                  onChange={(e) => setParams((prev) => ({ ...prev, [p.name]: e.target.value }))}
                  placeholder={p.description}
                />
              ) : (
                <input
                  id={`param-${p.name}`}
                  type={p.type === "integer" ? "number" : "text"}
                  value={params[p.name] ?? ""}
                  onChange={(e) => setParams((prev) => ({ ...prev, [p.name]: e.target.value }))}
                  placeholder={p.description}
                />
              )}
            </div>
          ))}
          <Button variant="primary" onClick={run} disabled={running}>
            {running ? "Running…" : "Run tool"}
          </Button>
        </>
      ) : null}

      {result ? (
        <div className="tool-result">
          <Badge ok={result.ok} />
          <pre className="doc-preview-content">
            {result.ok
              ? JSON.stringify(result.result, null, 2)
              : (result.message ?? "Failed.")}
          </pre>
        </div>
      ) : null}
    </Card>
  );
}

function Badge({ ok }: { ok: boolean }) {
  return (
    <span className={`badge ${ok ? "badge--ok" : "badge--danger"}`} style={{ marginBottom: 8 }}>
      <span className="badge-dot" aria-hidden="true" />
      {ok ? "Success" : "Failed"}
    </span>
  );
}
