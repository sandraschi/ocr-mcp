"""Fixtures for optional real OCR regression tests."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from ocr_mcp.core.backend_manager import BackendManager
from ocr_mcp.core.config import OCRConfig


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize ``backend_id`` over every key in ``BackendManager.backend_registry`` (single sync snapshot)."""
    if "backend_id" not in metafunc.fixturenames:
        return
    if not metafunc.module.__name__.endswith("test_all_registered_backends"):
        return
    cache = Path(tempfile.mkdtemp(prefix="ocr_registry_param_"))
    cfg = OCRConfig(
        cache_dir=cache,
        model_dir=cache / "models",
        model_cache_dir=cache / "models",
        device="cpu",
        default_backend="tesseract",
    )
    mgr = BackendManager(cfg)
    metafunc.parametrize("backend_id", sorted(mgr.backend_registry.keys()))


def real_ocr_env_enabled() -> bool:
    v = os.environ.get("OCR_RUN_REAL_OCR", "").strip().lower()
    return v in ("1", "true", "yes", "on")


@pytest.fixture(scope="module")
def stored_scan_manifest() -> dict:
    root = Path(__file__).resolve().parents[1]
    path = root / "fixtures" / "scans" / "manifest.json"
    if not path.is_file():
        pytest.skip(f"Missing manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def real_ocr_config():
    """Dedicated OCRConfig so real runs do not fight other session fixtures."""
    import tempfile

    cache = Path(tempfile.mkdtemp(prefix="ocr_real_ocr_"))
    return OCRConfig(
        cache_dir=cache,
        model_dir=cache / "models",
        model_cache_dir=cache / "models",
        device="cpu",
        default_backend="tesseract",
    )


@pytest.fixture(scope="module")
def real_ocr_manager(real_ocr_config):
    if not real_ocr_env_enabled():
        pytest.skip("Set OCR_RUN_REAL_OCR=1 to run real OCR on stored fixtures (see tests/fixtures/scans/README.md)")
    return BackendManager(real_ocr_config)
