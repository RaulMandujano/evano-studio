# Security Policy

Evano Studio is **alpha** software and **local-first** by design: it runs on your
machine and does not upload your data to the cloud by default. Security is still a
top priority — thank you for helping keep users safe.

## Reporting a vulnerability

**Please do not open a public issue for security vulnerabilities.**

Report them privately via GitHub's **"Report a vulnerability"** (Security →
Advisories) on the repository, or by contacting the maintainers directly. Include:

- a description of the issue and its impact,
- steps to reproduce (and a proof of concept if possible),
- affected version/commit and your OS.

We'll acknowledge your report, investigate, and coordinate a fix and disclosure.
Please give us reasonable time to address it before any public disclosure.

## Scope

Examples of issues we especially want to hear about:

- Renderer escaping the Electron sandbox, or executing code/commands it shouldn't.
- Filesystem access outside the configured workspace (path traversal).
- Any path that uploads user data off-device, or leaks secrets/private content
  into logs or the support bundle.
- The backend being reachable beyond `127.0.0.1`, or unsafe CORS.

## What we guarantee (by design)

These are core invariants — a violation of any is a security bug:

- Electron runs with `contextIsolation` **on** and `nodeIntegration` **off**.
- The renderer cannot execute arbitrary shell commands; there is no `sudo` and no
  silent installs.
- Agent tools are **deny-by-default** and confined to the approved workspace.
- The backend binds to `127.0.0.1` only; CORS is restricted to localhost.
- No cloud upload by default; support bundles exclude chat/document contents and
  secrets.

The full model is documented in [docs/SECURITY.md](docs/SECURITY.md).
