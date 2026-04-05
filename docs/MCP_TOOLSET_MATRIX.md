# MCP server toolset matrix

Audit of **stdio** tools registered from `src/ocr_mcp/tools/ocr_tools.py` plus **agentic_document_workflow** (`agentic_document_workflow.py`). Last reviewed: **2026-03-19**.

| Tool | Role | Status | Notes |
|------|------|--------|--------|
| **document_processing** | OCR, layout, quality | **Implemented** | 12 `operation` values wired in `ocr_tools.py` → `_processor` / `_analysis` / `_quality`. |
| **image_management** | Preprocess, convert, PDF | **Implemented** | `preprocess`, `convert`, `pdf_to_images`, `embed_text`. |
| **scanner_operations** | WIA (Windows) | **Implemented** | Delegates `_scanner.handle_scanner_op`. |
| **workflow_management** | Batch, pipelines, health | **Mixed** | **Fixed 2026-03:** MCP args now go through `handle_mcp_workflow` (maps `source_dir` → file list). `process_batch_intelligent` / `optimize_processing` / `execute_pipeline` / `create_processing_pipeline` are real; **`monitor_batch_progress`**, **`manage_models`** are **placeholders**. |
| **corpus_management** | Local document index | **Implemented (v0)** | SQLite under `OCR_CORPUS_DIR` or `{cache_dir}/corpus`. Ops: `register`, `get`, `search`, `list_recent`, `update_metadata`, `attach_ocr_result`. |
| **help** | Text help | **Minimal** | `_workflow.get_help_content` only **basic/advanced** stubs — expand later. |
| **status** | Health dict | **Basic** | `get_system_status` lists backends; not deep per-backend metrics. |
| **agentic_document_workflow** | SEP-1577 sampling | **Implemented** | Registered in `server.py` when import succeeds. |

## document_processing — operations

| operation | Handler | Status |
|-----------|---------|--------|
| process_document | `_processor.process_document` | **Live** |
| process_batch | `_processor.process_batch` | **Live** |
| analyze_layout | `_analysis.analyze_document_layout` | **Live** (depth varies by backend) |
| extract_tables | `_analysis.extract_table_data` | **Live** |
| detect_forms | `_analysis.detect_form_fields` | **Live** |
| analyze_reading_order | `_analysis.analyze_document_reading_order` | **Live** |
| classify_type | `_analysis.classify_document_type` | **Live** |
| extract_metadata | `_analysis.extract_document_metadata` | **Live** |
| assess_quality | `_quality.assess_ocr_quality` | **Live** |
| validate_accuracy | `_quality.validate_ocr_accuracy` | **Live** |
| compare_backends | `_quality.compare_ocr_backends` | **Live** |
| analyze_image_quality | `_quality.analyze_image_quality` | **Live** |

## workflow_management — `source_dir` convention

- **File:** single path added to `document_paths`.
- **Directory:** non-recursive; supported extensions: `.pdf`, images, `.cbz`, `.cbr`.
- **`pipeline_config`:** optional keys: `steps`, `input_documents`, `workflow_type`, `quality_threshold`, `max_concurrent`, `save_intermediates`, `execution_mode`, `quality_gates`, `error_handling`, `batch_id`, `detailed`, `focus`, etc.

## corpus_management — env

| Variable | Purpose |
|----------|---------|
| **`OCR_CORPUS_DIR`** | Override corpus folder (default: `{OCR_CACHE_DIR or ~/.cache/ocr-mcp}/corpus`). DB file: `corpus.db`. |

## Doc / naming hygiene

- Prefer **paddleocr-vl** in docs; **florence-2** / **florence** are **aliases** in `backend_manager` → paddleocr-vl.
- Server prompts in `server.py` should list current backends, not removed Florence-only stacks.

## Related

- [TECHNICAL.md](TECHNICAL.md) — architecture  
- [AI_FEATURES.md](AI_FEATURES.md) — sampling / agentic  
