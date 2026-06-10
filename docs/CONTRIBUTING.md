# Contributing to Evano Studio

Thank you for your interest in Evano Studio. This guide explains how to contribute in a way that keeps the project clean, stable, and maintainable for the long term.

> **Current status:** the project is in the documentation/planning phase (Phase 0). No application code exists yet. Early contributions are mostly about docs, architecture review, and preparing the foundation. See [ROADMAP.md](ROADMAP.md).

---

## Before you start

1. **Read the foundational docs:**
   - [ARCHITECTURE.md](ARCHITECTURE.md) — how the system is structured.
   - [ROADMAP.md](ROADMAP.md) — what's in scope and the order of work.
   - [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) — engineering standards (binding).
   - [SECURITY.md](SECURITY.md) — security rules (binding).
   - [FREE_BY_DEFAULT.md](FREE_BY_DEFAULT.md) — the free/local promise (binding).
2. **Check the roadmap.** Contributions should fit the current phase. Work that belongs to a later phase, or to the "not included" list, will be asked to wait.
3. **Open an issue first for anything non-trivial.** Describe the problem and your proposed approach before writing code, so we can agree on direction.

---

## How contributors should work

- **Stay in scope.** Match the current roadmap phase. Don't pull in out-of-scope or future work.
- **Respect the binding rules.** No paid APIs, no cloud-by-default, no Chroma Cloud, no arbitrary command execution, Electron security intact. These are not negotiable (see [SECURITY.md](SECURITY.md) and [FREE_BY_DEFAULT.md](FREE_BY_DEFAULT.md)).
- **Make small, focused changes.** One logical change per PR.
- **Don't rewrite unrelated working code** and don't remove existing working features (see the no-unrelated-rewrites rule in [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md)).
- **Keep the structure clean.** Put code where [ARCHITECTURE.md](ARCHITECTURE.md) says it goes. Don't add new top-level folders or dependencies without justification.
- **Add types and validate boundaries.** TypeScript types and Pydantic schemas; validate API/IPC/file inputs.
- **Handle errors gracefully**, including the "external service missing" cases (Ollama/ComfyUI).

---

## How to structure PRs

A good PR:

- **Does one thing.** If you find yourself writing "and also…", split it.
- **Has a clear title and description** explaining *what* changed and *why*.
- **States how to test it** — exact steps to verify, or the automated tests that cover it.
- **Keeps refactors separate** from feature changes.
- **Avoids formatting churn** in files you aren't otherwise changing.
- **Updates docs in the same PR** when behavior, architecture, scope, or security is affected.
- **Stays small.** Large PRs are hard to review safely; prefer a series of small ones.

Suggested PR description template:

```
## What changed
<short summary>

## Why
<the motivation / linked issue>

## How to test
<step-by-step verification, or the tests added>

## Docs updated
<which docs/ files were updated, or "n/a — no behavior change">

## Checklist
- [ ] Stays within current roadmap phase
- [ ] No paid API / cloud-by-default introduced
- [ ] Electron security rules intact (if touched)
- [ ] Filesystem/permission boundaries respected (if touched)
- [ ] No unrelated rewrites or removed working features
- [ ] Tests or manual verification included
- [ ] Docs updated if needed
```

---

## How to avoid breaking the project

- **Build step by step.** Don't combine many changes into one risky drop.
- **Run and verify before submitting.** Don't claim something works if you didn't run it (see [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md)).
- **Test the security boundaries** if you touch them: path safety, permissions, IPC, Electron config.
- **Preserve backward-compatible behavior.** Additive changes are preferred over breaking ones.
- **Check the layering.** Renderer talks to the backend over HTTP; OS actions go through the IPC bridge; external systems go through adapters. Don't shortcut these.
- **Don't commit local data.** Anything under `data/` is git-ignored and must stay that way (no databases, vectors, user files, or logs).

---

## How to document changes

- **Update the relevant `docs/` file** whenever your change affects architecture, scope, security, the free/local promise, or a feature's behavior.
- **Explain non-obvious decisions** in the PR (and in the docs if they're lasting). If you resolved an ambiguity, write down the decision and why.
- **Keep user-facing docs honest** and aligned with what actually works (see [WEBSITE.md](WEBSITE.md) honest-marketing rules).
- **Comments explain why, not what,** and match the surrounding code's style.

---

## Code of conduct & licensing

- Be respectful and constructive in issues and reviews.
- Evano Studio is intended to be released as open source; the specific license will be finalized before the first public release. By contributing, you agree your contributions will be licensed under the project's chosen open-source license.

---

Questions or unsure where something fits? **Open an issue and ask.** It's always better to align early than to build the wrong thing.
