# OCR-MCP — Project Status

**Last Updated:** 2026-07-21
**Version:** 0.1.0
**Status:** Alpha

## Current Build

| Gate | Status |
|------|--------|
| Python lint (ruff) | Pass |
| TypeScript (tsc --noEmit) | Pass |
| Vite build | Pass |
| Tests | Pass |
| NSIS build | Pass |
| CUA smoke test | Pass |

## What's Working

### Webapp
- Dashboard: file drop zone, scanner selector, backend selector, Quick Scan & OCR button
- Inline OCR result with Copy / .txt / .md export
- Live KPI cards from `/api/health` (server, tool count, backend availability)
- Backend health indicator in topbar (green ping / red / gray)
- Sidebar: 5 items (Dashboard, Editor, Activity, Settings, Help), collapse toggle at top
- Editor page: standalone text view with JSON/CSV/XML export
- Activity page: job status polling and history
- Settings: default backend, Mistral API key + test, backend and scanner lists

### MCP Server
- Dual transport: stdio + HTTP
- 6 portmanteau tools: `process_document`, `manage_image`, `operate_scanner`, `manage_workflow`, `manage_corpus`, `get_help`, `get_status`
- 14 OCR backends with lazy loading + auto-selection
- Resources: `resource://ocr/logs`, `resource://ocr/capabilities`, `resource://ocr/skills`
- Sampling handler for agentic workflows

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
- OpenAPI docs at `/docs`

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
- Legacy `frontend/` directory removed — all functionality lives in `web_sota/`

## Recent Milestones

| Date | Milestone |
|------|-----------|
| 2026-07-21 | Unlimited-OCR backend added (Baidu, MIT, 3B params) |
| 2026-07-21 | Webapp streamlined: dashboard-first, removed legacy frontend, 5-page sidebar |
| 2026-06-14 | Tauri 2.0 NSIS wrapper + CUA smoke test |
| 2026-05-14 | Nemotron VL 8B backend |
| 2026-05-12 | MinerU2.5-Pro backend, backend management UI |
