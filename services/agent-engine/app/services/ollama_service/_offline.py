"""Exceptions that mean Ollama is unreachable (vs an unexpected error)."""
from __future__ import annotations

import httpx

_OFFLINE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpx.TimeoutException,
)
