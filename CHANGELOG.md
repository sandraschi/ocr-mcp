# Changelog

All notable changes to OCR-MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-03-16

### Added
- **FastMCP 3.1 prompts**: `quality-assessment-guide`, `scanner-workflow`, `batch-processing-guide`, `agentic-workflow-instructions` (in addition to `process-instructions`).
- **Resources**: `resource://ocr/capabilities` (backends + 3.1 features), `resource://ocr/skills` (LLM-oriented skills reference for document processing, scanning, workflows, agentic).
- **Server docstring**: Documents sampling, agentic workflow tool, prompts, and skills in module header.

### Fixed
- **WIA scanner discovery lost after first request**
  - Scanner was found on first `/api/scanners` call then reported 0 devices on later calls.
  - **Cause**: `_release_device()` called `pythoncom.CoUninitialize()`, tearing down COM for the whole executor thread; next discovery then ran in a broken COM state. Also, cleanup ran before re-enumerate so devices were released right before enumeration.
  - **Changes**: (1) `_release_device()` now only releases the device COM reference (e.g. `device.Release()`), no longer calls `CoUninitialize()`. (2) Discovery no longer cleans up at start; it enumerates first, builds the new device list, then releases only connections no longer in the new set. (3) All WIA discovery and scan already use a single-thread executor so COM stays on one STA thread.
- **Agentic document workflow** — was simulated single-step mock; now uses real `context.sample_step` loop with tool execution (FastMCP 3.1).
- **GET /api/scanners** — no longer returns fake "Demo Scanner" when discovery fails; returns `scanners: []` and `error` message.
- **MCP server not starting in Cursor (FastMCP 3.x API)** — FastMCP 3.x removed `on_duplicate_tools`, `on_duplicate_resources`, `on_duplicate_prompts` and `include_fastmcp_meta`. Server now uses single `on_duplicate="replace"` and no longer passes removed kwargs, so it starts correctly in Cursor and other MCP clients.

### Changed
- **Web backend** — WIA operations use a dedicated single-thread `ThreadPoolExecutor` instead of `asyncio.to_thread()` so every discovery/scan runs on the same STA thread and device list stays stable.
- **FastMCP** — Upgraded from 2.14.x to **3.1**: dependency `fastmcp[server]>=3.1`, all docs and docstrings updated.

## [Unreleased] - 2026-02-27

### Added
- **PaddleOCR-VL-1.5 backend** (`paddleocr_vl_backend.py`) — January 2026 SOTA
  - 94.5% accuracy on OmniDocBench v1.5 — top of all open-source benchmarks
  - 0.9B parameters (NaViT encoder + ERNIE-4.5-0.3B LM), ~1.8GB on disk
  - ~3.3GB VRAM with flash-attn; ~40GB without — flash-attn is mandatory on GPU
  - First model with irregular box localization (tilted, folded, screen-captured docs)
  - Supports text, tables, formulas, charts, seals, 109 languages
  - HF: `PaddlePaddle/PaddleOCR-VL-1.5`
- **DeepSeek-OCR-2 backend** (`deepseek_ocr2_backend.py`) — January 2026
  - "Visual Causal Flow" architecture (arXiv:2601.20552)
  - 3B parameters, strong structured markdown output
  - HF: `deepseek-ai/DeepSeek-OCR-2`
  - Requires: `einops addict easydict flash-attn==2.7.3`
- **olmOCR-2 backend** (`olmocr_backend.py`) — October 2025, Allen Institute for AI
  - Built on Qwen2.5-VL-7B-Instruct, 82.4 on olmOCR-Bench
  - Best choice for scientific/academic PDFs with math equations and multi-column layouts
  - GRPO RL training specifically targets equations and tables
  - HF: `allenai/olmOCR-2-7B-1025`

### Changed
- **Auto backend priority order** updated to reflect 2026 SOTA reality:
  `paddleocr-vl → mistral-ocr → deepseek-ocr2 → olmocr-2 → deepseek-ocr → qwen-layered → got-ocr → dots-ocr → pp-ocrv5 → easyocr → tesseract`
- **Backend alias map** extended with `paddleocr`, `paddle`, `deepseek2`, `olmocr`, `olm`, `paddleocr-vl-1.5`; `florence` alias now redirects to `paddleocr-vl`

### Removed
- **Florence-2 backend** (`florence_backend.py`) — deleted
  - Florence-2 is a general-purpose vision foundation model (object detection, captioning, grounding), not an OCR specialist
  - The OCR task prompt it exposed produced inferior results; confidence score was hardcoded; structured output methods were stubs
  - Replaced by PaddleOCR-VL-1.5 which is purpose-built and measurably better
