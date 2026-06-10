# @evano/desktop

The Evano Studio desktop application — **Electron + React + TypeScript**, bundled with **electron-vite**.

> 🚧 **Alpha — desktop shell only.** This is the navigation shell and dashboard. There is **no backend connection, no Ollama logic, and no real functionality** wired up yet. Every feature view honestly says it's coming in a later phase.

## What's here

- A secure Electron app with a clean **main / preload / renderer** separation.
- A modern sidebar shell with all V1 sections: Dashboard, Models, Agents, Chat, Documents, Knowledge Base, Images, Routines, Calendar, Settings, Logs.
- A **Dashboard** with read-only status cards reflecting the honest current state (nothing connected yet).
- One real, safe IPC call (`app:get-info`) that reads basic runtime info over the contextBridge — a small example of the secure pattern future features will use.

## Requirements

- Node.js ≥ 20
- pnpm ≥ 9 (this app is part of the repo's pnpm workspace)
- A desktop environment (Electron opens a native window)

## Run it locally

From the **repository root**:

```bash
pnpm install            # installs workspace dependencies (downloads Electron)
pnpm dev:desktop        # launches the app in development
```

Or from **this folder** (`apps/desktop`):

```bash
pnpm dev                # electron-vite dev (HMR for the renderer)
```

## Other commands

```bash
pnpm build              # type-check + bundle main, preload, and renderer into out/
pnpm preview            # run the production build locally
pnpm typecheck          # TypeScript only (tsc --noEmit)
```

## Project structure

```
apps/desktop/
├── electron.vite.config.ts     # builds main, preload, renderer
├── tsconfig.json
├── package.json                # "main": ./out/main/index.js
└── src/
    ├── main/
    │   └── index.ts            # Electron main: window, security, IPC handlers
    ├── preload/
    │   └── index.ts            # contextBridge — the only renderer-facing API
    ├── shared/
    │   └── api.ts              # IPC contract (types + channel names, no imports)
    └── renderer/
        ├── index.html
        └── src/
            ├── main.tsx        # React entry
            ├── App.tsx         # app shell + view switching
            ├── navigation.ts   # sidebar registry (typed)
            ├── env.d.ts        # window.evano typing + vite client types
            ├── hooks/
            │   └── useAppInfo.ts
            ├── components/
            │   ├── layout/     # Sidebar, Topbar
            │   └── ui/         # Badge, Card, PageHeader, StatusCard, PlaceholderView
            ├── views/          # one component per section (+ index registry)
            └── styles/
                └── global.css  # design system
```

## Backend connection (Agent Engine)

The Dashboard checks the local backend (`services/agent-engine`) and shows a live
**Agent Engine** status: `Checking…`, `Running`, `Offline`, or `Error`, with a
**Refresh** button. If the backend isn't running, this is handled gracefully
(shown as "Offline" — the app does not crash).

- API client: `src/renderer/src/lib/api/` (`client.ts`, `types.ts`)
- Backend URL config: `src/renderer/src/lib/config.ts` (override with
  `VITE_EVANO_BACKEND_URL`, see `.env.example`) — defaults to
  `http://127.0.0.1:8765`
- Status logic: `src/renderer/src/hooks/useAgentEngineStatus.ts`
- UI: `src/renderer/src/components/dashboard/AgentEngineStatusCard.tsx`

To see "Running", start the backend first (see `services/agent-engine/README.md`),
then launch the desktop app and click **Refresh** if needed.

## Security model (Electron)

These defaults are mandatory and live in `src/main/index.ts` (see also `docs/SECURITY.md`):

| Setting | Value | Why |
| --- | --- | --- |
| `contextIsolation` | **true** | Renderer and preload run in isolated JS worlds. |
| `nodeIntegration` | **false** | No Node.js APIs in the renderer. |
| `sandbox` | **true** | Renderer runs in the OS sandbox. |
| `webSecurity` | **true** | Standard browser security model stays on. |
| Preload surface | tiny + typed | Only `window.evano.app.getInfo()` is exposed — never `ipcRenderer`, `require`, or `fs`. |
| New windows | denied | `setWindowOpenHandler` returns `deny`. |
| Navigation | locked to the app | `will-navigate` blocks external/unknown origins. |
| CSP | enforced in production | Strict `Content-Security-Policy` header (dev relaxes it for HMR). |

The renderer never touches the filesystem or OS directly. When real features arrive, they will go through the local backend over HTTP and through small, explicit IPC methods added to the preload contract in `src/shared/api.ts`.

## How to add a new view

1. Add the id to `ViewId` and an entry to `navGroups` in `src/renderer/src/navigation.ts`.
2. Create the component in `src/renderer/src/views/`.
3. Register it in `src/renderer/src/views/index.ts`.

TypeScript will flag any id you forget to wire up.
