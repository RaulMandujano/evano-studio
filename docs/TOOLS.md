# Tools — safe local actions for agents

Tools are how Evano Studio agents take **real actions on your computer** —
safely, locally, and visibly. The design goal is a useful local AI *employee*,
not an unrestricted AI: every tool is curated, confined to your workspace, and
logged.

## Principles (hard rules)

- **No arbitrary shell, no `sudo`, no terminal execution, no system changes.**
  The tool catalog is a fixed, curated list in code — there is no "run command"
  tool and no way for an agent to invent one.
- **Workspace-confined.** File tools can only read/write inside the configured
  [workspace](DOCUMENTS.md). Directory traversal (`..`, absolute paths, symlinks
  out) is blocked by `app/core/paths.py`.
- **Deny-by-default permissions.** An agent can only run a tool that has been
  explicitly enabled for it (per-agent `enabled_tools`). No grant → no action.
- **Everything is logged.** Each execution (manual or agent-initiated) is
  recorded in the `tool_execution_logs` table with metadata only — never file
  contents or other private payloads.
- **No hidden execution.** Tools never run on their own. They run from the Tools
  test page, or when a chat message is a clear, deterministic tool request (see
  *Agent tool calling* below). There is no autonomous multi-step loop.

## Architecture

| Piece | File | Responsibility |
| --- | --- | --- |
| Registry | `app/tools/registry.py` | The static catalog (`ToolSpec`/`ToolParam`). Source of truth for what exists. |
| Service | `app/services/tool_service.py` | Executes a tool with validation, permission gating, workspace confinement, and logging. |
| Intent | `app/tools/intent.py` | Deterministic (regex, English + Spanish) mapping of a chat message → at most one tool call, plus an optional content directive. |
| Orchestrator | `app/services/tool_orchestrator.py` | Decides whether a chat message is a tool request, enforces permission, resolves content, executes, and writes the chat reply. |
| Permissions | `Agent.enabled_tools` (JSON column) | Which tools each agent may use. |
| API | `app/api/tools.py` | `GET /tools`, `POST /tools/test`, `GET /tools/logs`. |
| Logging | `ToolExecutionLog` model | Append-only, metadata-only audit trail. |

## Tools (V1)

File tools (workspace-confined):

- `create_folder` — create a folder (optionally inside a subfolder).
- `list_files` — list files/folders in the workspace or a subfolder.
- `create_text_file` — create a new text file (fails if it exists).
- `read_text_file` — read a UTF-8 text file (`.txt/.md/.html`, 1 MB cap).
- `write_text_file` — create or overwrite a text file.
- `search_workspace` — search text files by name and content.

Document / knowledge / image tools:

- `create_markdown_document`, `create_text_report` — write documents via the
  [documents](DOCUMENTS.md) service.
- `create_word_document`, `create_pdf_document` — generate **real** `.docx` and
  `.pdf` binary files (python-docx / fpdf2) in the workspace. Title required,
  content optional (supports `#` headings and `-` bullets). Workspace-confined,
  no approval needed.
- `search_knowledge_base` — semantic search over the local
  [knowledge base](RAG_WITH_CHROMADB.md) (graceful if unavailable).
- `generate_image_prompt` — compose an image prompt (text only; no generation).

Back-compat root-only tools (`list_allowed_files`, `read_allowed_text_file`)
remain for agents configured before the workspace had a folder structure.

Writable extensions are limited to text formats (`.txt/.md/.markdown/.html/.csv/.json`).

## Computer control (opt-in, approval-gated)

Beyond the workspace, agents can be granted **computer-control** tools:

- `open_application` — open an installed app (e.g. Safari, Calculator).
- `open_url` — open an http/https URL in the default browser.
- `run_command` — run a shell command and return its output.

These are powerful and **off by default** (deny-by-default per agent). They carry
`requires_approval = true`, which changes how they run:

- **From an agent (chat):** the agent never runs them on its own. It creates a
  **pending action**; the chat shows the exact app/URL/command and an
  *Allow / Deny* card. Only on **Allow** does it run (`POST /actions/{id}/approve`).
  This is the human-in-the-loop model (`app/db/models.py:PendingAction`,
  `app/api/actions.py`, `AgentLoop._create_pending`).
- **From the Tools page (manual):** runs directly — that click is already a
  human action.

Safeguards: `sudo` (privilege escalation) is blocked; `run_command` has a
timeout and bounded captured output; every run is logged in
`tool_execution_logs`. Computer-control tools are **not** workspace-confined (by
nature), so grant them deliberately — especially for non-technical users, keep
approval on.

## File-tool result contract (verified writes)

