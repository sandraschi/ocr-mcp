# OCR-MCP — Product Requirements Document

**Version:** 1.1
**Status:** Active
**Last Updated:** 2026-07-21

## 1. Product Overview

OCR-MCP is a unified OCR platform with two surfaces: a **streamlined web application** for interactive document processing and a **FastMCP 3.1 MCP server** for agentic IDEs (Claude, Cursor, Windsurf). Both share the same 14 OCR backends, WIA scanner integration, and processing pipelines.

### 1.1 Target Users

| User | Primary Surface | Use Case |
|------|----------------|----------|
| **End users** | Web app (dashboard) | Drag-and-drop or scan a document, click one button, get text |
| **Developers / agents** | MCP server (stdio) | Integrate OCR into agent workflows, batch processing, CI/CD |
| **Power users** | Both | Settings, Mistral API config, backend probing, activity debugging |

### 1.2 Core Value Proposition

- **One-click OCR:** Scanner or file -> Unlimited-OCR backend -> inline result. No multi-page navigation.
- **14 OCR backends:** From lightweight (Tesseract, EasyOCR) to SOTA VLMs (Unlimited-OCR, PaddleOCR-VL, Nemotron VL).
- **Same backends, two surfaces:** What works in the webapp also works in the MCP server.
- **Local-first:** All models run on your hardware (GPU optional). No cloud dependency unless you choose Mistral OCR.

## 2. Functional Requirements

### 2.1 Web Application (Dashboard-First)

| Feature | Priority | Description |
|---------|----------|-------------|
| Quick Scan & OCR | P0 | One button: pick scanner or drop file, select backend, click. Result appears inline. |
| File drop zone | P0 | Drag-and-drop or click to browse (images + PDF). |
| Scanner integration | P0 | WIA 2.0 flatbed scanner control (Windows). |
| Inline OCR result | P0 | Editable textarea with Copy / .txt / .md export. |
| Live KPI cards | P1 | Server health, tool count, backend availability from `/api/health`. |
| Backend selector | P1 | Dropdown with auto-detected available backends. |
| Activity log | P1 | Job status and history for debugging. |
| Settings | P1 | Default backend, Mistral API key, backend/scanner lists. |
| Help | P2 | In-app documentation. |
| Editor (standalone) | P2 | Full text view with JSON/CSV/XML export. |

### 2.2 MCP Server

| Feature | Priority | Description |
|---------|----------|-------------|
| Portmanteau tools | P0 | `process_document`, `manage_image`, `operate_scanner`, `manage_workflow`, `manage_corpus` |
| Dual transport | P0 | stdio (Claude Desktop, Cursor) + HTTP (`MCP_TRANSPORT=http`). |
| Auto backend selection | P0 | Intelligent fallback chain (14 backends). |
| Resources | P1 | `resource://ocr/logs`, `resource://ocr/capabilities`. |
| Sampling | P2 | `ctx.sample()` for agentic document workflows (Ollama or client LLM). |

### 2.4 Book Pipeline (New)

| Feature | Priority | Description |
|---------|----------|-------------|
| Chapter detection | P1 | Rules-based heading detection across OCR page text (supports EN/FR/DE/ES) |
| EPUB assembly | P1 | Build valid EPUB with auto-generated TOC from chapters |
| Metadata extraction | P2 | Auto-detect title/author from first 3 pages |
| Full pipeline | P1 | One-shot: OCR pages -> detect chapters -> assemble EPUB |
| Calibre integration | P2 | Send finished EPUB to calibre-mcp for library ingest |

### 2.5 Auto-Scan Watcher (New)

| Feature | Priority | Description |
|---------|----------|-------------|
| Preview-poll mode | P1 | Detect document placement on flatbed via low-res preview + image hash diff |
| Button mode | P2 | Detect WIA scan button events |
| Auto-OCR | P1 | Automatically scan + OCR when document detected |
| Dashboard toggle | P1 | Start/stop watcher from Dashboard, see live scan count |
| Settings config | P2 | Configure mode, interval, backend from Settings page |

### 2.3 OCR Backends

14 backends covering all quality/performance tiers:

