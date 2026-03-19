# Technical architecture

OCR-MCP has **two entrypoints** that share **`OCRConfig`**, **`BackendManager`**, and the same **OCR backends**:

| Surface | Process | Transport | Typical use |
|---------|---------|-----------|-------------|
| **Web** | Uvicorn + `backend.app:app` | HTTP **10859**; browser **10858** (Vite proxies `/api`) | Humans: upload, scan, editor, settings |
| **MCP** | `ocr-mcp` / `python -m ocr_mcp.server` | **stdio** to the IDE | Agents: portmanteau tools, resources, prompts, sampling |

They are **not** the same OS process: web **Settings → Mistral** updates only the FastAPI worker; MCP clients must set **`MISTRAL_API_KEY`** (etc.) in their MCP config `env` if agents need **mistral-ocr**.

## Web app architecture (high level)

```
  Browser (Vite :10858)  ──proxy /api──►  FastAPI (:10859)  ──►  BackendManager  ──►  OCR backends
```

React routes live under **`web_sota/src`** (e.g. Import, Scanner, Editor, Settings, **`/help`**). User-facing documentation for all three surfaces is maintained in **`web_sota/src/pages/help.tsx`** (kept in sync with **INSTALL.md** / this file).

## MCP server architecture (high level)

```
  IDE (Cursor, Claude, …)  ◄──stdio──►  FastMCP (`src/ocr_mcp/server.py`)  ──►  BackendManager  ──►  same OCR backends
```

Portmanteau tools and resources are registered in **`ocr_mcp.tools`** and **`server.py`** (see below).

## Portmanteau tool ecosystem

### Document Processing
**`document_processing(operation, ...)`** — OCR, analysis, quality assessment  
- process_document, process_batch, analyze_layout, extract_tables, detect_forms  
- analyze_reading_order, classify_type, extract_metadata  
- assess_quality, validate_accuracy, compare_backends, analyze_image_quality  

### Image Management
**`image_management(operation, ...)`** — Preprocessing and format conversion  
- preprocess (deskew, denoise, grayscale, threshold, autocrop)  
- convert (PNG, JPG, TIFF, WebP)  
- pdf_to_images, embed_text (searchable PDF)  

### Scanner Operations (WIA, Windows)
**`scanner_operations(operation, ...)`** — Scanner hardware control  
- list_scanners, scanner_properties, configure_scan  
- scan_document, scan_batch, preview_scan, diagnostics  

### Workflow Management
**`workflow_management(operation, ...)`** — Batch and pipeline orchestration  
- process_batch_intelligent, create_processing_pipeline, execute_pipeline  
- monitor_batch_progress, optimize_processing  
- ocr_health_check, list_backends, manage_models  

### Help & Status
**`help(level, topic?)`** — basic | intermediate | advanced  
**`status(level)`** — basic | detailed  

## Configuration

### Environment variables

- **`OCR_CACHE_DIR`**: Model cache directory (default: `~/.cache/ocr-mcp`)
- **`OCR_DEVICE`**: Computing device (`cuda`, `cpu`, `auto`)
- **`OCR_MAX_MEMORY`**: Maximum GPU memory usage in GB
- **`OCR_DEFAULT_BACKEND`**: Default OCR backend (`got-ocr`, `tesseract`, etc.)
- **`OCR_BATCH_SIZE`**: Default batch processing size
- **`OCR_AUTO_BOOTSTRAP`**: If `1` (default), after `OCRConfig()` the process runs PyYAML dist-info repair, Tesseract (Windows), Poppler (Windows), and one-shot ML hints (e.g. missing flash-attn on CUDA). Set `0` to skip those (pip block below still applies).
- **`OCR_AUTO_INSTALL_DEPS`**: If `1`, after bootstrap the process may pip/uv install torch, transformers, optional Paddle, etc., and restart — see `ocr_mcp.utils.ocr_pip_install`.
- **`OCR_AUTO_INSTALL_TESSERACT`**: Windows only — if `1` (default), bootstrap tries silent Tesseract install (winget / choco / scoop). Set `0` to disable.
- **`OCR_AUTO_INSTALL_POPPLER`**: Windows only — if `1` (default), bootstrap may run `winget install oschwartz10612.Poppler` when `pdftoppm` is missing. Set `0` to only detect PATH / `POPPLER_PATH`.
- **`TESSERACT_CMD`**: Full path to `tesseract` executable when not on `PATH`
- **`POPPLER_PATH`**: Folder containing `pdftoppm` / `pdftoppm.exe` (passed to pdf2image)
- **`MISTRAL_API_KEY`** / **`MISTRAL_BASE_URL`**: Enable **mistral-ocr** for the **current process** (MCP stdio or env before Uvicorn). Web UI can also set key/base URL at runtime via **`POST /api/settings/mistral`** (FastAPI only).

### Web REST API (selected)

Implemented in **`backend/app.py`**. Examples:

- **`GET /api/backends`** — all registered backends with `available` + description
- **`GET|POST /api/settings/mistral`** — read/update Mistral credentials in-process
- **`POST /api/settings/mistral/test`** — validate key with **`GET {mistral_base_url}/models`** (optional body overrides for unsaved form values)

Full list: run the backend and open **`/docs`**.

### Backend-specific settings

```yaml
# config/ocr_config.yaml
backends:
  got_ocr:
    model_size: "base"  # or "large"
    cache_dir: "/models/got-ocr"
    device: "cuda:0"

  tesseract:
    language: "eng+fra+deu"
    config: "--psm 6"

  easyocr:
    languages: ["en", "fr", "de"]
    gpu: true
```

## Development status

- ✅ Phase 1–5: Core, backends, web UI, document processing, scanner
- 🟡 Phase 6: Production deployment (Alpha)
- 🔄 Phase 7–8: Beta, production release

See [OCR-MCP_MASTER_PLAN.md](../OCR-MCP_MASTER_PLAN.md) for roadmap.

## Development

1. **Clone:** `git clone https://github.com/sandraschi/ocr-mcp.git` then `cd ocr-mcp`
2. **Install [uv](https://docs.astral.sh/uv/) and Python 3.12+**
3. **Deps:** `uv sync` (add `--all-extras` or `--extra webapp` / `--extra ml` as needed)
4. **Dev (pytest, ruff, etc.):** `uv sync --extra dev`
5. **Optional:** `pre-commit install`; run with `pre-commit run --all-files`
6. **Tests:** `uv run python -m pytest` or `python scripts/run_tests.py --suite quick` — see [tests/README.md](../tests/README.md)
7. **Lint/format:** `uv run ruff check src backend tests scripts` and `uv run ruff format …` (or `just lint` / `just format` if defined)
8. **Webapp:** `web_sota\start.ps1` from repo root — see [INSTALL.md](INSTALL.md)  
9. **Web UI (alternate):** `just webapp` if defined in your justfile

### Packaging

```bash
mcpb pack . dist/ocr-mcp.mcpb
```

- **Glama.ai**: [glama.json](../glama.json) snippet for MCP client config
- **LLMs:** [llms.txt](../llms.txt) at repo root
- **Just:** [JUSTFILE.md](JUSTFILE.md) — `just install`, `just run`, etc.

## Contributing

Areas of interest: new OCR backends, performance (GPU/batch), domain models, documentation, tests.
