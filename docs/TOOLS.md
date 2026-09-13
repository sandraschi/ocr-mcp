# TOOLS — ocr-mcp

Source of truth for behavior is the docstrings in `src/ocr_mcp/tools/`.
This page is the map, not the manual.

## MCP tools (`src/ocr_mcp/server.py` + `tools/ocr_tools.py`)

| Tool | Operations | Needs |
|---|---|---|
| `process_document` | `process_document`, `process_batch`, `analyze_layout`, `extract_tables`, `detect_forms`, `analyze_reading_order`, `classify_type`, `extract_metadata`, `assess_quality`, `validate_accuracy`, `compare_backends`, `analyze_image_quality` | file path / OCR result |
| `manage_image` | `preprocess`, `convert`, `pdf_to_images`, `embed_text` | image path |
| `operate_scanner` | `list_scanners`, `scanner_properties`, `configure_scan`, `scan_document`, `scan_batch`, `preview_scan`, `diagnostics` | WIA scanner (Windows) |
| `manage_workflow` | `process_batch_intelligent`, `create_processing_pipeline`, `execute_pipeline`, `monitor_batch_progress`, `optimize_processing`, `ocr_health_check`, `list_backends`, `manage_models` | `source_dir` for batch ops |
| `manage_corpus` | `register`, `update_metadata`, `get`, `search`, `list_recent`, `attach_ocr_result` | — (local SQLite) |
| `execute_agentic_workflow` | goal-driven multi-step OCR via sampling (SEP-1577) | local LLM (Ollama default) |
| book-pipeline tool | chapter detect, metadata, EPUB assembly | book scan dir |
| `llm_ops` | provider/model ops shared with AI Settings | — |
| `show_health_card`, `show_backends_card` | Prefab in-chat cards | — |
| `get_help`, `get_status`, `shutdown_server` | docs / health / graceful stop | (`shutdown_server` needs `confirm=true`) |

Backend alias note: `canonical_backend_name` maps retired names —
`florence-2` → `paddleocr-vl`. Requesting `florence-2` resolves (and
reports) as `paddleocr-vl`; tests must use canonical names for identity
assertions.

## Canonical call shapes

```python
process_document(operation="process_document", source_path="page.png", backend="auto")
process_document(operation="process_batch", source_path="D:/scans/batch1")
operate_scanner(operation="list_scanners")
operate_scanner(operation="scan_document", device_id="wia:...", resolution=300,
                color_mode="color", save_path="D:/scans/p1.png")
manage_workflow(operation="ocr_health_check")
manage_workflow(operation="process_batch_intelligent", source_dir="D:/scans/batch1")
manage_corpus(operation="search", query="invoice")
```

Scanner enums: `color_mode` ∈ `color|grayscale|lineart`; `resolution` is an
int DPI (the handler field is `dpi` — the tool field is `resolution`).

## Just recipes (`just --list`)

`run`/`serve` (stdio server), `test`, `lint`/`fix`/`format` (ruff + biome),
`webapp` (backend+frontend), `bootstrap`, `check` (pre-commit all),
`check-sec` (bandit), `install-models`, `stats`, plus fleet-vendored
`mcpb-pack`, `cua-nsis-test`, `cua-webapp-test`, `zombie-clean`, gpu helpers.