| Tier | Backends | Use Case |
|------|----------|----------|
| **SOTA VLM** | Unlimited-OCR, PaddleOCR-VL-1.5, MinerU2.5-Pro, Nemotron VL 8B | High-accuracy document parsing |
| **Strong VLM** | DeepSeek-OCR-2, olmOCR-2, Mistral OCR (API) | Structured text, academic PDFs |
| **Lean VLM** | GOT-OCR 2.0, Qwen2.5-VL, DOTS.OCR | Fast inference, moderate VRAM |
| **Legacy** | PP-OCRv5, EasyOCR | High throughput, CJK, handwriting |
| **Backstop** | Tesseract | CPU-only, always available |

## 3. Technical Requirements

### 3.1 Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite 7, Tailwind CSS, Zustand, Lucide icons, Radix UI |
| Backend API | FastAPI (Uvicorn) |
| MCP Framework | FastMCP 3.4+ |
| Python | 3.12+ |
| Package Manager | uv |
| ML Runtime | PyTorch, Transformers, Hugging Face Hub |
| Task Runner | just |
| Linter | Ruff (Python), Biome (TypeScript) |
| Scanner | WIA 2.0 (Windows), comtypes |
| Models | Hugging Face (trust_remote_code for custom VLMs) |

### 3.2 Ports

| Service | Port |
|---------|------|
| Vite dev server (frontend) | 10858 |
| FastAPI backend | 10859 |
| MCP HTTP transport | 10859 (`/mcp`) |

### 3.3 Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Any x64 | Any x64 |
| RAM | 8 GB | 16 GB |
| GPU | None (Tesseract, EasyOCR) | NVIDIA RTX 3060+ (12GB+ VRAM) |
| Disk | 500 MB (code) + model cache | 20 GB+ for full model cache |
| OS | Windows 10+ (WIA scanner) | Windows 11 |

## 4. User Stories

### 4.1 Quick scan

> As a user, I want to place a document on my scanner, press one button, and get the OCR text immediately without navigating between pages.

**Acceptance:** Dashboard has scanner selector, backend dropdown, "Quick Scan & OCR" button. Click -> scan -> OCR with Unlimited-OCR -> text appears in inline textarea. Copy or download.

### 4.2 File upload

> As a user, I want to drag-and-drop a photo of a document and get its text.

**Acceptance:** Drop zone accepts image files and PDFs. Click "OCR File" triggers upload + processing. Result appears inline.

### 4.3 Backend switching

> As a power user, I want to try a different OCR engine on the same document.

**Acceptance:** Backend dropdown on dashboard. Changing it and clicking Quick Scan re-processes with the new backend.

## 5. Roadmap

| Phase | Status | Features |
|-------|--------|----------|
| Core backends | Done | 14 backends, lazy loading, auto-selection |
| Web app v1 | Done | Dashboard-first redesign, quick scan, inline results |
| MCP server | Done | Portmanteau tools, dual transport, resources, prompts |
| WIA scanner | Done | Flatbed scanning on Windows |
| Batch/pipelines | Done | Quality optimizer, pipeline execution |
| Skills directory | Done | SKILL.md + parameterized skill:// resources |
| Prefab UI cards | Done | Health card, backends card |
| Book pipeline | Done | Chapter detection, EPUB assembly, webapp page |
| Auto-Scan watcher | Done | Preview-poll + button event detection |
| Agentic workflows | Done | ctx.sample() + sample_step() fallback |
| Production packaging | In Progress | Tauri NSIS installer, PyInstaller sidecar |
| CUA-NSIS smoke tests | In Progress | Install -> launch -> verify -> uninstall |
| Folder watcher (CZUR) | Future | Watch directory for new scan images |
| TWAIN scanner | Future | Support non-WIA scanners |
| Cloud sync | Future | Cross-device settings, corpus sync |

## 6. Success Metrics

| Metric | Target |
|--------|--------|
| Time from scan to text | < 30 seconds (with VLM backend) |
| Backend availability | 14 backends registered, at least 1 always available |
| Webapp page load | < 2 seconds |
| Quick Scan button clicks to result | 1 click, 0 page navigations |
| TypeScript compilation | Zero errors |
| Python lint | Zero errors (ruff) |
