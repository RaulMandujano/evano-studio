# Desktop App

The Evano Studio desktop app — **Electron + React + TypeScript**, bundled with
**electron-vite**. It's the user-facing control center.

## Run

```bash
pnpm dev:desktop        # from the repo root
```

Requires the backend running (see [AGENT_ENGINE.md](AGENT_ENGINE.md)).

## Structure (`apps/desktop`)

```
src/
├── main/index.ts          # Electron main: window, security, IPC handlers
├── main/services.ts       # safe local service management (start/stop/open)
├── preload/index.ts       # contextBridge — the only renderer-facing API
├── shared/api.ts          # IPC contract (types + channel names, no imports)
└── renderer/src/
    ├── App.tsx, navigation.ts
    ├── lib/api/           # typed HTTP client for the backend
    ├── hooks/             # useBackendResource, useOllama, useAgentEngineStatus, …
    ├── components/        # layout, ui, agents, chat, calendar, routines, settings, docs
    └── views/             # Dashboard, Models, Agents, Chat, Documents, Knowledge,
                           # Images, Routines, Calendar, Settings, Logs
```

## How it talks to the backend

The renderer calls the local backend over HTTP (`VITE_EVANO_BACKEND_URL`, default
`http://127.0.0.1:8765`) through a small typed client in `lib/api/`. OS-level
actions (reveal a file, pick a folder, open a URL, start/stop the backend) go
through a **small, explicit IPC bridge** (`window.evano.*`) — never raw Node APIs.

## Security model (mandatory)

- `contextIsolation` **on**, `nodeIntegration` **off**, `sandbox` **on**.
- The preload exposes only a tiny, typed surface via `contextBridge`.
- New windows denied; navigation locked to the app; strict CSP in production.
- The renderer can't run shell commands; service start uses a pre-configured
  command from env, never renderer input.

See [SECURITY.md](SECURITY.md). Packaging is covered in [PACKAGING.md](PACKAGING.md).
