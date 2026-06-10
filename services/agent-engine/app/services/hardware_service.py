"""Hardware probe — what can THIS machine actually run?

Powers the "Cookbook"-style model recommendations: instead of a static list,
Evano reads the machine's RAM/CPU (and Apple unified memory) and scores each
curated model so a non-technical user instantly sees what fits. Best-effort
and cached: probing never fails the request.
"""

from __future__ import annotations

import os
import platform
import subprocess
from functools import lru_cache


def _mac_sysctl(key: str) -> str | None:
    try:
        out = subprocess.run(
            ["sysctl", "-n", key], capture_output=True, text=True, timeout=3
        )
        return out.stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


@lru_cache(maxsize=1)
def probe_hardware() -> dict:
    """RAM, CPU, and chip info. Cached for the process lifetime."""
    system = platform.system()
    ram_gb = 0.0
    chip: str | None = None
    unified_memory = False

    if system == "Darwin":
        mem = _mac_sysctl("hw.memsize")
        if mem and mem.isdigit():
            ram_gb = int(mem) / 1024**3
        chip = _mac_sysctl("machdep.cpu.brand_string")
        unified_memory = bool(chip and "Apple" in chip)
    else:
        try:
            page = os.sysconf("SC_PAGE_SIZE")
            pages = os.sysconf("SC_PHYS_PAGES")
            ram_gb = page * pages / 1024**3
        except (ValueError, OSError, AttributeError):
            ram_gb = 0.0
        chip = platform.processor() or platform.machine() or None

    return {
        "platform": system,
        "ram_gb": round(ram_gb, 1),
        "cpu_cores": os.cpu_count() or 0,
        "chip": chip,
        "unified_memory": unified_memory,
    }


def fit_for(min_ram_gb: float | None, ram_gb: float) -> tuple[str, str]:
    """Score how well a model fits this machine → (fit, human reason).

    fit: great | good | tight | too_big | unknown
    """
    if not min_ram_gb or ram_gb <= 0:
        return "unknown", "Couldn't estimate for this machine."
    if ram_gb >= min_ram_gb * 2:
        return "great", f"Runs great — needs ~{min_ram_gb:.0f} GB, you have {ram_gb:.0f} GB."
    if ram_gb >= min_ram_gb * 1.25:
        return "good", f"Runs well — needs ~{min_ram_gb:.0f} GB, you have {ram_gb:.0f} GB."
    if ram_gb >= min_ram_gb:
        return "tight", f"Tight fit — close other apps while it runs ({min_ram_gb:.0f} GB needed)."
    return "too_big", f"Too big for this machine — needs ~{min_ram_gb:.0f} GB of RAM."