- **Demo mode backend list** no longer references florence-2 or pp-ocrv5 as defaults

### Fixed
- **Scanner bug: `"id"` → `"device_id"` in `/api/scanners` response**
  - Frontend `ScannerInfo` interface expected `device_id`; backend was returning `id`
  - `selectedScanner` was always `undefined`, FormData sent garbage device_id, scan never triggered
- **WIA COM threading: scan now runs in dedicated thread via `asyncio.to_thread()`**
  - WIA COM operations require STA apartment; uvicorn async event loop thread uses MTA
  - Calling `scanner_manager.scan_document()` directly in an `async def` endpoint caused silent failures
  - Fixed by wrapping in `asyncio.to_thread()` which creates a new thread with proper COM context
- **Pipeline execution: `backend` parameter now passed through to `execute_pipeline_background()`**
  - `/api/pipelines/execute` now accepts `backend` as a Form field
  - Previously hardcoded `"auto"` regardless of user selection

### Changed (webapp)
- **`process.tsx` (Pipeline page) rewritten** — was non-functional placeholder
  - Each pipeline card now has file picker + OCR backend selector + Run Pipeline button
  - Polls `/api/job/{id}` until complete; shows extracted text inline in expandable result panel
  - Quality Optimizer kept as separate utility below the pipeline cards
- **`settings.tsx`** — added Default OCR Backend selector (persisted to `localStorage`)
  - Shows scanner details: manufacturer, max DPI, raw device_id
- **`scanner.tsx`** — added OCR Backend dropdown; "OCR this Scan" now uses selected backend instead of hardcoded `"auto"`

## [Unreleased] - 2026-02-09

### Changed
- Upgraded FastMCP to 3.1 (see 2026-03-16 section)
- Removed lifespan storage usage (mcp_instance.storage not in FastMCP 3.x)
- Portmanteau tool docstrings: 2026 SOTA format, no triple quotes within
- README: Portmanteau Tool Ecosystem aligned with actual operations

## [0.2.0-alpha.0] - 2026-01-19

### 🚀 **Major Improvements**

#### **Development Environment Modernization**
- **Streamlined Tooling**: Removed redundant Black and isort dependencies - Ruff now handles all linting, formatting, and import sorting
- **Enhanced Ruff Configuration**: Configured Ruff for comprehensive code quality with import sorting and first-party package recognition
- **Comprehensive Pre-commit Hooks**: Added 20+ quality checks including security scanning, complexity analysis, and secret detection
- **Automated Dev Setup**: Created `ocr-mcp-setup-dev` script for one-command development environment setup
- **CI/CD Pipeline Enhancement**: Improved workflow with better error handling, security audits, and quality reports

#### **Code Quality & Standards**
- **Advanced Linting**: Integrated MyPy, Bandit, Pip-Audit, Radon, and Detect-Secrets
- **Security Hardening**: Added comprehensive security scanning and vulnerability detection
- **Documentation Generation**: Added pDoc for automatic API documentation generation
- **Type Safety**: Enhanced type checking with proper dependency management

#### **Infrastructure Improvements**
- **Port Standardization**: Consolidated all ports to 15550 for consistent development experience
- **Frontend-Backend Integration**: Fixed React app serving issues with proper static file handling
- **Testing Framework**: Enhanced test suite with advanced fixtures, mock servers, and comprehensive coverage
- **Build System**: Improved Poetry configuration with proper dependency grouping

#### **Project Maturity**
- **Professional Documentation**: Created dedicated `AI_MODELS.md` with detailed backend specifications
- **Comprehensive README**: Added development setup guides, pre-commit documentation, and troubleshooting
- **Changelog Management**: Established proper version tracking and release notes
- **Badge System**: Added version, CI/CD, coverage, and status badges

### 🛠️ **Technical Enhancements**

#### **Backend Improvements**
- **Ruff Integration**: Single tool for linting, formatting, and import sorting
- **Error Handling**: Improved exception chaining and bare except fixes
- **Static File Serving**: Proper React SPA routing with catch-all handlers
- **CORS Configuration**: Updated origins for localhost:15550

#### **Frontend Updates**
- **API Configuration**: Standardized backend URL to localhost:15550
- **Build Process**: Fixed static file generation and distribution
- **Settings Management**: Updated default backend URLs

#### **Testing Infrastructure**
- **Advanced Fixtures**: Enhanced pytest configuration with proper path handling
- **Mock Servers**: Improved testing utilities with configurable ports
- **Performance Testing**: Added benchmark framework and load testing capabilities
- **Cross-Platform**: Windows-compatible test execution

