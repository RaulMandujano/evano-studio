<!--
Thanks for contributing to Evano Studio! Please keep PRs small and focused.
See CONTRIBUTING.md and docs/DEVELOPMENT_RULES.md.
-->

## What changed

A short summary of the change and why.

## Related issue

Closes #

## How to test

Steps to verify (or the tests added). Don't claim it works if you didn't run it.

## Checklist

- [ ] Small and focused (one logical change)
- [ ] Stays **local & free** — no paid API, no cloud-by-default, no Chroma Cloud
- [ ] No arbitrary shell execution; Electron security intact (contextIsolation on, nodeIntegration off) — if touched
- [ ] Filesystem/permission boundaries respected (workspace-only, no traversal) — if touched
- [ ] No secrets or private content in code, logs, or fixtures
- [ ] No unrelated rewrites; didn't remove working features
- [ ] Types/schemas added where needed
- [ ] Tests or a clear manual test included
- [ ] Docs updated if behavior/architecture changed
- [ ] `typecheck` passes (desktop/website) and backend `pytest` passes (if backend touched)
