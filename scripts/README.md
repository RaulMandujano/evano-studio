# scripts/

Project automation scripts, organized by purpose. These are placeholders in Phase 1 — real scripts are added as each phase needs them.

| Folder | Purpose |
| --- | --- |
| `setup/` | One-time environment setup helpers (e.g. checking for Ollama, creating a Python venv). The app never installs software silently — these scripts only *check* and *guide*. See [docs/SECURITY.md](../docs/SECURITY.md). |
| `dev/` | Day-to-day development launchers (start desktop, website, backend). |
| `health-checks/` | Scripts that verify the local environment / running services (Ollama reachable, backend `/health`, optional ComfyUI reachable). |

Keep scripts cross-platform-friendly and dependency-light. Document any new script here.
