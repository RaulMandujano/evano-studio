"""Filesystem path safety helpers.

These enforce the security boundary for documents: files may only live directly
inside the Evano Studio workspace. No arbitrary paths, no directory traversal.
See docs/SECURITY.md.
"""

from __future__ import annotations

import re
from pathlib import Path

from .errors import AppError

# Allow letters, digits, space, dot, underscore, hyphen. Everything else → "_".
_UNSAFE = re.compile(r"[^A-Za-z0-9._ -]")
_MAX_NAME_LEN = 120


def sanitize_filename(name: str) -> str:
    """Reduce an arbitrary string to a safe, flat filename (no directories).

    Strips path separators and ``..``, removes unsafe characters, and trims
    leading/trailing dots and spaces. Always returns a non-empty name.
    """
    name = (name or "").strip()
    name = name.replace("/", "_").replace("\\", "_")
    name = name.replace("..", "_")  # defeat traversal sequences
    name = _UNSAFE.sub("_", name)
    name = name.strip(". ")
    if not name:
        name = "document"
    return name[:_MAX_NAME_LEN]


def resolve_within(root: Path, filename: str) -> Path:
    """Resolve ``filename`` directly inside ``root`` and verify it stays there.

    Raises AppError if the resolved path would escape the workspace root.
    """
    root = root.resolve()
    candidate = (root / filename).resolve()
    if candidate == root or candidate.parent != root:
        raise AppError(
            "Invalid file path (must be inside the workspace).",
            status_code=400,
            code="invalid_path",
        )
    return candidate


def is_within(root: Path, path: Path) -> bool:
    """True if ``path`` is inside ``root`` (used for safe deletes)."""
    try:
        root = root.resolve()
        path = path.resolve()
    except OSError:
        return False
    return path == root or root in path.parents


def split_relative_segments(relative: str) -> list[str]:
    """Split a user-supplied relative path into safe, sanitized segments.

    Splits on both ``/`` and ``\\``, drops empty/``.`` segments, rejects any
    ``..`` traversal segment, and sanitizes each remaining segment so it can
    never contain path separators or unsafe characters. Returns an empty list
    for an empty/root path (callers decide whether that is allowed).
    """
    segments: list[str] = []
    for raw in re.split(r"[\\/]+", (relative or "").strip()):
        seg = raw.strip()
        if not seg or seg == ".":
            continue
        if seg == "..":
            raise AppError(
                "Invalid path (directory traversal is not allowed).",
                status_code=400,
                code="invalid_path",
            )
        segments.append(sanitize_filename(seg))
    return segments


def resolve_subpath(root: Path, relative: str, *, require: bool = True) -> Path:
    """Resolve a possibly-nested ``relative`` path *inside* ``root``.

    Unlike :func:`resolve_within` (which only allows files directly in ``root``),
    this permits subdirectories — needed now that the workspace has a folder
    structure. It still guarantees the result stays within ``root``: traversal
    segments are rejected and the resolved path is verified against the root.

    With ``require=True`` an empty relative path is an error; with
    ``require=False`` an empty path resolves to ``root`` itself (e.g. "list the
    workspace root").
    """
    root = root.resolve()
    segments = split_relative_segments(relative)
    if not segments:
        if require:
            raise AppError("A path is required.", status_code=400, code="invalid_path")
        return root
    candidate = root.joinpath(*segments).resolve()
    if candidate != root and root not in candidate.parents:
        raise AppError(
            "Invalid path (must be inside the workspace).",
            status_code=400,
            code="invalid_path",
        )
    return candidate
