"""Limits and extension policies for the workspace-confined tools."""
from __future__ import annotations

_READABLE_EXTENSIONS = {".txt", ".md", ".markdown", ".html", ".csv", ".json", ".doc", ".rtf", ".log"}
# Files are written as text. We allow any extension EXCEPT clearly executable /
# script types (which could be run later) — a blocklist instead of an allowlist
# so an agent can create the file the user actually asked for (e.g. .doc, .csv).
_BLOCKED_WRITE_EXTENSIONS = {
    ".sh", ".bash", ".zsh", ".command", ".exe", ".bat", ".cmd", ".ps1", ".psm1",
    ".app", ".scpt", ".scr", ".msi", ".dll", ".so", ".dylib", ".com", ".jar", ".vbs",
}
_MAX_READ_BYTES = 1_000_000  # 1 MB cap for tool reads
_SEARCH_MAX_FILE_BYTES = 1_000_000  # skip files larger than this when searching
_SEARCH_MAX_FILES = 500  # don't scan an unbounded number of files
_SEARCH_MAX_MATCHES = 50  # cap results returned
