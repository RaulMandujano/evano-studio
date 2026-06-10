# packages/

Shared, reusable JavaScript/TypeScript packages consumed by the apps. None contain implementation yet (Phase 1 placeholders).

| Package | Purpose |
| --- | --- |
| `@evano/shared` | Shared TS types, API contracts (mirrored as Pydantic in the backend), and constants. |
| `@evano/ui` | Shared React UI components — used by desktop and website where it makes sense. |
| `@evano/config` | Shared configuration constants. |

**Rules:**
- Packages may be imported by `apps/*`.
- Packages must **not** import from `apps/*` or `services/*`.
- Keep each package focused on one responsibility.

See [docs/PROJECT_STRUCTURE.md](../docs/PROJECT_STRUCTURE.md) for how to add a new package.
