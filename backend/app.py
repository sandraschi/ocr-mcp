# MIT License
#
# Copyright (c) 2025 OCR-MCP Project
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
#
#
#
#

"""
OCR-MCP Web Application Backend
FastAPI server providing web interface for OCR-MCP functionality
"""

import asyncio
import collections
import concurrent.futures
import json
import logging
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
import uvicorn
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel


class MistralSettingsUpdate(BaseModel):
    """``api_key``: omit to leave unchanged; send empty string to clear."""

    api_key: str | None = None
    base_url: str | None = None


class MistralTestRequest(BaseModel):
    """Optional overrides for a one-off test (unsaved key in the form)."""

    api_key: str | None = None
    base_url: str | None = None


class BackendProbeRequest(BaseModel):
    """Probe one OCR backend: availability, optional model load, tiny sample image."""

    backend: str


# Single-thread executor for WIA: COM is thread-affine; one STA thread for all scanner ops.
_wia_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="wia_sta")

# Module-level singleton variables for FastAPI dependencies
FILE_DEPENDENCY = File()
FILE_LIST_DEPENDENCY = File()

# Max jobs to retain (prevents unbounded growth)
MAX_PROCESSING_JOBS = 500


def _prune_old_jobs():
    """Remove oldest completed/failed jobs when over limit."""
    if len(processing_jobs) <= MAX_PROCESSING_JOBS:
        return
    completed = [k for k, v in processing_jobs.items() if v.get("status") in ("completed", "failed")]
    to_remove = min(len(completed), len(processing_jobs) - MAX_PROCESSING_JOBS)
    if to_remove <= 0:
        return
    for k in completed[:to_remove]:
        processing_jobs.pop(k, None)


