#!/usr/bin/env bash
#
# Build a distributable Evano Studio desktop app for non-technical clients.
# Steps: freeze the Python backend (PyInstaller) → build the Electron app →
# package it (electron-builder bundles the frozen backend as a resource and the
# app auto-starts it, so the client needs no Python and no terminal).
#
# Usage:
#   scripts/build-desktop.sh            # unpacked .app (fast, for testing)
#   scripts/build-desktop.sh dmg        # installable .dmg (macOS)
#
# Prereqs: the backend venv with deps + PyInstaller, Node + pnpm.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="${1:-dir}"

echo "==> [1/3] Freezing the backend (PyInstaller)…"
cd "$ROOT/services/agent-engine"
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -q -e ".[build]"
pyinstaller --noconfirm --distpath dist-backend --workpath build-backend evano-backend.spec
test -x dist-backend/evano-backend/evano-backend
echo "    backend frozen → services/agent-engine/dist-backend/evano-backend"

echo "==> [2/3] Installing desktop deps…"
cd "$ROOT/apps/desktop"
pnpm install

echo "==> [3/3] Packaging the desktop app…"
case "$MODE" in
  dmg) pnpm package:mac ;;
  win) pnpm package:win ;;
  *)   pnpm package:dir ;;
esac

echo "==> Done. Output in apps/desktop/release/"