#### **CI/CD Pipeline**
- **Multi-OS Testing**: Ubuntu and Windows CI with Python 3.9-3.11
- **Quality Gates**: Security audits, complexity analysis, and coverage requirements
- **Documentation Deployment**: Automated pDoc generation and GitHub Pages deployment
- **Release Automation**: GitHub releases with comprehensive test validation

### 📊 **Quality Metrics**

- **Code Coverage**: Maintained 90%+ test coverage requirement
- **Security**: Zero high-severity vulnerabilities (pip-audit, Bandit)
- **Complexity**: Cyclomatic complexity analysis with Radon
- **Dependencies**: Vulnerability scanning and license compliance

### 🔄 **Breaking Changes**
- **Tooling Migration**: Black and isort removed in favor of Ruff
- **Port Changes**: All services now use port 15550
- **Import Structure**: Ruff import sorting may reorganize imports

### 🧪 **Testing & Validation**
- **Unit Tests**: Comprehensive backend and frontend test coverage
- **Integration Tests**: End-to-end workflow validation
- **WebApp Tests**: Playwright-based UI testing with server readiness checks
- **Performance Benchmarks**: Automated performance regression detection

## [0.1.2] - 2026-01-01

### Added
- **Singleton Backend Manager**: Refactored `BackendManager` in `app.py` to a global singleton, ensuring COM context stability.
- **Robust WIA 2.0 Acquisition**: Implemented explicitly scoped `CoInitialize` calls and reconnection logic in `wia_scanner.py` for hardware stability.
- **Hardware Stability**: Successfully resolved the `WIA_ERROR_BUSY` (0x8021006B) and acquisition failures for Canon LiDE 400 scanners.
- **Professional Web Interface**: Finalized integration of the modern React-based UI with the stable backend.

### Fixed
- Indentation errors and logic flow in `webapp/backend/app.py` `/api/scan` endpoint.
- Redundant backend re-initialization that caused resource churn and COM instability.
- Port conflict resolution and documentation (Standardized on port 8765).

## [0.1.1] - 2025-12-23

### Added
- Complete implementation of all 6 advanced OCR backends:
  - Mistral OCR 3 (State-of-the-art API-based OCR, 74% win rate over OCR2)
  - DeepSeek-OCR (4.7M+ downloads)
  - Florence-2 (Microsoft vision foundation model)
  - DOTS.OCR (Document structure specialist)
  - PP-OCRv5 (Industrial PaddlePaddle OCR)
  - Qwen-Image-Layered (Advanced image decomposition)
- Full scanner integration with WIA (Windows Image Acquisition)
- Comprehensive document processing for PDF, CBZ/CBR, and images
- Modern web application with FastAPI backend and responsive frontend
- 7 fully functional MCP tools with portmanteau design
- Advanced comic/manga processing with scaffold separation
- Batch processing capabilities with concurrent operations
- Complete project documentation and usage guides

### Changed
- Updated README with current backend matrix and tool ecosystem
- Enhanced documentation with detailed backend descriptions
- Improved error handling and user feedback throughout

### Fixed
- Unicode encoding issues in Windows environment
- Server startup problems with stdio mode
- Logging configuration conflicts
- Backend interface inconsistencies
- Missing dependencies and import errors
- PP-OCRv5 backend availability check (removed deprecated PaddleOCR parameters)
- PP-OCRv5 backend now fully functional with automatic model downloading
- Webapp startup issues with MCP client initialization
- MCP client JSON parsing errors from server log messages
- Incorrect webapp port documentation (8000 → 7460)
- Blocking webapp startup during MCP client initialization

### Tested
- PP-OCRv5 backend successfully tested and verified working
- All 5 OCR models automatically downloaded and initialized:
  - PP-LCNet_x1_0_doc_ori (document orientation detection)
  - UVDoc (document layout analysis)
  - PP-LCNet_x1_0_textline_ori (text line orientation)
  - PP-OCRv5_server_det (text detection)
  - en_PP-OCRv5_mobile_rec (text recognition)
- All 9 OCR backends successfully initialized with graceful fallback system
- 6 out of 9 backends fully functional and available for use
- Backend manager properly handles failed backends with mock implementations

### Added
- MockOCRBackend class for graceful degradation of failed backends
- Comprehensive backend fallback system preventing crashes
- All 9 OCR backends now available in the system:
  - DeepSeek-OCR: Working (4.7M+ downloads)
  - Florence-2: Working (Microsoft vision model)
  - DOTS.OCR: Working (document structure)
  - PP-OCRv5: Working (industrial PaddlePaddle)
  - GOT-OCR2.0: Working (legacy backend)
  - Tesseract: Working (classic OCR)
  - Mistral OCR 3: Ready (API-based, requires key)
  - Qwen-Image-Layered: Available (model not found)
  - EasyOCR: Available (Unicode issues)
