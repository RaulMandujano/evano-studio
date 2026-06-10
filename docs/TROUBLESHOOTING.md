# Troubleshooting

Evano Studio is **alpha** and entirely local — most issues are about local
services not running. Nothing here involves the cloud.

## Agent Engine offline

The local backend isn't running. Start it (see [AGENT_ENGINE.md](AGENT_ENGINE.md)),
or use **Settings → Local services → Start** if auto-start is configured. The
Dashboard's Agent Engine card and the Settings page show live status.

## Ollama not detected

Make sure Ollama is installed and running (`http://localhost:11434`). The
Dashboard/Settings show its status; the Models page links to the official
download. See [OLLAMA.md](OLLAMA.md).

## No models installed / chat fails with HTTP 404

Install a model from the **Models** page. Set the agent's model to an **exact
installed tag** (e.g. `gemma3:4b`) — a family alias may not match.

## Knowledge base unavailable

ChromaDB couldn't initialize locally, or the first embedding-model download needs
network access (a ~80 MB local model, one time). The app shows a clear local-setup
message and **never** falls back to the cloud. See
[RAG_WITH_CHROMADB.md](RAG_WITH_CHROMADB.md).

## Images won't generate

Confirm ComfyUI is installed, running, reachable at the configured URL, and that
the agent is **image-enabled**. See [COMFYUI_INTEGRATION.md](COMFYUI_INTEGRATION.md).

## Routines didn't run

Routines run **only while Evano Studio is open**. Runs missed while the app was
closed are recorded as **"missed"**, not run late. Check the routine's run history
and the Calendar.

## Reporting a problem

Use **Logs → Export support bundle**. It collects non-sensitive diagnostics
(versions, statuses, model names, recent logs) and **excludes** chat messages,
document contents, routine prompts, and secrets by default. The file is written
locally and not uploaded — attach it to a bug report (see the issue template).
