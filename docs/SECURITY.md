# Security

Evano Studio is local-first and privacy-first. This document defines the security model and the non-negotiable rules that protect the user's machine and data. These rules are binding for all code.

> **Reporting vulnerabilities:** until a formal security policy is published, report suspected vulnerabilities privately to the maintainers rather than opening a public issue. A `SECURITY.md` disclosure process will be finalized before the first public release.

---

## Local-first security model

- **Everything runs on the user's machine.** There is no Evano Studio server, no account, and no cloud component required to use the app.
- **The backend listens on `127.0.0.1` only.** It is never exposed to the network or other machines.
- **No data leaves the machine by default.** Models, documents, embeddings, chats, and logs all stay local.
- **The threat model** focuses on: protecting the user from the app doing something dangerous to their system, protecting user data from leaving the machine unintentionally, and limiting what agents (driven by a local model) can do.

---

## Agent permissions

Agents are powered by a local model and act on the user's behalf, so they are treated as **untrusted by default**.

- An agent can do **nothing** beyond chatting unless the user explicitly grants permissions.
- Permissions are stored per-agent and enforced **in the backend**, not in the UI. A compromised or buggy UI must not be able to bypass them.
- Permissions are **deny-by-default**. New capabilities are off until turned on.
- Granting a permission to one agent never grants it to another.
- See [AGENTS.md](AGENTS.md) for the full permission and tool model.

---

## Tool permissions

- **Agents can only use explicitly enabled tools.** A tool that isn't enabled for an agent is unreachable by that agent.
- **Tools can only access approved workspace folders.** A file tool may read/write only within the allow-listed workspace, never arbitrary system paths.
- Every tool call is validated against the agent's permission set **on the backend** before execution.
- Tools that touch external services (ComfyUI, the knowledge base) are gated by their own permission and only act on the configured local endpoints.
- Tool actions should be **logged** (without sensitive content) so the user can see what an agent did.

---

## Electron security rules

These are mandatory and must never be relaxed:

- **`contextIsolation` is enabled** on all windows.
- **`nodeIntegration` is disabled** on all windows.
- **No `remote` module**, no exposing `require`, `fs`, `child_process`, or `ipcRenderer` directly to the renderer.
- **The preload script exposes only a small, explicit, typed IPC surface** via `contextBridge`. Each exposed function does one specific, safe thing.
- **The renderer never accesses the filesystem or OS directly.** It reaches application logic through the local backend HTTP API and OS-level actions only through the vetted IPC bridge.
- **Validate everything crossing the IPC boundary.** Treat IPC input as untrusted.
- **Web security stays on.** No disabling of web security, no loading remote/untrusted content into privileged windows.

---

## Filesystem boundaries

- **All file access is confined to an allow-listed workspace root** (`data/workspace` in dev; a per-user app directory when packaged).
- **Directory traversal is prevented.** Every path is normalized and resolved, then checked to ensure it stays inside the allowed root. Paths containing `..`, symlinks escaping the root, or absolute paths outside the root are rejected.
- **No writing outside the workspace.** The app does not modify system files, other apps' data, or anything the user didn't point it at.
- **No reading sensitive system locations.** Tools cannot be aimed at home-directory secrets, SSH keys, browser profiles, etc.
- Path-safety logic is centralized in the backend `core/` layer and **must be unit-tested** (see [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md)).

---

## No arbitrary command execution

- **The renderer cannot execute shell commands.** There is no IPC or API that runs arbitrary commands on its behalf.
- **Agents cannot execute arbitrary system commands.** There is no "run this in the terminal" tool in V1.
- **No `sudo`, ever.** The app never asks for or uses elevated privileges.
- **No silent installs.** The app never installs Ollama, models, ComfyUI, or any software without the user explicitly doing it themselves. The app may *guide* the user, but it does not run installers behind their back.
- External services (Ollama, ComfyUI) are reached only over their **local HTTP APIs**, never by shelling out.

---

## No cloud upload by default

- **Nothing is uploaded to the cloud by default.** No telemetry, no analytics, no crash reporting that sends data off-machine without explicit, informed opt-in.
- **No remote model calls.** All inference is local via Ollama. No paid or remote LLM/embedding/image APIs (see [FREE_BY_DEFAULT.md](FREE_BY_DEFAULT.md)).
- If any optional feature ever sends data off the machine, it must be **off by default**, clearly labeled, and require explicit consent each time it matters.

---

## Support bundle privacy rules

The support bundle helps users report problems. It must never leak private content.

- **By default, the support bundle excludes private chat contents and document contents.**
- **By default, it excludes knowledge base contents and generated files.**
- It may include: app version, OS info, sanitized logs, configuration flags (not secrets), and the presence/health of Ollama/ComfyUI — only what's needed to diagnose issues.
- **No secrets in logs or the bundle.** API tokens (if any are ever configured), absolute paths revealing personal info, and credentials must be redacted.
- The user is shown **what the bundle contains before it is created/shared**, and creating it never automatically sends it anywhere.
- Any inclusion of richer detail (e.g., a specific failing document) must be an explicit, per-item opt-in by the user.

---

## Secrets handling

- **Never log secrets.** This includes any configured tokens, credentials, or sensitive paths.
- **Never commit secrets** to the repository. Local config holding sensitive values stays under git-ignored `data/` or OS keychain-equivalent storage.
- Configuration that must be present (e.g., a ComfyUI URL) is **not secret**, but is still kept out of logs where it could reveal the user's setup unnecessarily.

---

## Summary checklist

| Rule | Status requirement |
| --- | --- |
| Backend binds to localhost only | Always |
| `contextIsolation` on, `nodeIntegration` off | Always |
| Renderer has no direct FS/OS access | Always |
| Agent/tool permissions deny-by-default, enforced in backend | Always |
| Filesystem confined to workspace, traversal blocked | Always |
| No arbitrary command execution, no sudo, no silent installs | Always |
| No cloud upload / remote APIs by default | Always |
| Support bundle excludes private content by default | Always |
| No secrets in logs or commits | Always |
