"""
Unit tests for FastAPI webapp logging ring buffer, scan crop helper, and related API routes.

Imports ``backend.app`` (full module init). Marked ``webapp`` for selective runs.
"""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

pytestmark = pytest.mark.webapp


@pytest.fixture(scope="module")
def webapp_module():
    """Import webapp once per module (heavy: managers, bootstrap)."""
    import backend.app as app_mod

    return app_mod


@pytest.fixture
def clear_log_buffer(webapp_module):
    webapp_module._server_log_lines.clear()
    yield
    webapp_module._server_log_lines.clear()


def test_crop_scanned_region_sync_success(webapp_module, tmp_path: Path):
    from backend.app import _crop_scanned_region_sync

    scans = tmp_path / "scans"
    scans.mkdir()
    src = scans / "src.png"
    Image.new("RGB", (80, 60), color=(10, 20, 30)).save(src)

    crop_name, crop_abs = _crop_scanned_region_sync(src, 10, 10, 30, 20, "jobtest1", scans)

    assert crop_name.startswith("crop_jobtest1")
    assert Path(crop_abs).exists()
    with Image.open(crop_abs) as c:
        assert c.size == (30, 20)


def test_crop_scanned_region_sync_invalid(webapp_module, tmp_path: Path):
    from backend.app import _crop_scanned_region_sync

    scans = tmp_path / "scans"
    scans.mkdir()
    src = scans / "src2.png"
    Image.new("RGB", (20, 20), color="white").save(src)

    with pytest.raises(ValueError, match="Invalid crop dimensions"):
        _crop_scanned_region_sync(src, 5, 5, 0, 10, "bad", scans)


def test_server_logs_endpoint_shape_and_limit(webapp_module, clear_log_buffer):
    from fastapi.testclient import TestClient

    from backend.app import app

    buf = webapp_module._server_log_lines
    buf.append("line-a")
    buf.append("line-b")
    buf.append("line-c")

    client = TestClient(app)
    r = client.get("/api/server_logs", params={"limit": 2})
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 2
    assert data["max"] == webapp_module.MAX_SERVER_LOG_LINES
    assert data["lines"] == ["line-b", "line-c"]

    r0 = client.get("/api/server_logs", params={"limit": 0})
    assert r0.status_code == 200
    assert r0.json()["count"] == 1

    r_big = client.get("/api/server_logs", params={"limit": 99999})
    assert r_big.status_code == 200
    assert r_big.json()["count"] <= webapp_module.MAX_SERVER_LOG_LINES


def test_ring_memory_handler_handle_error(webapp_module, monkeypatch):
    """Broken formatter should use handleError (stderr) without crashing."""
    from backend.app import _RingMemoryHandler

    bad = _RingMemoryHandler()
    bad.setFormatter(logging.Formatter("%(missing)s"))
    err_calls: list[logging.LogRecord] = []

    def fake_handle_error(record: logging.LogRecord) -> None:
        err_calls.append(record)

    monkeypatch.setattr(bad, "handleError", fake_handle_error)
    bad.emit(logging.LogRecord("x", logging.INFO, __file__, 1, "msg", (), None))
    assert len(err_calls) == 1


def test_ocr_selection_missing_file_returns_404(webapp_module, monkeypatch, tmp_path: Path):
    from fastapi.testclient import TestClient

    from backend.app import app

    monkeypatch.setattr(webapp_module, "project_root", tmp_path)
    (tmp_path / "scans").mkdir(parents=True)

    client = TestClient(app)
    r = client.post(
        "/api/ocr_selection",
        data={
            "filename": "nope.png",
            "x": 0,
            "y": 0,
            "width": 10,
            "height": 10,
            "backend": "auto",
        },
    )
    assert r.status_code == 404


def test_ocr_selection_starts_job_demo_path(webapp_module, monkeypatch, tmp_path: Path):
    """POST succeeds; OCR runs on demo path when no backends are available."""
    from fastapi.testclient import TestClient

    from backend.app import app

    scans = tmp_path / "scans"
    scans.mkdir(parents=True)
    fn = "unit_scan_xy.png"
    Image.new("RGB", (50, 40), color="gray").save(scans / fn)

    monkeypatch.setattr(webapp_module, "project_root", tmp_path)
    monkeypatch.setattr(
        webapp_module,
        "backend_manager",
        MagicMock(get_available_backends=lambda: []),
    )

    client = TestClient(app)
    r = client.post(
        "/api/ocr_selection",
        data={
            "filename": fn,
            "x": 5,
            "y": 5,
            "width": 20,
            "height": 15,
            "backend": "auto",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("status") == "processing"
    assert "job_id" in body and str(body["job_id"]).startswith("scan_selection_")


def test_model_status_returns_structure(webapp_module, monkeypatch):
    """GET /api/models/status returns proper structure regardless of backend state."""
    from fastapi.testclient import TestClient

    from backend.app import app

    client = TestClient(app)
    r = client.get("/api/models/status")
    assert r.status_code == 200
    data = r.json()
    assert "backends" in data
    assert "available_count" in data
    assert "total_count" in data
    assert isinstance(data["backends"], dict)
    assert data["total_count"] >= 0


def test_model_status_with_no_backend_manager(webapp_module, monkeypatch):
    """GET /api/models/status works when backend_manager is None."""
    from fastapi.testclient import TestClient

    from backend.app import app

    monkeypatch.setattr(webapp_module, "backend_manager", None)
    client = TestClient(app)
    r = client.get("/api/models/status")
    assert r.status_code == 200
    data = r.json()
    assert data["total_count"] == 0
    assert data["available_count"] == 0


def test_model_download_unknown_backend(webapp_module, monkeypatch):
    """POST /api/models/download/{name} returns 404 for unknown backend."""
    from fastapi.testclient import TestClient

    from backend.app import app

    client = TestClient(app)
    r = client.post("/api/models/download/zxcvbn_not_real")
    assert r.status_code == 404


def test_get_download_progress_not_started(webapp_module, monkeypatch):
    """GET progress for a backend that was never triggered returns not_started."""
    from fastapi.testclient import TestClient

    from backend.app import app

    client = TestClient(app)
    r = client.get("/api/models/download/tesseract/progress")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") in ("not_started", "available")
