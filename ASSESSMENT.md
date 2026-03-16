# OCR-MCP Repository Assessment

**Date**: 2026-02-08  
**Scope**: Technical assessment of OCR-MCP - bugs, strengths, weaknesses, improvement suggestions

---

## Executive Summary

OCR-MCP is a comprehensive FastMCP document processing server with 8+ OCR backends, scanner integration, and a React webapp. Architecture is solid: lazy-loaded backends, structured error handling, portmanteau tools, SEP-1577 agentic workflow. However, several bugs, platform assumptions, and design gaps prevent reliable production use. Webapp currently runs in demo-only mode; real OCR is never invoked for uploads.

**Overall Score**: 6.5/10 (alpha-ready, needs fixes before production)

---

## Strengths

### Architecture
- **Lazy-loaded backends**: BackendManager loads OCR engines on first use; avoids slow startup and memory bloat.
- **Backend registry pattern**: Clean registry for 8 backends with module paths; easy to add new engines.
- **Portmanteau tools**: `document_processing`, `image_management`, `scanner_operations`, `workflow_management` consolidate operations; reduces tool sprawl.
- **Structured error handling**: `ErrorHandler` with `OCRError`, error codes, recovery options, severity levels.
- **Sampling integration**: FastMCP 2.14.3 `OCRSamplingHandler` for AI-orchestrated document workflows (SEP-1577).
- **Modular backends**: Tesseract, EasyOCR, DeepSeek, Florence-2, DOTS, PP-OCRv5, Qwen-Layered, Mistral OCR; clear base class `OCRBackend`.

### Tooling & Standards
- **Pre-commit**: Ruff, MyPy, Bandit, detect-secrets, Markdownlint.
- **CI/CD**: Multi-OS (Ubuntu, Windows), multi-Python (3.9–3.11), unit/integration/e2e/benchmark jobs.
- **Packaging**: Poetry, pyproject.toml, MCPB packaging; optional extras for ml, webapp, scanner, dev.
- **Test structure**: Unit, integration, e2e, benchmarks, fuzzing, security, performance; conftest and mocks.

### Documentation
- **AI_MODELS.md**: Model matrix, capabilities, benchmarks.
- **OCR-MCP_MASTER_PLAN.md**: Roadmap and phases.
- **README**: Feature overview, quick start, portmanteau tool reference.

### Backend Quality
- **WIA scanner**: Windows-specific with fallback; `ScanSettings`, `ScannerInfo` dataclasses.
- **Tesseract backend**: Clean implementation, capability reporting, language config.

---

## Weaknesses

### Webapp Demo-Only Mode
- **Critical**: `backend/app.py` line 166: "Always use demo processing for now to ensure it works" – uploads and batch jobs always call `process_file_demo` / `process_batch_demo`, never real OCR.
- `process_file_background` and `process_batch_background` exist but are never used.
- Webapp behaves like a mock; users do not get actual OCR.

### Platform Assumptions
- **config.py** lines 60–61, 97–98: `model_dir` and `model_cache_dir` default to `Path("/app/models")` – Docker-oriented; on Windows resolves to `C:\app\models` and can fail on mkdir or when `/app` doesn’t exist.
- **Scanner**: WIA only; no TWAIN or SANE support; Linux/macOS users have no scanner support.
- **CI webapp test**: Uses `pkill -f "run_webapp.py"` – Linux-specific; will fail on Windows.

### Temp File Leaks
- **backend/app.py**: `process_file_demo` and `process_batch_demo` receive `filename` (and `filenames`), not file paths. Temp files are stored in `processing_jobs[job_id]["file_path"]` but demo tasks never delete them; temp files accumulate.

### Backend Manager Misuse
- **backend/app.py** lines 502–504, 604: `backend_manager.get_backend("auto")` – `"auto"` is not in `backend_registry`; `get_backend("auto")` returns `None`, causing `AttributeError` when calling `process_document` on `None`.
- **optimize_background** iterates over `["auto", "florence-2", ...]`; `get_backend("auto")` fails.

