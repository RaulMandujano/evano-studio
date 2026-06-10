"""Tests for the hardware probe and Cookbook-style model fit scoring."""

from __future__ import annotations

import pytest

from app.services.hardware_service import fit_for, probe_hardware


def test_probe_hardware_shape() -> None:
    hw = probe_hardware()
    assert hw["ram_gb"] > 0
    assert hw["cpu_cores"] > 0
    assert hw["platform"]


@pytest.mark.parametrize(
    "min_ram,ram,expected",
    [
        (8, 32, "great"),
        (8, 12, "good"),
        (8, 8.5, "tight"),
        (8, 4, "too_big"),
        (None, 32, "unknown"),
        (8, 0, "unknown"),
    ],
)
def test_fit_scoring(min_ram, ram, expected) -> None:
    fit, reason = fit_for(min_ram, ram)
    assert fit == expected
    assert reason


def test_recommended_endpoint_includes_fit(client) -> None:
    body = client.get("/ollama/models/recommended").json()
    assert body["hardware"]["ram_gb"] > 0
    fits = {m["fit"] for m in body["models"]}
    assert fits <= {"great", "good", "tight", "too_big", "unknown"}
    assert all(m["fit_reason"] for m in body["models"])
    # Sorted best-fit first.
    rank = {"great": 0, "good": 1, "tight": 2, "unknown": 3, "too_big": 4}
    ranks = [rank[m["fit"]] for m in body["models"]]
    assert ranks == sorted(ranks)