def _silence_third_party_loggers() -> None:
    """Raise log level for chatty libraries (HF, httpx, comtypes, …) on console and parents.

    Set ``OCR_VERBOSE_THIRD_PARTY_LOGS=1`` to keep their default verbosity.
    """
    if os.environ.get("OCR_VERBOSE_THIRD_PARTY_LOGS", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        return
    level = logging.WARNING
    for name in (
        "comtypes",
        "comtypes.client",
        "comtypes.client._code_cache",
        "httpx",
        "httpcore",
        "h11",
        "huggingface_hub",
        "transformers",
        "urllib3",
        "filelock",
        "PIL",
        "Pillow",
        "sentence_transformers",
        "torch",
        "torchvision",
        "accelerate",
        "bitsandbytes",
        "safetensors",
        "uvicorn.access",
        "multipart",
    ):
        logging.getLogger(name).setLevel(level)


class _RingNoiseFilter(logging.Filter):
    """Keep the webapp log ring focused on this app (not HF/httpx/comtypes spam)."""

    _DENY_PREFIXES = (
        "httpx",
        "httpcore",
        "huggingface_hub",
        "transformers",
        "urllib3",
        "comtypes",
        "h11",
        "filelock",
        "PIL",
        "Pillow",
        "sentence_transformers",
        "torch",
        "torchvision",
        "accelerate",
        "bitsandbytes",
        "safetensors",
        "uvicorn.access",
        "multipart",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        if os.environ.get("OCR_WEBAPP_LOG_RING_ALL", "").strip().lower() in (
            "1",
            "true",
            "yes",
        ):
            return True
        name = record.name or ""
        for p in self._DENY_PREFIXES:
            if name == p or name.startswith(f"{p}."):
                return False
        return True


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
_silence_third_party_loggers()

# In-memory ring buffer for the webapp Logger page (last N formatted lines)
MAX_SERVER_LOG_LINES = 500
_server_log_lines: collections.deque[str] = collections.deque(maxlen=MAX_SERVER_LOG_LINES)


class _RingMemoryHandler(logging.Handler):
    """Append formatted log records to an in-memory deque for /api/server_logs."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            _server_log_lines.append(self.format(record))
        except Exception:
            # Stderr via logging internals; avoids recursion into this handler
            self.handleError(record)


_mem_handler = _RingMemoryHandler()
_mem_handler.setLevel(logging.INFO)
_mem_handler.addFilter(_RingNoiseFilter())
_mem_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
logging.getLogger().addHandler(_mem_handler)

# Initialize FastAPI app
app = FastAPI(
    title="OCR-MCP Web Interface",
    description="Web interface for OCR-MCP document processing",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:10858",
        "http://127.0.0.1:10858",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    ],
    allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and React app
# Get the correct path relative to this script's location
script_dir = Path(__file__).parent
project_root = script_dir.parent
dist_dir = project_root / "frontend" / "dist"

# React app will be mounted at the end of the file after all API routes

# Keep templates as None since we're serving the React app directly
templates = None

# Initialize MCP client

demo_mode = False  # Real scanner functionality enabled

# Global state for processing jobs
processing_jobs: dict[str, dict[str, Any]] = {}

# Initialize BackendManager globally
backend_manager = None
scanner_manager = None

# Pip auto-install for torch/transformers/Paddle runs inside run_ocr_startup_bootstrap when
# OCR_AUTO_INSTALL_DEPS=1 (see ocr_mcp.utils.startup_bootstrap).

try:
    from ocr_mcp.backends.scanner.scanner_manager import ScannerManager
    from ocr_mcp.backends.scanner.wia_scanner import ScanSettings
    from ocr_mcp.core.backend_manager import BackendManager
    from ocr_mcp.core.config import OCRConfig
    from ocr_mcp.utils.startup_bootstrap import run_ocr_startup_bootstrap

    config = OCRConfig()
    try:
        run_ocr_startup_bootstrap(config)
    except Exception as boot_e:
        logger.debug("OCR startup bootstrap: %s", boot_e)
    backend_manager = BackendManager(config)

    # Initialize Scanner Manager
    scanner_manager = ScannerManager()

    logger.info("Global BackendManager and ScannerManager initialized")
except Exception as e:
    import traceback

    logger.error("Failed to initialize global managers: %s", e)
    traceback.print_exc()


@app.on_event("startup")
async def startup_event():
    """Initialization on startup"""
    if demo_mode:
        logger.info("Running in demo mode")
        return

    # Re-apply after any late-importing deps may have tweaked loggers
    _silence_third_party_loggers()
    logger.info("Backend starting (real mode)...")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    for _jid, job in list(processing_jobs.items()):
        for key in ("file_path", "file_paths"):
            paths = job.get(key)
            if paths is None:
                continue
            for path in paths if isinstance(paths, list) else [paths]:
                try:
                    if path and os.path.exists(path):
                        os.unlink(path)
                except OSError:
                    pass


# Remove the home route since the React app is now served statically
# The frontend will handle all non-API routes


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    if demo_mode:
        return {
            "status": "healthy",
            "mcp_connected": True,
            "mcp_status": "demo_mode",
            "demo_mode": True,
            "instructions": (
                "Running in demo mode - start OCR-MCP server for full functionality: python -m src.ocr_mcp.server"
            ),
            "version": "0.1.0",
        }

    return {
        "status": "healthy" if backend_manager else "degraded",
        "backend_initialized": backend_manager is not None,
        "scanner_initialized": scanner_manager is not None,
        "demo_mode": False,
        "version": "0.1.0",
    }


@app.get("/api/server_logs")
async def get_server_logs(limit: int = 200):
    """Recent backend log lines for the webapp Logger page (in-memory ring buffer)."""
    lim = max(1, min(limit, MAX_SERVER_LOG_LINES))
    lines = list(_server_log_lines)[-lim:]
    logger.debug(
        "server_logs request limit_param=%s effective=%s returned=%s buffer_total=%s",
        limit,
        lim,
        len(lines),
        len(_server_log_lines),
    )
    return {"lines": lines, "count": len(lines), "max": MAX_SERVER_LOG_LINES}


def _crop_scanned_region_sync(
    file_path: Path, x: int, y: int, width: int, height: int, job_id: str, scans_dir: Path
) -> tuple[str, str]:
    """Crop a region from a scan on disk; return (crop_filename, absolute_crop_path_str)."""
    with Image.open(file_path) as img:
        left = max(0, x)
        top = max(0, y)
        right = min(img.width, x + width)
        bottom = min(img.height, y + height)

        if right <= left or bottom <= top:
            raise ValueError("Invalid crop dimensions")

        cropped_img = img.crop((left, top, right, bottom))
        crop_filename = f"crop_{job_id}.png"
        crop_path = scans_dir / crop_filename
        cropped_img.save(crop_path, format="PNG")
    return crop_filename, str(crop_path)


@app.post("/api/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = FILE_DEPENDENCY,
    ocr_mode: str = Form("text"),
    backend: str = Form("auto"),
):
    """Upload and process a file"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        _prune_old_jobs()
        job_id = f"job_{uuid.uuid4().hex[:12]}"

        # Store job info
        processing_jobs[job_id] = {
            "status": "processing",
            "filename": file.filename,
            "file_path": temp_file_path,
            "ocr_mode": ocr_mode,
            "backend": backend,
            "result": None,
            "error": None,
        }

        # Use real OCR when backend_manager available, else demo
        if backend_manager and backend_manager.get_available_backends():
            background_tasks.add_task(process_file_background, job_id, temp_file_path, ocr_mode, backend)
        else:
            background_tasks.add_task(process_file_demo, job_id, temp_file_path, file.filename, ocr_mode, backend)

        return {"job_id": job_id, "status": "processing"}

    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    """Get processing job status"""
    if job_id not in processing_jobs:
        raise HTTPException(
            status_code=404,
            detail=(
                "Job not found — it may have been pruned after many newer jobs, "
                "or the server was restarted (in-memory jobs are not persisted)."
            ),
        )

    job = processing_jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "filename": job["filename"],
        "result": job["result"],
        "error": job["error"],
    }


@app.post("/api/process_batch")
async def process_batch(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = FILE_LIST_DEPENDENCY,
    ocr_mode: str = Form("text"),
    backend: str = Form("auto"),
):
    """Process multiple files in batch"""
    try:
        file_paths = []
        filenames = []

        for file in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
                content = await file.read()
                temp_file.write(content)
                file_paths.append(temp_file.name)
                filenames.append(file.filename)

        _prune_old_jobs()
        job_id = f"batch_job_{uuid.uuid4().hex[:12]}"

        # Store job info
        processing_jobs[job_id] = {
            "status": "processing",
            "filenames": filenames,
            "file_paths": file_paths,
            "ocr_mode": ocr_mode,
            "backend": backend,
            "result": None,
            "error": None,
        }

        # Use real OCR when backend_manager available, else demo
        if backend_manager and backend_manager.get_available_backends():
            background_tasks.add_task(process_batch_background, job_id, file_paths, ocr_mode, backend)
        else:
            background_tasks.add_task(process_batch_demo, job_id, file_paths, filenames, ocr_mode, backend)

        return {"job_id": job_id, "status": "processing", "file_count": len(files)}

    except Exception as e:
        logger.error(f"Failed to process batch: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/backends")
async def get_backends():
    """Get available OCR backends"""
    if demo_mode:
        return {
            "backends": [
                {
                    "name": "paddleocr-vl",
                    "available": True,
                    "description": "Baidu PaddleOCR-VL-1.5 — Jan 2026 SOTA, 94.5% OmniDocBench",
                },
                {
                    "name": "deepseek-ocr2",
                    "available": True,
                    "description": "DeepSeek-OCR-2 — Jan 2026, Visual Causal Flow",
                },
                {
                    "name": "olmocr-2",
                    "available": True,
                    "description": "Allen AI olmOCR-2 — academic PDFs, math, multi-column",
                },
                {
                    "name": "mistral-ocr",
                    "available": True,
                    "description": "Mistral OCR API — 94.9% accuracy",
                },
                {"name": "got-ocr", "available": True, "description": "GOT-OCR2.0 — fast, lean"},
                {
                    "name": "qwen-layered",
                    "available": True,
                    "description": "Qwen2.5-VL — complex layouts",
                },
                {
                    "name": "tesseract",
                    "available": True,
                    "description": "Tesseract OCR — CPU backstop",
                },
            ],
            "default_backend": "paddleocr-vl",
        }

    if not backend_manager:
        raise HTTPException(
            status_code=503,
            detail="Backend manager not initialized.",
        )
    try:
        backend_info = []
        for name in sorted(backend_manager.backend_registry.keys()):
            meta = backend_manager.backend_registry[name]
            desc = meta.get("description", f"{name} OCR backend")
            backend = backend_manager.get_backend(name)
            available = bool(backend and backend.is_available())
            if backend and hasattr(backend, "get_capabilities"):
                try:
                    caps = backend.get_capabilities()
                    if isinstance(caps, dict) and caps.get("description"):
                        desc = caps["description"]
                except Exception as cap_err:
                    logger.debug("get_capabilities failed for %s: %s", name, cap_err)
            backend_info.append(
                {
                    "name": name,
                    "available": available,
                    "description": desc,
                }
            )
        return {"backends": backend_info}
    except Exception as e:
        logger.error(f"Failed to get backends: {e}")
        raise HTTPException(status_code=500, detail=f"{e!s}") from e


@app.get("/api/llm/providers")
async def get_llm_providers():
    """Discover local LLM providers (Ollama, LM Studio)."""
    providers = []
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://127.0.0.1:11434/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                providers.append(
                    {
                        "id": "ollama",
                        "label": "Ollama",
                        "base_url": "http://127.0.0.1:11434/v1",
                        "models": models,
                        "needs_key": False,
                    }
                )
    except Exception:
        providers.append(
            {
                "id": "ollama",
                "label": "Ollama",
                "base_url": "http://127.0.0.1:11434/v1",
                "models": [],
                "needs_key": False,
            }
        )
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://127.0.0.1:1234/v1/models")
            if resp.status_code == 200:
                data = resp.json()
                models = [m["id"] for m in data.get("data", [])]
                providers.append(
                    {
                        "id": "lmstudio",
                        "label": "LM Studio",
                        "base_url": "http://127.0.0.1:1234/v1",
                        "models": models,
                        "needs_key": False,
                    }
                )
    except Exception:
        providers.append(
            {
                "id": "lmstudio",
                "label": "LM Studio",
                "base_url": "http://127.0.0.1:1234/v1",
                "models": [],
                "needs_key": False,
            }
        )
    return {"providers": providers}