### Entry Point Mismatch
- **pyproject.toml** line 105: `ocr-mcp-webapp = "webapp.backend.app:main"` – but the module is `backend.app` at repo root; no `webapp.backend.app` exists.
- `scripts/run_webapp.py` correctly uses `from backend.app import main`; CLI entry point would fail.

### Form Parameter Bug
- **backend/app.py** line 331: `target_format: str = FORM_DEPENDENCY` – `FORM_DEPENDENCY` is `Form()`, used as default for a string parameter. Should be `Form("json")` or similar; current usage is incorrect.

### Duplicate / Redundant Code
- **backend_manager.py** line 72: Duplicate `logger = logging.getLogger(__name__)` (already at line 31).
- **config.py** lines 5–7 and 8–10: Two docstring blocks at module top.
- **_processor.py** line 61: Redundant `import time` inside function (time already imported at top).

### Unicode Emoji in Logs
- **backend_manager.py** line 212: `logger.info(f"✅ {backend_name} backend loaded successfully")` – Unicode emoji in logger; violates project rules; can cause encoding issues on Windows.

### Error Handler Gap
- **error_handler.py**: `ErrorHandler.create_error("INTERNAL_ERROR", ...)` used in `_processor.py` line 47, but `"INTERNAL_ERROR"` is not in `ERROR_CODES`; falls back to generic handling (works but inconsistent).

### Pipeline Placeholders
- **backend/app.py** lines 609–620: Pipeline steps `deskew_image`, `enhance_image`, `assess_ocr_quality`, `convert_image_format` return `{"status": "skipped", "reason": "Not implemented"}` – pipelines run but produce no real preprocessing or conversion.

---

## Bugs Summary

| Severity | Location | Issue |
|----------|----------|-------|
| Critical | backend/app.py:166 | Demo-only processing; real OCR never used for uploads |
| Critical | backend/app.py:502,604 | `get_backend("auto")` returns None; AttributeError |
| Critical | backend/app.py | Temp files never deleted in demo tasks (resource leak) |
| High | config.py:60-61,97-98 | `/app/models` default breaks on non-Docker Windows |
| High | pyproject.toml:105 | `webapp.backend.app` entry point does not exist |
| High | backend/app.py:331 | `target_format: str = FORM_DEPENDENCY` incorrect |
| Medium | backend_manager.py:212 | Unicode emoji in logger |
| Medium | backend_manager.py:72 | Duplicate logger definition |
| Medium | config.py | Duplicate docstrings |
| Medium | _processor.py:61 | Redundant import |
| Low | error_handler.py | INTERNAL_ERROR not in ERROR_CODES |
| Low | CI webapp-test | `pkill` is Linux-only |

---

## Improvement Suggestions

### P0 – Critical Fixes
1. **Enable real OCR in webapp**: Remove demo-only path; call `process_file_background` / `process_batch_background` when `demo_mode=False`, or introduce a flag to switch modes.
2. **Fix `get_backend("auto")`**: Use `backend_manager.select_backend("auto", image_path)` instead of `get_backend("auto")` in `optimize_background` and `execute_pipeline_background`.
3. **Clean up temp files**: Pass `file_path` to demo tasks, or have a post-job cleanup that deletes temp files from `processing_jobs[job_id]`.

### P1 – High Priority
4. **Platform-aware config**: Default `model_dir` / `model_cache_dir` to `cache_dir / "models"` or `Path.home() / ".cache" / "ocr-mcp" / "models"`; use `/app/models` only when `OCR_MODEL_DIR` is set (e.g. in Docker).
5. **Fix pyproject entry point**: Change `ocr-mcp-webapp = "webapp.backend.app:main"` to `ocr-mcp-webapp = "backend.app:main"`, or move `backend/` under `webapp/` and adjust imports.
6. **Fix convert_format parameter**: Use `target_format: str = Form("json")` (or appropriate default) instead of `FORM_DEPENDENCY`.

