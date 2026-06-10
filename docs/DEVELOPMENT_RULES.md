# Development Rules

These rules exist so Evano Studio stays clean, maintainable, and shippable as it grows. They apply to everyone, including AI assistants generating code. Treat them as binding, not advisory.

---

## Engineering standards

1. **Build step by step.** Implement one feature at a time, in roadmap order. Each change should leave the project in a working, testable state.
2. **Prefer small, testable changes.** A small PR that does one thing well beats a large PR that touches everything.
3. **Use types and schemas.** TypeScript types on the frontend; Pydantic schemas on the backend. Validate data at boundaries (API requests, IPC messages, file inputs).
4. **Keep the layering honest.** Respect the architecture boundaries (renderer → backend over HTTP; backend `api → services → adapters/db`). Don't let HTTP concerns leak into business logic or vice versa.
5. **Thin adapters for external systems.** Ollama, ChromaDB, and ComfyUI are always reached through their adapter modules. Never call them directly from UI or business logic.
6. **Clear naming.** Names should describe intent. No cryptic abbreviations, no `data2`, no `utils` dumping grounds.
7. **No dead code.** Don't commit commented-out blocks or unused exports "just in case."

---

## File organization rules

1. **Follow the planned structure** in [ARCHITECTURE.md](ARCHITECTURE.md). Put code where it belongs.
2. **One responsibility per module.** A file should have a clear, single purpose.
3. **Feature-first on the frontend.** Group renderer code by feature (`agents`, `chat`, `documents`, …), not by file type.
4. **Domain-first on the backend.** One router and matching service per domain.
5. **Shared code goes in `packages/`.** If the desktop app and website need the same thing, it belongs in a shared package — not copy-pasted.
6. **No new top-level folders** without updating [ARCHITECTURE.md](ARCHITECTURE.md) and explaining why.
7. **Local runtime data stays under `data/`** and is git-ignored. Never commit user data, databases, vectors, or generated files.

---

## No overbuilding rule

- **Build only what the current phase requires.** Do not add features, abstractions, or configuration for hypothetical future needs.
- **No speculative generality.** Don't add a plugin system, an event bus, or a generic framework when a direct implementation works.
- **Don't add dependencies you don't need.** Every dependency is a maintenance and security cost. Prefer the standard library and what's already in the project. If a new dependency is needed, justify it in the PR.
- **Respect the V1 "not included" list** in [ROADMAP.md](ROADMAP.md). If a change starts pulling in out-of-scope work, stop and split it.
- **The simplest correct solution wins.**

---

## No unrelated rewrites rule

- **Do not rewrite working code that is unrelated to your task.** If it works and it's not in scope, leave it alone.
- **Do not remove existing working features.** Additive changes are strongly preferred.
- **Refactors are their own PRs.** Don't mix a refactor into a feature change — it hides bugs and makes review impossible.
- **If you must touch shared code,** make the minimal change and verify you didn't break other consumers.
- **Don't reformat files you aren't otherwise changing.** Formatting churn obscures real diffs.

---

## Testing expectations

- **Test the logic that matters.** Backend services (permissions, path safety, RAG chunking, routine scheduling) need tests. Pure UI glue does not need exhaustive tests.
- **Path safety and permission checks must be tested.** These are security boundaries — see [SECURITY.md](SECURITY.md).
- **Adapters should be testable in isolation,** with external systems (Ollama, ChromaDB, ComfyUI) mockable.
- **A change isn't done until it's verified.** Either an automated test or a clearly described manual test in the PR.
- **Never claim something works if it wasn't run.** If you couldn't test it, say so.

---

## Error handling expectations

- **Fail clearly, never silently.** Surface errors with enough context to act on.
- **Handle the "external service is missing" case explicitly.** Ollama not running, no model installed, ComfyUI not configured — these are normal states, not crashes. Show non-technical, helpful guidance.
- **Validate inputs at every boundary** (API, IPC, file paths). Reject bad input early with clear errors.
- **No secrets or private content in error messages or logs** (see [SECURITY.md](SECURITY.md)).
- **User-facing errors are written for non-technical users.** Avoid stack traces in the UI; log the detail, show the human message.

---

## Documentation expectations

- **Update docs with the code.** If a change affects architecture, scope, security, or a feature's behavior, update the relevant `docs/` file in the same PR.
- **Explain what changed and how to test it.** Every PR description must state what changed and the steps to verify it (see [CONTRIBUTING.md](CONTRIBUTING.md)).
- **Document engineering decisions.** When you make a non-obvious choice (or resolve an ambiguity), write it down — in the PR and, if it's lasting, in the relevant doc.
- **Keep `data/` and config documented.** If you add a new data location, setting, or environment variable, document it.
- **Comments explain *why*, not *what*.** Match the comment density and style of the surrounding code.

---

## The short version

> Small changes. Clear boundaries. No overbuilding. No unrelated rewrites. Test the boundaries. Fail clearly. Keep docs in sync.