@app.post("/api/backends/test")
async def post_backend_probe(
    body: BackendProbeRequest,
    timeout: float = Query(120, ge=15, le=600, description="Seconds to wait for load + sample OCR"),
):
    """Run a live probe on a single backend (no auto-fallback). Heavy models may use most of the timeout."""
    if demo_mode:
        return {
            "success": True,
            "backend": body.backend.strip() or "unknown",
            "message": "Demo mode — no live probe.",
            "phase": "demo",
        }
    if not backend_manager:
        raise HTTPException(status_code=503, detail="Backend manager not initialized.")
    name = body.backend.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Missing backend name")

    try:
        result = await asyncio.wait_for(
            backend_manager.probe_backend(name),
            timeout=timeout,
        )
    except TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"Backend probe timed out after {int(timeout)}s (large model download or slow GPU).",
        ) from None
    return result


@app.get("/api/settings/mistral")
async def get_mistral_settings():
    """Return Mistral OCR API status (never expose full API key)."""
    if demo_mode or not backend_manager:
        return {
            "key_configured": False,
            "base_url": "https://api.mistral.ai/v1",
            "key_hint": None,
        }
    key = config.mistral_api_key
    hint = None
    if key and len(key) >= 4:
        hint = f"...{key[-4:]}"
    return {
        "key_configured": bool(key),
        "base_url": config.mistral_base_url,
        "key_hint": hint,
    }


@app.post("/api/settings/mistral")
async def post_mistral_settings(body: MistralSettingsUpdate):
    """Update Mistral API key and/or base URL; reload mistral-ocr backend."""
    if demo_mode:
        raise HTTPException(status_code=400, detail="Demo mode: settings not persisted")
    if not backend_manager:
        raise HTTPException(status_code=503, detail="Backend manager not initialized")

    updates = body.model_dump(exclude_unset=True)
    if "api_key" in updates:
        raw = updates["api_key"]
        config.mistral_api_key = (raw.strip() or None) if isinstance(raw, str) else None
        if config.mistral_api_key:
            os.environ["MISTRAL_API_KEY"] = config.mistral_api_key
        else:
            os.environ.pop("MISTRAL_API_KEY", None)
    if "base_url" in updates and isinstance(updates["base_url"], str):
        bu = updates["base_url"].strip()
        if bu:
            config.mistral_base_url = bu

    backend_manager.invalidate_backend("mistral-ocr")

    key = config.mistral_api_key
    hint = f"...{key[-4:]}" if key and len(key) >= 4 else None
    return {
        "success": True,
        "key_configured": bool(key),
        "base_url": config.mistral_base_url,
        "key_hint": hint,
    }


@app.post("/api/settings/mistral/test")
async def test_mistral_api_key(body: MistralTestRequest = MistralTestRequest()):
    """Validate Mistral API key via GET ``/models`` (lightweight, same as backend probe)."""
    if demo_mode:
        raise HTTPException(status_code=400, detail="Demo mode: API test unavailable")
    if not backend_manager:
        raise HTTPException(status_code=503, detail="Backend manager not initialized")

    raw_key = body.api_key.strip() if isinstance(body.api_key, str) else ""
    key = raw_key or (config.mistral_api_key or "")
    if not key:
        raise HTTPException(
            status_code=400,
            detail="No API key to test: paste a key or save one first",
        )

    raw_base = body.base_url.strip() if isinstance(body.base_url, str) else ""
    base = (raw_base or config.mistral_base_url or "https://api.mistral.ai/v1").rstrip("/")
    url = f"{base}/models"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {key}"},
            )
    except httpx.TimeoutException:
        return {
            "valid": False,
            "message": "Request timed out — check base URL and network",
            "http_status": None,
        }
    except httpx.RequestError as e:
        return {
            "valid": False,
            "message": f"Connection failed: {e!s}",
            "http_status": None,
        }

    if response.status_code == 200:
        return {
            "valid": True,
            "message": "API key accepted (models list reachable)",
            "http_status": 200,
        }
    if response.status_code == 401:
        return {
            "valid": False,
            "message": "Invalid or unauthorized API key",
            "http_status": 401,
        }
    if response.status_code == 403:
        return {
            "valid": False,
            "message": "Forbidden — key may lack required scope",
            "http_status": 403,
        }
    if response.status_code == 429:
        return {
            "valid": False,
            "message": "Rate limited — try again shortly",
            "http_status": 429,
        }
    snippet = (response.text or "")[:200].replace("\n", " ")
    return {
        "valid": False,
        "message": f"Unexpected response ({response.status_code}){': ' + snippet if snippet else ''}",
        "http_status": response.status_code,
    }


