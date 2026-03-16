# Technical architecture

## WebApp architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Web Interface                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐  │
│  │ Single  │  │   Batch    │  │  Image     │  │   Doc    │  │
│  │ Upload  │  │ Processing │  │  Preproc   │  │ Analysis │  │
│  └─────────┘  └────────────┘  └────────────┘  └──────────┘  │
│  ┌─────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐  │
│  │ Quality │  │ Workflows  │  │ Conversion │  │ Scanner  │  │
│  │ Assess  │  │ & Pipelines│  │ & Export   │  │ Control  │  │
│  └─────────┘  └────────────┘  └────────────┘  └──────────┘  │
├─────────────────────────────────────────────────────────────┤
│                 FastMCP Server (20+ Tools)                  │
├─────────────────────────────────────────────────────────────┤
│   OCR Engines ┌──┬──┬──┬──┬──┬──┬──┐  Document Processing   │
│               │M │D │F │D │P │Q │E │  Image Analysis        │
│               │3 │S │2 │O │P │I │O │  Quality Assessment    │
│               └──┴──┴──┴──┴──┴──┴──┘  Workflow Automation   │
└─────────────────────────────────────────────────────────────┘
```

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
3. **Deps:** `uv sync --all-extras`
4. **Optional:** `pre-commit install`; run with `pre-commit run --all-files`
5. **Tests:** `just test` or `uv run pytest`
6. **Lint/format:** `just lint`, `just format`
7. **Web UI:** `just webapp`

### Packaging

```bash
mcpb pack . dist/ocr-mcp.mcpb
```

- **Glama.ai**: [glama.json](../glama.json) snippet for MCP client config
- **LLMs:** [llms.txt](../llms.txt) at repo root
- **Just:** [JUSTFILE.md](JUSTFILE.md) — `just install`, `just run`, etc.

## Contributing

Areas of interest: new OCR backends, performance (GPU/batch), domain models, documentation, tests.
