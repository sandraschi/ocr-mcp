"""
Real OCR on committed fixture images.

Skipped unless ``OCR_RUN_REAL_OCR`` is truthy and the backend binary / deps work.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

SCANS_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "scans"
MANIFEST_PATH = SCANS_DIR / "manifest.json"


def _env_backend_override() -> str | None:
    v = os.environ.get("OCR_REAL_OCR_BACKEND", "").strip()
    return v if v else None


def _digits_only(text: str) -> str:
    return "".join(c for c in text if c.isdigit())


def _load_cases() -> list[dict[str, Any]]:
    raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return list(raw.get("cases") or [])


def _resolve_backend_name(case: dict[str, Any], manifest: dict[str, Any]) -> str:
    override = _env_backend_override()
    if override is not None:
        return override
    return str(case.get("backend") or manifest.get("default_backend") or "tesseract")


@pytest.mark.real_ocr
@pytest.mark.asyncio
async def test_manifest_cases(real_ocr_manager, stored_scan_manifest):
    manifest = stored_scan_manifest
    cases = _load_cases()
    assert cases, "manifest.json should list at least one case"

    for case in cases:
        image_name = case["image"]
        image_path = SCANS_DIR / image_name
        if not image_path.is_file():
            pytest.fail(f"Fixture image missing: {image_path} (run generate_fixtures.py)")

        backend_name = _resolve_backend_name(case, manifest)
        backend = real_ocr_manager.get_backend(backend_name)
        if not backend or not backend.is_available():
            pytest.skip(f"Backend {backend_name!r} not available on this host")

        mode = str(case.get("mode") or "text")
        result = await real_ocr_manager.process_with_backend(
            backend_name,
            str(image_path),
            mode=mode,
        )

        assert result.get("success") is True, (
            f"{image_name} failed on {backend_name}: {result.get('error')!r} body={result!r}"
        )
        text = (result.get("text") or "").upper()

        if "digits_exact" in case:
            expected = str(case["digits_exact"])
            got = _digits_only(result.get("text") or "")
            assert expected in got, (
                f"{image_name}: expected digit substring {expected!r} in {got!r} from OCR {result.get('text')!r}"
            )

        if "needles" in case:
            needles = [str(n).upper() for n in case["needles"]]
            min_hits = int(case.get("min_needle_hits", 1))
            hits = sum(1 for n in needles if n in text)
            assert hits >= min_hits, (
                f"{image_name}: wanted >= {min_hits} of {needles} in OCR text; got {hits}. text={result.get('text')!r}"
            )


@pytest.mark.real_ocr
@pytest.mark.asyncio
async def test_auto_backend_runs_on_first_fixture(real_ocr_manager):
    """``auto`` should pick an available engine and still read the primary alpha fixture."""
    cases = _load_cases()
    alpha = next((c for c in cases if "needles" in c), None)
    if not alpha:
        pytest.skip("No needle-based case in manifest")

    image_path = SCANS_DIR / alpha["image"]
    if not image_path.is_file():
        pytest.fail(f"Fixture image missing: {image_path}")

    result = await real_ocr_manager.process_with_backend("auto", str(image_path), mode="text")
    assert result.get("success") is True, result
    upper = (result.get("text") or "").upper()
    needles = [str(n).upper() for n in alpha["needles"]]
    min_hits = int(alpha.get("min_needle_hits", 1))
    assert sum(1 for n in needles if n in upper) >= min_hits, result.get("text")


def test_fixture_pngs_tracked():
    """Fail fast in CI if someone deletes binaries but keeps manifest."""
    for case in _load_cases():
        p = SCANS_DIR / case["image"]
        assert p.is_file(), f"Missing {p} — run: uv run python tests/fixtures/scans/generate_fixtures.py"