@app.post("/api/optimize")
async def optimize_processing(
    background_tasks: BackgroundTasks,
    file: UploadFile = FILE_DEPENDENCY,
    target_quality: float = Form(0.8),
    max_attempts: int = Form(3),
):
    """Auto-optimize OCR processing for best quality"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        _prune_old_jobs()
        job_id = f"optimize_{uuid.uuid4().hex[:12]}"

        # Store job info
        processing_jobs[job_id] = {
            "status": "processing",
            "filename": file.filename,
            "file_path": temp_file_path,
            "target_quality": target_quality,
            "max_attempts": max_attempts,
            "result": None,
            "error": None,
        }

        # Process in background
        background_tasks.add_task(optimize_background, job_id, temp_file_path, target_quality, max_attempts)

        return {"job_id": job_id, "status": "processing"}

    except Exception as e:
        logger.error(f"Failed to start optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/convert")
async def convert_format(
    background_tasks: BackgroundTasks,
    file: UploadFile = FILE_DEPENDENCY,
    target_format: str = Form("json"),
    ocr_mode: str = Form("auto"),
    backend: str = Form("auto"),
):
    """Convert document format with optional OCR"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        _prune_old_jobs()
        job_id = f"convert_{uuid.uuid4().hex[:12]}"

        # Store job info
        processing_jobs[job_id] = {
            "status": "processing",
            "filename": file.filename,
            "file_path": temp_file_path,
            "target_format": target_format,
            "ocr_mode": ocr_mode,
            "backend": backend,
            "result": None,
            "error": None,
        }

        # Process in background
        background_tasks.add_task(convert_background, job_id, temp_file_path, target_format, ocr_mode, backend)

        return {"job_id": job_id, "status": "processing"}

    except Exception as e:
        logger.error(f"Failed to start conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/export")
async def export_results(data: dict[str, Any]):
    """Export processed results in various formats"""
    try:
        export_type = data.get("export_type", "json")
        content = data.get("content", {})
        filename = data.get("filename", f"export_{len(processing_jobs)}")

        # Generate export based on type
        if export_type == "json":
            export_content = json.dumps(content, indent=2)
            media_type = "application/json"
            file_extension = "json"
        elif export_type == "xml":
            # Simple XML conversion
            export_content = dict_to_xml(content)
            media_type = "application/xml"
            file_extension = "xml"
        elif export_type == "csv":
            # Convert structured data to CSV
            export_content = dict_to_csv(content)
            media_type = "text/csv"
            file_extension = "csv"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported export type: {export_type}")

        return {
            "filename": f"{filename}.{file_extension}",
            "content": export_content,
            "media_type": media_type,
            "size": len(export_content),
        }

    except Exception as e:
        logger.error(f"Failed to export results: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/pipelines")
async def get_pipelines():
    """Get available processing pipelines"""
    # Return predefined pipelines
    return {
        "pipelines": [
            {
                "id": "basic_ocr",
                "name": "Basic OCR",
                "description": "Simple OCR processing",
                "steps": ["deskew_image", "enhance_image", "process_document"],
            },
            {
                "id": "quality_focused",
                "name": "Quality Focused",
                "description": "Multiple OCR attempts for high accuracy",
                "steps": [
                    "deskew_image",
                    "enhance_image",
                    "process_document",
                    "assess_ocr_quality",
                ],
            },
            {
                "id": "archive_ready",
                "name": "Archive Ready",
                "description": "Convert to searchable PDF with metadata",
                "steps": [
                    "deskew_image",
                    "enhance_image",
                    "process_document",
                    "convert_image_format",
                ],
            },
        ]
    }


