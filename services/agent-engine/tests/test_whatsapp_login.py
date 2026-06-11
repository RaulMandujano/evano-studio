"""Tests for the in-app WhatsApp QR login (terminal QR art → SVG)."""

from __future__ import annotations

from app.services.openclaw_service._whatsapp_login import (
    _is_qr_line,
    matrix_to_svg,
    parse_qr_block,
)


def _checker_matrix(n: int = 25) -> list[list[bool]]:
    return [[(x + y) % 2 == 0 for x in range(n)] for y in range(n)]


def _to_half_block_art(matrix: list[list[bool]]) -> list[str]:
    """Render a matrix the way terminal QRs do: one char = two vertical modules."""
    lines = []
    for y in range(0, len(matrix), 2):
        top = matrix[y]
        bottom = matrix[y + 1] if y + 1 < len(matrix) else [False] * len(top)
        line = ""
        for t, b in zip(top, bottom):
            line += "█" if (t and b) else "▀" if t else "▄" if b else " "
        lines.append(line)
    return lines


def test_half_block_roundtrip() -> None:
    original = _checker_matrix(26)
    art = _to_half_block_art(original)
    assert all(_is_qr_line(l) for l in art)
    parsed = parse_qr_block(art)
    assert parsed == original


def test_full_block_double_width() -> None:
    original = _checker_matrix(25)
    art = ["".join("██" if cell else "  " for cell in row) for row in original]
    parsed = parse_qr_block(art)
    assert parsed == original


def test_rejects_non_qr_text() -> None:
    assert parse_qr_block(["hello world", "not a qr"]) is None
    assert not _is_qr_line("Scanning… please wait")
    assert parse_qr_block(_to_half_block_art(_checker_matrix(10))) is None  # too small


def test_svg_render_shape() -> None:
    svg = matrix_to_svg(_checker_matrix(25))
    assert svg.startswith("<svg")
    assert 'fill="#000"' in svg  # dark background (faithful to the terminal)
    assert svg.count("<rect") > 200  # plenty of light modules


def test_endpoints_graceful_without_openclaw(client, monkeypatch) -> None:
    from app.services.openclaw_service import process

    monkeypatch.setattr(process, "_which", lambda cmd: None)
    body = client.post("/openclaw/whatsapp/login/start").json()
    assert body["state"] == "error"
    assert "OpenClaw" in body["message"]

    status = client.get("/openclaw/whatsapp/login/status").json()
    assert status["state"] in ("idle", "error")

    assert client.post("/openclaw/whatsapp/login/cancel").json()["state"] == "idle"
