# Ollama (Local AI Runtime)

Evano Studio uses [Ollama](https://ollama.com) to run AI models **locally** on
your machine. Ollama is a **local dependency you install yourself** — the app
never installs software silently. No paid API, no cloud.

## Install

1. Download Ollama from [ollama.com](https://ollama.com) and run the installer.
2. Start it — it serves a local API at `http://localhost:11434`.
3. In Evano Studio, the Dashboard/Settings show Ollama's status.

## Install a model

From the app's **Models** page (no terminal): pick a recommended model and click
Install, with live progress. Recommended: **Gemma** (3/4 class) when available;
also **Qwen** (coding), **Llama** (chat), **Mistral**, and **DeepSeek** distills.

Advanced users can also pull via terminal:

```bash
ollama pull gemma3:4b
```

> Use the **exact tag** (e.g. `gemma3:4b`) as an agent's model — a family name
> alone may not match an installed model.

## How Evano Studio integrates

- The backend talks to Ollama over its local HTTP API via a thin adapter
  (`services/ollama_service.py`); it's never bundled or reimplemented.
- Endpoints: model status, model list, recommended models, pull (with progress),
  and a chat test. Agents use it for chat and image-prompt generation.
- Timeouts keep the app responsive; if Ollama isn't running, you get a clear
  "not reachable" message rather than a hang.

## Hardware notes

Local models run on your hardware — more RAM/GPU means larger, faster models.
Small models run on modest machines; this is the trade-off for privacy and zero
cost. Configure the runtime URL or recommended model via `EVANO_OLLAMA_*` env vars
if needed.