@app.post("/api/pipelines/execute")
async def execute_pipeline(
    background_tasks: BackgroundTasks,
    pipeline_id: str = Form(...),
    file: UploadFile = FILE_DEPENDENCY,
    backend: str = Form("auto"),
):
    """Execute a processing pipeline"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        _prune_old_jobs()
        job_id = f"pipeline_{uuid.uuid4().hex[:12]}"

        # Store job info
        processing_jobs[job_id] = {
            "status": "processing",
            "filename": file.filename,
            "file_path": temp_file_path,
            "pipeline_id": pipeline_id,
            "result": None,
            "error": None,
        }

        # Process in background
        background_tasks.add_task(execute_pipeline_background, job_id, pipeline_id, temp_file_path, backend)

        return {"job_id": job_id, "status": "processing"}

    except Exception as e:
        logger.error(f"Failed to execute pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


def _store_ocr_job_result(job_id: str, result: dict[str, Any]) -> None:
    """Mark job completed or failed from an OCR backend result dict."""
    success = result.get("success", True)
    text = (result.get("text") or "").strip()
    err = result.get("error")
    if success is False or err:
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(err or "OCR reported failure")
        processing_jobs[job_id]["result"] = result
    elif not text:
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = "OCR returned no text (empty or unreadable)"
        processing_jobs[job_id]["result"] = result
    else:
        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["error"] = None
        processing_jobs[job_id]["result"] = result


async def process_file_background(job_id: str, file_path: str, ocr_mode: str, backend: str):
    """Process single file in background"""
    try:
        if not backend_manager:
            raise Exception("Backend manager not initialized")

        result = await backend_manager.process_with_backend(backend_name=backend, image_path=file_path, mode=ocr_mode)

        _store_ocr_job_result(job_id, result)

        # Clean up temp file
        try:
            os.unlink(file_path)
        except OSError:
            pass

    except Exception as e:
        logger.error(f"Failed to process file {job_id}: {e}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)
        try:
            os.unlink(file_path)
        except OSError:
            pass


async def process_batch_background(job_id: str, file_paths: list[str], ocr_mode: str, backend: str):
    """Process batch files in background"""
    try:
        if not backend_manager:
            raise Exception("Backend manager not initialized")

        results = []
        for path in file_paths:
            res = await backend_manager.process_with_backend(backend_name=backend, image_path=path, mode=ocr_mode)
            results.append(res)

        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["result"] = {
            "total_files": len(file_paths),
            "successful": sum(1 for r in results if r.get("success")),
            "results": results,
        }

        # Clean up temp files
        for file_path in file_paths:
            try:
                os.unlink(file_path)
            except OSError:
                pass

    except Exception as e:
        logger.error(f"Failed to process batch {job_id}: {e}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)
        for fp in file_paths:
            try:
                os.unlink(fp)
            except OSError:
                pass


async def process_file_demo(job_id: str, file_path: str, filename: str, ocr_mode: str, backend: str):
    """Demo processing - simulate OCR results"""
    try:
        logger.info(f"Starting demo processing for job {job_id}, file {filename}")
        # Simulate processing time
        await asyncio.sleep(2)
        logger.info(f"Demo processing sleep completed for job {job_id}")

        # Generate mock OCR results based on filename
        if "pdf" in filename.lower():
            mock_text = (
                f"This is extracted text from {filename}.\n\n"
                f"Document processed using {backend} backend in {ocr_mode} mode.\n\n"
                "This is a demo result showing how the OCR-MCP webapp works.\n\n"
                "Features demonstrated:\n"
                "- Multi-backend OCR support\n"
                "- Quality assessment\n"
                "- Format conversion\n"
                "- Batch processing\n\n"
                "Thank you for trying OCR-MCP!"
            )
        else:
            mock_text = (
                f"Image {filename} processed successfully.\n\n"
                f"OCR Results:\n"
                f"Sample text extracted from the image.\n"
                f"Confidence: 95%\n"
                f"Backend: {backend}\n"
                f"Mode: {ocr_mode}"
            )

        mock_result = {
            "text": mock_text,
            "quality_score": 0.87,
            "backend_used": backend,
            "processing_time": 1.5,
            "confidence": 0.92,
            "demo_mode": True,
        }

        logger.info(f"Setting job {job_id} to completed with result")
        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["result"] = mock_result
        logger.info(f"Demo processing completed successfully for job {job_id}")

        # Clean up temp file
        try:
            os.unlink(file_path)
        except OSError:
            pass

    except Exception as e:
        logger.error(f"Failed to process demo file {job_id}: {e}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)
        try:
            os.unlink(file_path)
        except OSError:
            pass


async def process_batch_demo(
    job_id: str,
    file_paths: list[str],
    filenames: list[str],
    ocr_mode: str,
    backend: str,
):
    """Demo batch processing - simulate results for multiple files"""
    try:
        results = []

        for i, filename in enumerate(filenames):
            # Simulate processing time for each file
            await asyncio.sleep(0.5)

            # Generate mock results
            mock_result = {
                "filename": filename,
                "text": (
                    f"Extracted text from {filename} (file {i + 1} of {len(filenames)}).\n\n"
                    f"Processed with {backend} in {ocr_mode} mode.\n"
                    "Demo batch processing result."
                ),
                "quality_score": 0.85 + (i * 0.02),  # Vary quality slightly
                "processing_time": 1.0 + (i * 0.1),
                "status": "completed",
                "demo_mode": True,
            }
            results.append(mock_result)

        batch_result = {
            "total_files": len(filenames),
            "successful": len(filenames),
            "failed": 0,
            "results": results,
            "average_quality": 0.87,
            "total_time": len(filenames) * 1.2,
            "demo_mode": True,
        }

        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["result"] = batch_result

        # Clean up temp files
        for fp in file_paths:
            try:
                os.unlink(fp)
            except OSError:
                pass

    except Exception as e:
        logger.error(f"Failed to process demo batch {job_id}: {e}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)
        for fp in file_paths:
            try:
                os.unlink(fp)
            except OSError:
                pass


async def optimize_background(job_id: str, file_path: str, target_quality: float, max_attempts: int):
    """Auto-optimize OCR processing in background"""
    try:
        # Try different backends and settings to achieve target quality
        best_result = None
        best_quality = 0.0

        backends = [
            "auto",
            "paddleocr-vl",
            "deepseek-ocr2",
            "olmocr-2",
            "mistral-ocr",
            "got-ocr",
            "qwen-layered",
            "tesseract",
        ]
        modes = ["auto", "text", "format"]

        for attempt in range(max_attempts):
            for backend in backends:
                for mode in modes:
                    try:
                        if not backend_manager:
                            continue

                        result = await backend_manager.process_with_backend(
                            backend_name=backend,
                            image_path=file_path,
                            mode=mode if mode != "auto" else "text",
                        )

                        if not result.get("success"):
                            continue

                        # Check quality score (mock for now)
                        quality_score = result.get("quality_score", 0.5)

                        if quality_score >= target_quality:
                            processing_jobs[job_id]["status"] = "completed"
                            processing_jobs[job_id]["result"] = result
                            return

                        if quality_score > best_quality:
                            best_quality = quality_score
                            best_result = result

                    except Exception as e:
                        logger.warning(f"Optimization attempt {attempt + 1} with {backend}/{mode} failed: {e}")
                        continue

        # Return best result found
        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["result"] = best_result or {"error": "Could not achieve target quality"}

        # Clean up temp file
        try:
            os.unlink(file_path)
        except OSError:
            pass

    except Exception as e:
        logger.error(f"Failed to optimize {job_id}: {e}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)
        try:
            os.unlink(file_path)
        except OSError:
            pass


async def convert_background(job_id: str, file_path: str, target_format: str, ocr_mode: str, backend: str):
    """Convert document format in background"""
    try:
        ocr_result = None
        if target_format in ["pdf", "docx"]:
            if not backend_manager:
                raise Exception("Backend manager not initialized")

            ocr_result = await backend_manager.process_with_backend(
                backend_name=backend,
                image_path=file_path,
                mode=ocr_mode if ocr_mode != "auto" else "text",
            )

        # Convert format logic (simplified fallback for now)
        # In a real scenario, this would call a PDF converter backend
        result = {
            "status": "completed",
            "target_path": f"{file_path}.{target_format}",
            "format": target_format,
            "text_included": ocr_result is not None and ocr_result.get("success", False),
        }

        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["result"] = result

        # Clean up temp file
        try:
            os.unlink(file_path)
        except OSError:
            pass

    except Exception as e:
        logger.error(f"Failed to convert {job_id}: {e}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)
        try:
            os.unlink(file_path)
        except OSError:
            pass


async def execute_pipeline_background(job_id: str, pipeline_id: str, file_path: str, backend: str = "auto"):
    """Execute processing pipeline in background"""
    try:
        # Define pipeline steps
        pipelines = {
            "basic_ocr": ["deskew_image", "enhance_image", "process_document"],
            "quality_focused": [
                "deskew_image",
                "enhance_image",
                "process_document",
                "assess_ocr_quality",
            ],
            "archive_ready": [
                "deskew_image",
                "enhance_image",
                "process_document",
                "convert_image_format",
            ],
        }

        steps = pipelines.get(pipeline_id, ["process_document"])
        results = {}

        # Execute each step in sequence
        for step in steps:
            try:
                if step == "process_document":
                    if not backend_manager:
                        raise Exception("Backend manager not initialized")
                    result = await backend_manager.process_with_backend(
                        backend_name=backend,
                        image_path=file_path,
                        mode="text",
                    )
                elif step == "deskew_image":
                    # Placeholder for deskew logic
                    result = {"status": "skipped", "reason": "Not implemented"}
                elif step == "enhance_image":
                    # Placeholder for enhance logic
                    result = {"status": "skipped", "reason": "Not implemented"}
                elif step == "assess_ocr_quality":
                    # Placeholder for quality assessment
                    result = {"quality_score": 0.9}
                elif step == "convert_image_format":
                    # Placeholder for conversion
                    result = {"status": "skipped", "reason": "Not implemented"}

                results[step] = result

            except Exception as e:
                logger.warning(f"Pipeline step {step} failed: {e}")
                results[step] = {"error": str(e)}

        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["result"] = {
            "pipeline_id": pipeline_id,
            "steps_executed": steps,
            "results": results,
        }

        # Clean up temp file
        try:
            os.unlink(file_path)
        except OSError:
            pass

    except Exception as e:
        logger.error(f"Pipeline execution failed for {job_id}: {e}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)
        try:
            os.unlink(file_path)
        except OSError:
            pass


# End of processing jobs


# Utility functions for export
def dict_to_xml(data: dict[str, Any], root_name: str = "data") -> str:
    """Convert dictionary to XML string"""

    def _dict_to_xml(data: Any, key: str | None = None) -> str:
        if isinstance(data, dict):
            xml_parts = []
            for k, v in data.items():
                xml_parts.append(f"<{k}>{_dict_to_xml(v)}</{k}>")
            return "".join(xml_parts)
        elif isinstance(data, list):
            xml_parts = []
            item_name = key[:-1] if key and key.endswith("s") else "item"
            for item in data:
                xml_parts.append(f"<{item_name}>{_dict_to_xml(item)}</{item_name}>")
            return "".join(xml_parts)
        else:
            return str(data)

    return f"<?xml version='1.0' encoding='UTF-8'?>\n<{root_name}>{_dict_to_xml(data)}</{root_name}>"


def dict_to_csv(data: dict[str, Any]) -> str:
    """Convert dictionary to CSV string"""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Simple flattening for CSV
    if isinstance(data, dict):
        writer.writerow(["Key", "Value"])
        for key, value in data.items():
            writer.writerow([key, str(value)])
    elif isinstance(data, list) and data and isinstance(data[0], dict):
        if data:
            headers = list(data[0].keys())
            writer.writerow(headers)
            for row in data:
                writer.writerow([row.get(h, "") for h in headers])

    return output.getvalue()


# --- Scanner API Endpoints ---


@app.get("/api/scanners")
async def get_scanners():
    """Get list of available scanners. WIA discovery runs in a thread (STA) so flatbed is found."""
    if not scanner_manager:
        return {"scanners": [], "error": "Scanner manager not initialized"}

    try:
        # WIA is thread-affine: use single dedicated STA thread so every request sees devices.
        loop = asyncio.get_event_loop()
        scanners = await loop.run_in_executor(
            _wia_executor,
            lambda: scanner_manager.discover_scanners(True),
        )
        if not scanners:
            return {
                "scanners": [],
                "error": "No scanners found. Check USB connection and WIA drivers.",
            }

        scanner_list = [
            {
                "device_id": s.device_id,
                "name": s.name,
                "manufacturer": s.manufacturer,
                "type": s.device_type,
                "max_dpi": s.max_dpi,
                "supports_adf": s.supports_adf,
                "supports_duplex": s.supports_duplex,
                "status": "ready",
            }
            for s in scanners
        ]
        return {"scanners": scanner_list}
    except Exception as e:
        logger.error("Error fetching scanners: %s", e)
        return {"scanners": [], "error": str(e)}


@app.post("/api/scan")
async def scan_document(
    device_id: str = Form(...),
    dpi: int = Form(300),
    color_mode: str = Form("Color"),
    paper_size: str = Form("A4"),
):
    """Perform a document scan"""
    if not scanner_manager:
        raise HTTPException(status_code=503, detail="Scanner manager not initialized")

    try:
        # Create settings object
        settings = ScanSettings(dpi=dpi, color_mode=color_mode, paper_size=paper_size)

        logger.info("Starting scan on %s with settings: %s", device_id, settings)

        # Same WIA STA thread as discovery so scan sees the device.
        loop = asyncio.get_event_loop()
        image = await loop.run_in_executor(
            _wia_executor,
            lambda: scanner_manager.scan_document(device_id, settings),
        )

        if not image:
            return {
                "success": False,
                "message": "Scan failed or returned no image",
                "device_id": device_id,
            }

        # Save image to scans folder in project root
        scans_dir = project_root / "scans"
        scans_dir.mkdir(exist_ok=True)

        import uuid

        filename = f"scan_{uuid.uuid4().hex}.png"
        file_path = scans_dir / filename

        image.save(file_path, format="PNG")

        image_url = f"/static/scans/{filename}"

        return {
            "success": True,
            "device_id": device_id,
            "image_path": image_url,
            "image_info": {
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "filename": filename,
            },
            "settings": {
                "dpi": dpi,
                "color_mode": color_mode,
                "paper_size": paper_size,
            },
            "message": "Scan completed successfully",
        }

    except Exception as e:
        logger.error(f"Scan error: {e}")
        return {"success": False, "message": str(e), "device_id": device_id}


@app.post("/api/ocr_scanned")
async def ocr_scanned_document(
    background_tasks: BackgroundTasks,
    filename: str = Form(...),
    ocr_mode: str = Form("text"),
    backend: str = Form("auto"),
):
    """Process an already scanned document with OCR"""
    try:
        scans_dir = project_root / "scans"
        file_path = scans_dir / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Scanned file {filename} not found")

        _prune_old_jobs()
        job_id = f"scan_ocr_{uuid.uuid4().hex[:12]}"

        # Store job info
        processing_jobs[job_id] = {
            "status": "processing",
            "filename": filename,
            "file_path": str(file_path),
            "ocr_mode": ocr_mode,
            "backend": backend,
            "result": None,
            "error": None,
        }

        # Process in background (note: we don't delete the file after processing for scans)
        if backend_manager and backend_manager.get_available_backends():
            background_tasks.add_task(process_scanned_background, job_id, str(file_path), ocr_mode, backend)
        else:
            # demo mode
            background_tasks.add_task(process_file_demo, job_id, str(file_path), filename, ocr_mode, backend)

        return {"job_id": job_id, "status": "processing"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start OCR for scanned file: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/ocr_selection")
async def ocr_selection(
    background_tasks: BackgroundTasks,
    filename: str = Form(...),
    x: int = Form(...),
    y: int = Form(...),
    width: int = Form(...),
    height: int = Form(...),
    ocr_mode: str = Form("text"),
    backend: str = Form("auto"),
):
    """Process a specific selected region of a scanned document with OCR"""
    try:
        scans_dir = project_root / "scans"
        file_path = scans_dir / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Scanned file {filename} not found")

        # Create a new job ID
        _prune_old_jobs()
        job_id = f"scan_selection_{uuid.uuid4().hex[:12]}"

        # PIL is synchronous and can block the event loop on large scans — run off-loop.
        loop = asyncio.get_event_loop()
        logger.info(
            "OCR selection crop start job=%s file=%s region=%s,%s %sx%s",
            job_id,
            filename,
            x,
            y,
            width,
            height,
        )
        try:
            crop_filename, crop_path_str = await loop.run_in_executor(
                None,
                lambda: _crop_scanned_region_sync(file_path, x, y, width, height, job_id, scans_dir),
            )
        except Exception as crop_error:
            logger.error("Failed to crop image for OCR: %s", crop_error)
            raise HTTPException(status_code=400, detail=f"Failed to crop image: {crop_error}") from crop_error
        logger.info("OCR selection crop done job=%s crop=%s", job_id, crop_filename)

        # Store job info
        processing_jobs[job_id] = {
            "status": "processing",
            "filename": crop_filename,
            "file_path": crop_path_str,
            "ocr_mode": ocr_mode,
            "backend": backend,
            "result": None,
            "error": None,
        }

        # Process in background (process_scanned_background uses the new crop file)
        if backend_manager and backend_manager.get_available_backends():
            background_tasks.add_task(process_scanned_background, job_id, crop_path_str, ocr_mode, backend)
        else:
            # demo mode
            background_tasks.add_task(process_file_demo, job_id, crop_path_str, crop_filename, ocr_mode, backend)

        return {"job_id": job_id, "status": "processing"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start OCR for selection: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


async def process_scanned_background(job_id: str, file_path: str, ocr_mode: str, backend: str):
    """Process scanned file in background without deleting original"""
    try:
        if not backend_manager:
            raise Exception("Backend manager not initialized")

        result = await backend_manager.process_with_backend(backend_name=backend, image_path=file_path, mode=ocr_mode)

        _store_ocr_job_result(job_id, result)

    except Exception as e:
        logger.error(f"Failed to process scanned file {job_id}: {e}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)


# --- Model / Backend Status & Download Endpoints ---

model_downloads: dict[str, dict[str, Any]] = {}


def _backend_meta(name: str) -> dict[str, str]:
    """Look up description + model_size from the registry (no import)."""
    if not backend_manager:
        return {"description": f"{name} OCR backend", "model_size": "unknown"}
    meta = backend_manager.backend_registry.get(name, {})
    return {
        "description": meta.get("description", f"{name} OCR backend"),
        "model_size": meta.get("model_size", "unknown"),
    }


def _collect_model_status() -> dict[str, Any]:
    """Gather status for every registered backend without triggering lazy loads."""
    backends_status: dict[str, dict[str, Any]] = {}
    available_count = 0
    total_count = 0
    if not backend_manager:
        return {"backends": {}, "available_count": 0, "total_count": 0}

    for name, _meta in backend_manager.backend_registry.items():
        total_count += 1
        meta_info = _backend_meta(name)

        # Check if already loaded or mock
        existing = backend_manager.backends.get(name)
        if existing is not None and existing is not None:
            caps: dict[str, Any] = {}
            if hasattr(existing, "get_capabilities") and existing.is_available():
                try:
                    caps = existing.get_capabilities()
                except Exception:
                    pass
            backends_status[name] = {
                "name": name,
                "description": meta_info["description"],
                "model_size": meta_info["model_size"],
                "available": existing.is_available(),
                "capabilities": caps,
            }
            if existing.is_available():
                available_count += 1
            continue

        # Peek availability without downloading: try lazy-load
        try:
            be = backend_manager.get_backend(name)
            caps = {}
            if be and hasattr(be, "get_capabilities") and be.is_available():
                try:
                    caps = be.get_capabilities()
                except Exception:
                    pass
            backends_status[name] = {
                "name": name,
                "description": meta_info["description"],
                "model_size": meta_info["model_size"],
                "available": be is not None and be.is_available(),
                "capabilities": caps,
            }
            if be and be.is_available():
                available_count += 1
        except Exception as e:
            backends_status[name] = {
                "name": name,
                "description": meta_info["description"],
                "model_size": meta_info["model_size"],
                "available": False,
                "error": str(e),
                "capabilities": {},
            }

    return {
        "backends": backends_status,
        "available_count": available_count,
        "total_count": total_count,
    }


@app.get("/api/models/status")
async def get_model_status():
    """Get detailed status of all OCR backends including availability and download state."""
    if demo_mode:
        return _collect_model_status()
    status = _collect_model_status()
    for name in status["backends"]:
        if name in model_downloads:
            status["backends"][name]["download"] = model_downloads[name]
    return status


@app.post("/api/models/download/{backend_name}")
async def download_model(backend_name: str, background_tasks: BackgroundTasks):
    """Trigger download/load of a model for the specified backend."""
    if demo_mode:
        raise HTTPException(status_code=400, detail="Cannot download in demo mode")
    if not backend_manager:
        raise HTTPException(status_code=503, detail="Backend manager not initialized")

    key = backend_name.strip().lower()
    # Resolve alias
    from ocr_mcp.core.backend_manager import canonical_backend_name

    key = canonical_backend_name(key)
    if key not in backend_manager.backend_registry:
        raise HTTPException(status_code=404, detail=f"Unknown backend: {backend_name}")

    # Already downloaded?
    be = backend_manager.get_backend(key)
    if be and be.is_available():
        return {
            "status": "already_available",
            "backend": key,
            "message": f"{key} is already loaded and available",
        }

    # Already downloading?
    if key in model_downloads and model_downloads[key].get("status") == "downloading":
        return {
            "status": "downloading",
            "backend": key,
            "job_id": model_downloads[key].get("job_id", key),
        }

    job_id = f"model_load_{uuid.uuid4().hex[:8]}"
    model_downloads[key] = {
        "status": "downloading",
        "started_at": time.time(),
        "progress": 0,
        "job_id": job_id,
    }

    background_tasks.add_task(_download_model_background, key, job_id)
    logger.info("Model download started for %s (job %s)", key, job_id)
    return {"status": "downloading", "backend": key, "job_id": job_id}


@app.get("/api/models/download/{backend_name}/progress")
async def get_download_progress(backend_name: str):
    """Poll download/load progress for a specific backend."""
    key = backend_name.strip().lower()
    from ocr_mcp.core.backend_manager import canonical_backend_name

    key = canonical_backend_name(key)
    dl = model_downloads.get(key)
    if not dl:
        # Check if already available
        if backend_manager:
            be = backend_manager.get_backend(key)
            if be and be.is_available():
                return {"status": "available", "backend": key}
        return {"status": "not_started", "backend": key}
    return {"backend": key, **dl}


async def _download_model_background(backend_key: str, job_id: str):
    """Background task: load a backend (downloads models if needed)."""
    import time as _time

    try:
        if not backend_manager:
            model_downloads[backend_key] = {
                "status": "failed",
                "error": "Backend manager not initialized",
                "job_id": job_id,
            }
            return

        model_downloads[backend_key] = {"status": "downloading", "progress": 10, "job_id": job_id}
        _time.sleep(0.2)  # Let the status propagate

        # Force-load the backend
        be = backend_manager.get_backend(backend_key)
        if be is None:
            err_msg = f"Unknown backend: {backend_key}"
            model_downloads[backend_key] = {"status": "failed", "error": err_msg, "job_id": job_id}
            return

        if be.is_available():
            model_downloads[backend_key] = {"status": "available", "progress": 100, "job_id": job_id}
            return

        model_downloads[backend_key] = {"status": "downloading", "progress": 30, "job_id": job_id}

        # Try load_model if available
        if hasattr(be, "load_model"):
            loaded = await be.load_model()
            if loaded is False:
                model_downloads[backend_key] = {
                    "status": "failed",
                    "error": "load_model returned False (check server logs)",
                    "job_id": job_id,
                }
                return
            model_downloads[backend_key] = {"status": "downloading", "progress": 70, "job_id": job_id}

        # Run a quick probe to confirm
        model_downloads[backend_key] = {"status": "verifying", "progress": 90, "job_id": job_id}
        probe = await backend_manager.probe_backend(backend_key)
        if probe.get("success"):
            model_downloads[backend_key] = {"status": "available", "progress": 100, "job_id": job_id, "probe": probe}
        else:
            model_downloads[backend_key] = {
                "status": "failed",
                "error": probe.get("error", "Probe returned no usable text"),
                "progress": 100,
                "job_id": job_id,
                "probe": probe,
            }
    except Exception as e:
        logger.exception("Model download failed for %s", backend_key)
        model_downloads[backend_key] = {"status": "failed", "error": str(e), "progress": 100, "job_id": job_id}


@app.post("/api/restart")
async def restart_backend():
    """Restart the backend server process. Kills current process and spawns a new one."""
    import subprocess
    import sys

    try:
        start_ps1 = project_root / "web_sota" / "start.ps1"
        if start_ps1.exists():
            subprocess.Popen(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(start_ps1),
                    "-Headless",
                ],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        else:
            subprocess.Popen(
                [
                    sys.executable or "python",
                    "-m",
                    "uvicorn",
                    "backend.app:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "10859",
                ],
                cwd=str(project_root),
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )

        logger.info("Backend restart triggered. Shutting down current process...")

        async def _delayed_shutdown():
            await asyncio.sleep(0.5)
            os._exit(0)

        asyncio.create_task(_delayed_shutdown())  # noqa: RUF006

        return {"success": True, "message": "Backend restarting...", "new_port": 10859}

    except Exception as e:
        logger.error("Restart failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


# Handle static files for scans
scans_dir = project_root / "scans"
scans_dir.mkdir(exist_ok=True)
app.mount("/static/scans", StaticFiles(directory=str(scans_dir)), name="scans")

# Mount React app static files (defined after all API routes for proper precedence)
if dist_dir.exists():
    # Mount static assets (JS, CSS, images, etc.)
    app.mount("/assets", StaticFiles(directory=str(dist_dir / "assets")), name="assets")

    @app.get("/")
    async def serve_react_app():
        """Serve the main React app"""
        index_file = dist_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file, media_type="text/html")
        return HTMLResponse("React app not built. Run 'npm run build' in frontend directory.", status_code=503)

    @app.get("/{path:path}")
    async def serve_react_assets(path: str):
        """Serve React app assets and handle SPA routing"""
        # This catch-all route is defined LAST so API routes take precedence
        # Check if the requested file exists in the React app
        requested_file = dist_dir / path
        if requested_file.exists() and requested_file.is_file():
            return FileResponse(requested_file)

        # For SPA routing, serve index.html for all other routes
        index_file = dist_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file, media_type="text/html")

        return HTMLResponse("React app not available.", status_code=503)
else:
    logger.warning(f"Frontend dist directory not found at {dist_dir}. Run 'npm run build' in frontend directory.")


def main():
    """Entry point for running the webapp"""
    host = os.getenv("WEBAPP_HOST", "0.0.0.0")
    port = int(os.getenv("WEBAPP_PORT", "10859"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    uvicorn.run("backend.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
