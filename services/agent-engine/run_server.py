"""Frozen-server entry point (used by PyInstaller for packaged desktop builds).

Runs the FastAPI app with uvicorn using the app object directly (no reload, no
import-string) so it works inside a PyInstaller bundle. Heavy optional features
(ChromaDB/onnxruntime knowledge base, Discord) are imported lazily by their
services, so they simply report "unavailable" if not bundled — the rest of the
backend (agents, tools, documents, computer control) works fully.
"""

from __future__ import annotations

import os


def main() -> None:
    import uvicorn

    from app.core.config import get_settings
    from app.main import app

    settings = get_settings()
    host = os.environ.get("EVANO_HOST", settings.host)
    port = int(os.environ.get("EVANO_PORT", str(settings.port)))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