### P2 – Medium Priority
7. **Remove emoji from logs**: Replace `"✅"` with `"[OK]"` or plain text in backend_manager.py.
8. **Remove duplicate logger/docstrings**: Clean up backend_manager.py and config.py.
9. **Add TWAIN/SANE stubs**: Document scanner support as Windows-only; add placeholder modules for future Linux/macOS support.
10. **Cross-platform CI**: Use a cross-platform stop command instead of `pkill` (e.g. store PID and terminate by PID, or use a helper script).

### P3 – Enhancements
11. **Pipeline implementation**: Implement `deskew_image`, `enhance_image`, `convert_image_format` via `image_management` tool or equivalent.
12. **Add INTERNAL_ERROR to ERROR_CODES**: For consistency with structured error handling.
13. **Job expiration**: Add TTL or periodic cleanup for `processing_jobs` to avoid unbounded growth.
14. **WebSocket progress**: Replace polling with WebSocket for job status where feasible.
15. **Scanner API validation**: Validate `device_id` against discovered scanners before scan.

---

## Technical Debt

- **backend/app.py** (~760 lines): Consider splitting into routers (upload, job, scanner, pipeline, export).
- **Backend interface inconsistency**: Some backends use `process_document(source_path=..., ocr_mode=...)`, others `process_image(image_path, mode)`. BackendManager handles both; consider standardizing on one.
- **requirements.txt vs pyproject.toml**: Both exist; requirements.txt has different version ranges (e.g. `fastmcp>=2.13.0,<2.14.0` vs pyproject `>=2.14.3,<3.0.0`). Align or remove redundant requirements.txt.
- **Root-level test files**: `test_*.py` at repo root (e.g. `test_backend_manager.py`, `test_gpu.py`) – move under `tests/` or document as ad-hoc scripts.

---

## Test & CI Notes

- Unit tests in `tests/unit/`; integration in `tests/integration/`; e2e in `tests/e2e/`.
- CI runs benchmarks with `continue-on-error: true`; failures don’t block pipeline.
- Webapp tests use `continue-on-error: true`; failures are not surfaced as blockers.
- Coverage threshold 85% (pyproject) vs 90% (release job); align if desired.

---

## Recommendations Summary

| Priority | Action |
|----------|--------|
| P0 | Switch webapp from demo-only to real OCR processing |
| P0 | Replace `get_backend("auto")` with `select_backend("auto", path)` |
| P0 | Add temp file cleanup in demo and real processing paths |
| P1 | Make config defaults platform-aware |
| P1 | Fix pyproject webapp entry point |
| P1 | Fix convert_format Form default |
| P2 | Remove emoji and redundant code |
| P2 | Cross-platform CI for webapp stop |
| P3 | Implement pipeline preprocessing steps |
| P3 | Add job expiration / cleanup |

---

*Assessment generated 2026-02-08*

---

## Fixes Applied (2026-02-08)

**Phase 1 (Previous session):**
- Real OCR enabled in webapp when backends available
- `get_backend("auto")` replaced with `process_with_backend(backend_name="auto", ...)`
- Temp file cleanup in demo tasks
- Platform-aware config (model_dir under ~/.cache)
- Pyproject entry point fixed (ocr_mcp.webapp_runner)
- convert_format Form default fixed
- Emoji/duplicate logger/docstrings removed
- INTERNAL_ERROR added to ErrorHandler

**Phase 2 (This session):**
- Temp file cleanup on all error paths (process_file_background, process_batch_background, demos, optimize_background, convert_background, execute_pipeline_background)
- Job pruning: _prune_old_jobs() when over MAX_PROCESSING_JOBS (500)
- Unique job IDs with uuid
- Shutdown cleanup: orphan temp files removed on shutdown

**Phase 3:**
- valid_backends: added mistral-ocr to error_handler
- _image.py: fixed execution_time (was time.time() - time.time() = 0)
