# CONFIGURATION — ocr-mcp

All knobs. Copy `.env.example` to `.env`; every variable below has a default
in code so the server also starts with no `.env` at all.

## Ports (fleet registry, adjacent pair)

| Process | Port | Source |
|---|---|---|
| Dashboard frontend (Vite) | **10858** | `web_sota/vite.config.ts`, `fleet-start.config.ps1` |
| REST backend (FastAPI/uvicorn) | **10859** | `WEBAPP_PORT`, `MCP_PORT`, `fleet-start.config.ps1` |

`web_sota/vite.config.ts` proxies `/api` → `http://127.0.0.1:10859`.
Forbidden fleet ports (3000, 5000, 5173, 8000, 8080) are never used.

## Environment variables (`.env.example` is the template)

| Variable | Default | Effect |
|---|---|---|
| `OCR_CACHE_DIR` | `~/.cache/ocr-mcp` | OCR working cache |
| `OCR_MODEL_DIR` | (cache subdir) | VLM weight downloads (GBs) |
| `OCR_DEVICE` | `auto` | `auto`/`cuda`/`cpu` |
| `OCR_DEFAULT_BACKEND` | `unlimited-ocr` | Backend for `backend="auto"` resolution fallback |
| `OCR_BATCH_SIZE` / `OCR_MAX_CONCURRENT` | `4` / `4` | Batch parallelism |
| `MISTRAL_API_KEY` / `MISTRAL_BASE_URL` | (empty) | Cloud Mistral OCR; empty = disabled |
| `TESSERACT_CMD` | PATH lookup | Override tesseract binary |
| `POPPLER_PATH` | PATH lookup | PDF rendering helper |
| `OCR_SAMPLING_USE_CLIENT_LLM` | `0` | `1` = prefer MCP host LLM for agentic sampling |
| `OCR_SAMPLING_API_KEY` / `OCR_SAMPLING_BASE_URL` / `OCR_SAMPLING_MODEL` | Ollama localhost / `llama3.2` | Local-first sampling endpoint |
| `OCR_WATCH_FOLDER_ENABLED` / `_PATH` / `_OUTPUT` / `_INTERVAL` | `0` | Auto-OCR drop folder |
| `OCR_CORPUS_DIR` | (cache subdir) | SQLite document index location |
| `OCR_SCANNER_BRIDGE_URL` | `http://127.0.0.1:15002` | WIA-over-Docker bridge |
| `OCR_AUTO_BOOTSTRAP` / `OCR_AUTO_INSTALL_*` | `1` / `0` | Startup dependency bootstrap |
| `WEBAPP_HOST` / `WEBAPP_PORT` | `0.0.0.0` / `10859` | Backend bind |
| `MCP_TRANSPORT` / `MCP_HOST` / `MCP_PORT` / `MCP_PATH` | `stdio` / `127.0.0.1` / `10859` / `/mcp` | `stdio` = Claude Desktop; `http` = dashboard/sidecar |

## LLM providers (Chat + AI Settings)

Auto-detected on page mount via `GET /api/llm/providers` (Ollama `:11434`,
LM Studio `:1234`, GPU inventory via `/api/llm/gpus`). Cloud keys are stored
server-side only (`POST /api/settings/llm`, never in localStorage); the Chat
page talks to `POST /api/llm/chat` + `/stream` — keys never reach the browser.
Selection persists in localStorage keys `llm_provider` / `llm_model`.

## MCP surface (Claude Desktop)

8 portmanteau tools + extras, registered in `src/ocr_mcp/server.py`:

`process_document` (12 ops), `manage_image` (4), `operate_scanner` (7),
`manage_workflow` (8), `manage_corpus` (6), `get_help`, `get_status`,
`shutdown_server`, plus `execute_agentic_workflow` (SEP-1577 sampling),
book-pipeline tool, `llm_ops`, Prefab `show_health_card`/`show_backends_card`.
Resources: `resource://ocr/{logs,capabilities,skills}`, `skill://{name}`.
Prompts: `prompt://ocr/{process-instructions,quality-assessment-guide,
scanner-workflow,batch-processing-guide,agentic-workflow-instructions}`.

## REST surface (dashboard)

Liveness: `GET /api/health`, `GET /api/v1/system/info`,
`GET /api/v1/diagnostics`. Domain: `/api/backends`, `/api/scanners`,
`/api/job/{job_id}`, `/api/process_batch`, `/api/upload`,
`/api/ocr/*` (book pipeline, chapters, metadata, epub),
`/api/corpus*` (index search/register), `/api/pipelines*`,
`/api/server_logs`, `/api/tools`, `/api/skills*`,
`/api/fleet/apps` (Apps Hub discovery), `/api/llm/*` (providers, models,
chat proxy, onboarding, install), `/api/settings/*`.
