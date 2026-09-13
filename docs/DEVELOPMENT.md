# DEVELOPMENT — ocr-mcp

## Layout

- `src/ocr_mcp/server.py` — FastMCP app, lifespan, resources/prompts, tool registration
- `src/ocr_mcp/tools/` — portmanteau tools (`ocr_tools.py`) + handlers
  (`_processor`, `_analysis`, `_conversion`, `_image`, `_quality`,
  `_scanner`, `_workflow`, `_corpus`), `agentic_document_workflow.py`,
  `book_pipeline.py`, `llm_ops.py`, `_prefab.py`, `models.py`
- `src/ocr_mcp/backends/` — 14 engines + `scanner/` (WIA) + legacy runners
- `src/ocr_mcp/core/` — `BackendManager`, `OCRConfig`, `ErrorHandler`, model manager
- `src/ocr_mcp/services/` — backend-side services (`apps_routes`, `llm_engine`, …)
- `src/ocr_mcp/skills/ocr-expert/` — skill definition; `sampling/` — sampling handler
- `backend/app.py` — FastAPI dashboard backend (REST, see CONFIGURATION.md)
- `web_sota/` — React + Vite + Tailwind + Zustand dashboard (port 10858)
- `native/` — Tauri shell (NSIS target); `scripts/` — just modules, CUA smoke, models
- `tests/` — unit, integration, e2e, fuzzing (hypothesis), performance, security

Onboarding: N/A is **not** claimed — this repo has a wrappee (Tesseract/
scanner hardware) and an online account path (Mistral) → full onboarding
applies (`docs/ONBOARDING.md`, under-hero CTA, MOCK-until-onboarded).

## Daily commands

```powershell
C:\Users\sandr\.local\bin\uv.exe sync            # deps
C:\Users\sandr\.local\bin\uv.exe run ruff check src/ backend/ run_server.py
C:\Users\sandr\.local\bin\uv.exe run ruff format src/ backend/
C:\Users\sandr\.local\bin\uv.exe run pytest tests/ -q -p no:cacheprovider --ignore=tests/benchmarks
just lint            # ruff + biome (web_sota)
just webapp          # backend :10859 + frontend :10858
```

Ruff policy: `T20` (no `print` in server code — use `logging`), and `S110`/
`S112` are **not** ignored: silent `except: pass/continue` must log
(`logger.debug(..., exc_info=True)`). CLI runner scripts (`*_runner.py`)
keep stdout-JSON protocol via per-file `T20` ignores.

## Conventions

- Tools are portmanteau (`operation` enum), verb-led snake_case, dialogic
  returns (`success`/`message`/`data`), docstrings carry `## Return Format`
  + `## Examples`; list/status/stats tools get Prefab `app=True` cards.
- `ErrorHandler` is the only error vocabulary (`OCRError`, `PATH_TRAVERSAL`,
  …). `validate_file_path` fails closed (traversal/null-byte/stat-refused →
  error, never raise).
- Tests use declared doubles: `MockBackendFactory` (dict-contract payloads),
  `mock_scanner_manager`, `_flat()` response adapter in integration/e2e.
  Perf thresholds assume mocks (no lower-bound inference timing).
- Batch edits (3+ files) take timestamped `.bak` copies first; `*.bak*` is
  gitignored + mcpbignored, clean up before commit.