The file-*creation* tools (`create_text_file`, `write_text_file`,
`create_markdown_document`, `create_text_report`) **verify the file exists on
disk after writing** and return a uniform contract. If verification fails, the
tool raises an error (reported as a failure in chat and on the Tools page) — the
agent can never *claim* a file was created when it wasn't.

```jsonc
{
  "success": true,
  "tool_name": "create_text_file",
  "name": "prueba.txt",
  "relative_path": "prueba.txt",                 // relative to the active workspace
  "absolute_path": "/Users/you/EvanoWorkspace/prueba.txt",
  "bytes_written": 10,
  "verified_exists": true,
  "message": "Created prueba.txt (10 bytes) in the workspace."
}
```

(`create_folder` keeps its own simpler result and is unchanged.)

## One workspace, one source of truth

All file operations resolve against **`effective_workspace()`** — the user's
configured `workspace_dir` setting, or the default if none is set. The desktop's
"Open folder" buttons (Settings, Tools, Service manager, and the per-file
"Open folder" action in chat) open the path the **backend reports**
(`GET /workspace/status`), so what you write and what you open are always the
same folder. The active workspace path is shown on both the Settings and Tools
pages.

## Agent tool calling (the brain)

There is **one** agent turn used by every channel (desktop chat and Discord):
`app/services/agent_runner.py` → `run_agent_turn(...)`. It chooses how to act:

1. **Native tool-calling loop (preferred)** — `app/services/agent_loop.py`.
   For agents with tools enabled and a model that supports tool calling (e.g.
   `gemma4`, `llama3.2`), the **model decides** which tools to call; the backend
   executes each through `ToolService` (deny-by-default, workspace-confined,
   verified, logged), feeds the real result back, and loops (bounded to a few
   steps) until the model gives a final answer. This is the OpenClaw-style
   behavior — kept inside Evano's safety model (no shell, no computer control).
   Only the agent's enabled tools are exposed to the model.
2. **Deterministic router (fallback)** — `app/services/tool_orchestrator.py`.
   Used when the model can't tool-call (e.g. `gemma3:4b`) or Ollama is offline,
   and for tool-less agents (to give a clear "enable the tool" message rather
   than letting the model pretend). Details below.
3. **Plain chat** — when no tool action applies.

### The deterministic router

The router decides — without asking the model — whether your message is a tool
request:

1. **Detect intent** (`app/tools/intent.py`) — narrow regexes in English *and*
   Spanish. Examples that resolve to a tool:
   - "Create a folder called Clients" / "crea una carpeta llamada Clientes" → `create_folder`
   - "crea un documento llamado prueba.md que diga Hola Evano" → `create_markdown_document` (literal content)
   - "create a document about local AI" → `create_markdown_document` (model-generated content)
   - "save this as a document" → `create_markdown_document` (saves the previous reply)
   - "create a report about Q1" → `create_text_report`
   - "crea un archivo llamado notes.txt que diga hola" → `create_text_file`
   - "list my workspace files" / "lista mis archivos" → `list_files`
   - "read the file notes.txt" / "lee el archivo notes.txt" → `read_text_file`
   - "search the workspace for invoice" / "busca en el workspace por factura" → `search_workspace`
2. **Enforce permission** — if the agent doesn't have that tool enabled, the
   orchestrator returns a clear "no permission" reply (and logs the denial). It
   does **not** silently fall through.
3. **Resolve content** for document/file tools, three ways:
   - *literal* — the user gave the text ("that says …" / "que diga …").
   - *generate* — the model writes content about a topic ("about …" / "sobre …").
     This is the **only** place the LLM is involved, and only to produce the
     document body — never to decide or execute the tool.
   - *from history* — "save this as a document" stores the previous reply.
4. **Execute** via `ToolService` (workspace-confined, logged).
5. **Reply** with exactly what was done, including the workspace-relative path.

The detector is intentionally conservative (it only fires on imperative
phrasings tied to a known object like *folder/document/file/report*), so ordinary
conversation is never hijacked. Agents with **no** tools enabled are treated as
chat-only and never trigger tool actions. There is no planning loop and no
chaining — one message maps to at most one tool call.

## Granting tools to an agent

In the desktop app, open **Agents → (an agent) → Tool Permissions** and tick the
tools to enable. Programmatically:

```
PUT /agents/{id}/tools   { "enabled_tools": ["create_folder", "list_files"] }
```

Unknown tool ids are rejected (`400 unknown_tool`).

## Testing tools

Use the **Tools** page in the desktop app to run any tool with custom
parameters and watch the result, then review the **Tool execution log** below
it. The same is available over HTTP via `POST /tools/test` and `GET /tools/logs`.

See also: [SECURITY.md](SECURITY.md), [DOCUMENTS.md](DOCUMENTS.md),
[EASY_START.md](EASY_START.md).
