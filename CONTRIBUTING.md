# Contributing to Evano Studio

Thanks for your interest! Evano Studio is a **free, open-source, local-first**
desktop app for running local AI agents. It's in **alpha** — contributions that
keep it clean, safe, and local are very welcome.

This is the quick-start contributor guide. For the deeper engineering standards
and the user-facing contributor doc, see
[docs/DEVELOPMENT_RULES.md](docs/DEVELOPMENT_RULES.md) and
[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

## Project layout (TL;DR)

- `apps/desktop` — Electron + React + TypeScript desktop app
- `apps/website` — Next.js website (evanostudio.com)
- `services/agent-engine` — Python + FastAPI local backend
- `packages/*` — shared TS types/config/UI
- `docs/` — architecture & reference docs (start at [docs/README.md](docs/README.md))

## Set up

Prerequisites: **Node.js ≥ 20**, **pnpm ≥ 9**, **Python ≥ 3.10**.

```bash
pnpm install

# backend
cd services/agent-engine
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --host 127.0.0.1 --port 8765

# desktop (another terminal, from repo root)
pnpm dev:desktop
```

You'll also need **Ollama** installed with at least one model to exercise AI
features (the app's Models page helps). ComfyUI is optional (images only).

## Before you open a PR

- **Open an issue first** for anything non-trivial, so we can agree on direction.
- Keep changes **small and focused**; refactors are separate PRs.
- **Don't break the invariants:** no paid APIs / cloud-by-default / Chroma Cloud;
  no arbitrary shell execution; Electron `contextIsolation` on / `nodeIntegration`
  off; filesystem access stays inside the workspace; no secrets/private content in
  logs.
- Add **types/schemas** and a **test or clear manual test**. Don't claim it works
  if you didn't run it.
- Run checks:
  ```bash
  pnpm --filter @evano/desktop typecheck
  pnpm --filter @evano/website typecheck
  cd services/agent-engine && source .venv/bin/activate && pytest
  ```
- **Update docs** in the same PR when behavior or architecture changes.
- Fill in the **pull request template** and link the issue.

## Reporting bugs & ideas

Use the issue templates (Bug report / Feature request). For security issues, see
[SECURITY.md](SECURITY.md) — report privately, not as a public issue.

## License

By contributing, you agree your contributions are licensed under the project's
**[MIT License](LICENSE)**.
