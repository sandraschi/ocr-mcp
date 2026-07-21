# OCR-MCP — Project Status

**Last Updated:** 2026-07-21
**Version:** 0.2.0-beta
**Status:** Beta

## Current Build

| Gate | Status |
|------|--------|
| Python lint (ruff) | Pass |
| TypeScript (tsc --noEmit) | Pass |
| Vite build | Pass |
| Tests | Pass |
| NSIS build | Pass |
| CUA smoke test | Pass |
| Pre-commit hooks | Configured (ruff, file hygiene) |
| CI workflow | Windows CI (ruff, pytest, tsc, vite build) |

## What's Working

### Webapp
- Dashboard: file drop zone, scanner selector, backend selector, Quick Scan & OCR button, **Auto-Scan toggle**
- Inline OCR result with Copy / .txt / .md export
- Live KPI cards from `/api/health` (server, tool count, backend availability)
- Backend health indicator in topbar (green ping / red / gray)
- Sidebar: 6 items (Dashboard, **Book Pipeline**, Editor, Activity, Settings, Help)
- **Book Pipeline page**: select page images, OCR batch, detect chapters, assemble EPUB
- Editor page: standalone text view with JSON/CSV/XML export
- Activity page: job status polling and history
- Settings: default backend, Mistral API key + test, backend and scanner lists, **Auto-Scan settings**

### MCP Server
- Dual transport: stdio + HTTP
- 8 portmanteau tools: `process_document`, `manage_image`, `operate_scanner`, `manage_workflow`, `manage_corpus`, `get_help`, `get_status`, **`ingest_book`**
- **2 Prefab UI tools**: `show_health_card`, `show_backends_card`
- Agentic workflow tool (`execute_agentic_workflow`) with `ctx.sample()` + `sample_step()` fallback
- 5 parameterized prompts (process-instructions, quality-assessment, scanner-workflow, batch-processing, agentic-workflow)
- 3 resources (`resource://ocr/logs`, `resource://ocr/capabilities`, `resource://ocr/skills`)
- **Skills directory** with `skill://{name}` parameterized resource
- 14 OCR backends with lazy loading + auto-selection

### OCR Backends
- 14 backends registered: Unlimited-OCR, PaddleOCR-VL-1.5, MinerU2.5-Pro, Nemotron VL 8B, DeepSeek-OCR-2, olmOCR-2, Mistral OCR, Qwen2.5-VL, GOT-OCR 2.0, DOTS.OCR, PP-OCRv5, EasyOCR, Tesseract
- Intelligent auto-selection with fallback chain
- Per-backend model caching and GPU memory management

### Backend API
- `GET /api/health` — server status, version, uptime, tool count
- `GET /api/backends` — registered backends with availability
- `GET /api/scanners` — WIA scanner discovery
- `POST /api/scan` — trigger WIA scan
- `POST /api/ocr_scanned` — OCR a scanned image
- `POST /api/upload` — upload and OCR a file
- `GET /api/job/{id}` — poll job status
- `GET|POST /api/settings/mistral` — Mistral API key management
- `POST /api/settings/mistral/test` — validate Mistral key
- `GET /api/scanner/watch/status` — auto-scan watcher status
- `POST /api/scanner/watch` — start auto-scan watcher
- `POST /api/scanner/watch/stop` — stop auto-scan watcher
- `POST /api/ocr/detect-chapters` — detect chapter headings from OCR text
- `POST /api/ocr/detect-metadata` — extract title/author from first pages
- `POST /api/ocr/assemble-epub` — build EPUB from chapter text
- `POST /api/ocr/book-pipeline` — full OCR-to-EPUB pipeline
- OpenAPI docs at `/docs`

### Auto-Scan Watcher
- Background service polls flatbed for document placement via preview-scan image diff
- Two modes: `preview` (universal, image-hash comparison) and `button` (WIA button events)
- Toggle from Dashboard or Settings
- When detected: full 300 DPI scan + OCR with configurable backend

### Book Pipeline
- `ingest_book` MCP tool with 4 operations: detect_chapters, detect_metadata, assemble_epub, full_pipeline
- Rules-based chapter heading detection (supports English, French, German, Spanish, Roman numerals)
- EPUB assembly via ebooklib with auto-generated TOC and navigation
- Metadata extraction from title page (title, author)
- Webapp page with multi-file upload, progress bar, chapter preview

## In Progress

- Tauri 2.0 NSIS installer (PyInstaller + embedded backend)
- CUA-NSIS smoke test pipeline
- Production packaging (MCPB bundle)

## Known Issues

- PaddleOCR-VL-1.5 requires flash-attn for reasonable VRAM (~3.3GB vs 40GB without)
- Mistral OCR requires a cloud API key (stored in backend process only)
- WIA scanner only works on Windows
- No TWAIN scanner support yet
- No cloud sync for settings across devices
- Scanner watcher preview mode requires a WIA-compatible scanner

## Recent Milestones

| Date | Milestone |
|------|-----------|
| 2026-07-21 | **v0.2.0-beta released** — FastMCP 3.4+ features, skills, Prefab UI, auto-scan, book pipeline |
| 2026-07-21 | Book scanning pipeline: chapter detection, EPUB assembly, webapp Book Pipeline page |
| 2026-07-21 | Auto-Scan watcher with preview-poll and WIA button detection |
| 2026-07-21 | Unlimited-OCR backend added (Baidu, MIT, 3B params) |
| 2026-07-21 | Webapp streamlined: dashboard-first, removed legacy frontend, 5-page sidebar |
| 2026-06-14 | Tauri 2.0 NSIS wrapper + CUA smoke test |
| 2026-05-14 | Nemotron VL 8B backend |
| 2026-05-12 | MinerU2.5-Pro backend, backend management UI |
