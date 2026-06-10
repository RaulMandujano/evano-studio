# Packaging

How Evano Studio's desktop app is packaged into a distributable build. This
covers the **Electron app**; the local Python backend is handled separately (see
"Backend in packaged builds" below).

> Status: **alpha**. Builds are **unsigned** and not notarized yet. macOS is the
> first target; Windows config is prepared but not part of the public release yet.

## Tooling

- **electron-vite** builds the three Electron layers into `apps/desktop/out/`
  (`main`, `preload`, `renderer`).
- **electron-builder** packages `out/` into a distributable app/installer.
  Configuration lives in `apps/desktop/electron-builder.yml`.

## App metadata

| Field | Value |
| --- | --- |
| Product name | Evano Studio |
| Description | Local AI agents without the terminal |
| Author | Evano |
| App ID | `com.evano.studio` |

Icons go in `apps/desktop/build/` (`icon.icns` / `icon.ico` / `icon.png`). They
are placeholders for now — until added, electron-builder uses the default
Electron icon (see `apps/desktop/build/README.md`).

## Build commands

From `apps/desktop/`:

```bash
pnpm package:dir    # build an unpacked .app (fast; no installer) → release/
pnpm package:mac    # build a macOS .dmg + .zip (unsigned)        → release/
pnpm package:win    # build a Windows NSIS installer (run on Windows)
```

Each script runs `electron-vite build` first, then electron-builder. From the
repo root you can target it with `pnpm --filter @evano/desktop package:mac`.

## Output location

Artifacts are written to `apps/desktop/release/` (git-ignored):

- macOS: `release/Evano Studio-<version>.dmg`, a `.zip`, and `release/mac/Evano Studio.app`
- Windows: `release/Evano Studio Setup <version>.exe`
- `--dir` builds: just the unpacked app under `release/mac/` (or `release/win-unpacked/`)

## One-command client build

For a client-ready app (no Python, no terminal), use the build script from the
repo root — it freezes the backend, builds the Electron app, and packages them
together:

```bash
scripts/build-desktop.sh        # unpacked .app (fast, for testing)
scripts/build-desktop.sh dmg    # installable macOS .dmg
```

## Backend in packaged builds (bundled + auto-started)

The packaged app **bundles the Python backend as a frozen binary** and **starts
it automatically** on launch, so a non-technical client just opens the app.

- The backend is frozen with **PyInstaller** (`services/agent-engine/run_server.py`
  + `evano-backend.spec`) into `dist-backend/evano-backend/`.
- electron-builder copies it into the app at
  `<App>/Contents/Resources/evano-backend/evano-backend` (see `extraResources`).
- On launch the Electron main process calls `ensureBackendStarted()`
  (`apps/desktop/src/main/services.ts`): if nothing is already serving, it spawns
  the bundled binary (`shell:false`, no renderer-supplied commands). The renderer
  talks to it over local HTTP (default `http://127.0.0.1:8765`).
- First launch takes a few seconds while the frozen binary starts; Easy Start
  retries automatically and shows "Starting Evano…".
- Local data (SQLite, workspace, logs) lives under `EVANO_DATA_DIR`
  (default `~/.evano-studio`), **not** inside the app bundle.

**"Lite" bundle:** to keep the binary small and reliable to freeze, the
knowledge base (ChromaDB/onnxruntime) and Discord are **not** bundled — their
services import lazily and report "unavailable", so agents, tools, documents
(incl. real `.docx`/`.pdf`), and computer control all work. A client who wants
the knowledge base installs the full backend, or a later build can include it.

In **development** the app does not bundle a backend; run it with
`uvicorn` (or set `EVANO_BACKEND_CMD`) as before.

## External dependencies (user-installed)

Evano Studio is local-first and free; some local tools are provided by the user:

- **Ollama** — required for any AI features. The user installs it (the app guides
  them and links to the official download; it never installs software silently).
  Models are pulled locally through the app's Models page.
- **ComfyUI** — optional, only for local image generation. The user installs and
  runs it themselves and points the app at its local URL. All other features work
  without it.
- **ChromaDB** — bundled as a Python dependency of the backend environment (local
  persistent mode only; never Chroma Cloud). No separate user install. Its
  default local embedding model (MiniLM) downloads once on first knowledge-base
  import.

## Signing & notarization

Not done yet. `mac.identity` is set to `null` so builds are produced **unsigned**
rather than failing when no signing identity is present. Before public
distribution, configure an Apple Developer ID (signing + notarization) for macOS
and a code-signing certificate for Windows.

## Limitations (alpha)

- Unsigned/un-notarized — macOS Gatekeeper will warn on first open (right-click →
  Open the first time).
- The bundled backend is the **"lite"** build (no knowledge base / Discord).
- **Ollama is still user-installed** (required for AI; the app links to it).
- Placeholder icons until final art is added.
- Windows/Linux targets are configured but only macOS is exercised for the
  first alpha.
