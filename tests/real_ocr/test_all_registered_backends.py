"""
Exercise every OCR backend registered on ``BackendManager`` (real engines only).

* ``probe_backend`` — built-in tiny PNG + availability + optional ``load_model``.
* ``process_with_backend`` — same path as production, on committed ``fixture_alpha.png``.

Engines that are missing, misconfigured, or hit Transformers / CUDA / HF issues are **skipped**
by default so ``OCR_RUN_REAL_OCR=1`` stays usable on partial installs.

Set ``OCR_REAL_OCR_STRICT=1`` to **fail** any probe or stored-fixture error instead of skipping
(useful on a fully provisioned GPU box).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ocr_mcp.core.backend_manager import MockOCRBackend

SCANS_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "scans"
ALPHA_FIXTURE = SCANS_DIR / "fixture_alpha.png"


def _strict_real_ocr() -> bool:
    return os.environ.get("OCR_REAL_OCR_STRICT", "").strip().lower() in ("1", "true", "yes", "on")


@pytest.mark.real_ocr
@pytest.mark.asyncio
async def test_probe_backend_smoke(real_ocr_manager, backend_id: str) -> None:
    r = await real_ocr_manager.probe_backend(backend_id)
    if r.get("success"):
        return
    msg = f"{backend_id} probe phase={r.get('phase')!r}: {r.get('error')}"
    if _strict_real_ocr():
        pytest.fail(msg)
    pytest.skip(msg)


@pytest.mark.real_ocr
@pytest.mark.asyncio
async def test_stored_alpha_fixture_smoke(real_ocr_manager, backend_id: str) -> None:
    if not ALPHA_FIXTURE.is_file():
        pytest.fail(f"Missing {ALPHA_FIXTURE} — run: uv run python tests/fixtures/scans/generate_fixtures.py")

    backend = real_ocr_manager.get_backend(backend_id)
    if backend is None or isinstance(backend, MockOCRBackend) or not backend.is_available():
        pytest.skip(f"{backend_id}: backend not available on this host")

    result = await real_ocr_manager.process_with_backend(
        backend_id,
        str(ALPHA_FIXTURE),
        mode="text",
    )
    assert result.get("backend_used") == backend_id, (
        f"Expected backend {backend_id!r}, got {result.get('backend_used')!r} — "
        "check select_backend fallback when the named engine is unavailable."
    )
    if result.get("success") is True:
        return
    msg = f"{backend_id} stored fixture: {result.get('error')!r}"
    if _strict_real_ocr():
        pytest.fail(f"{msg} full={result!r}")
    pytest.skip(msg)
