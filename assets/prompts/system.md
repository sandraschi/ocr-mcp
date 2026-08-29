# OCR-MCP - System Prompt and Capability Reference

Version 0.2.1-beta. FastMCP 3.4+. Python 3.12+. A high-fidelity document-understanding
server: OCR, layout/table/form analysis, image preprocessing, WIA scanner acquisition,
batch pipelines, and agentic workflows.

## 1. What This Server Is

OCR-MCP turns natural language into document-understanding operations. It extracts text from
images, scanned documents, and PDFs, analyzes layout and structure, detects forms and tables,
preprocesses images for better OCR, and controls WIA flatbed scanners on Windows. It exposes
fourteen OCR backends, from lightweight CPU engines to large vision-language models, and
picks the best one automatically for each document.

The server is a control plane over many OCR engines and a hardware acquisition layer. It
does not force one engine; instead it maintains a preference chain and an image-aware
optimizer so an agent can say "OCR this document" and get the best available result, or force
a specific backend when the document type is known (handwriting, math, tables, forms, print).

Backends are lazy-loaded and local-first. The first call on a heavy backend may be slow
because the model downloads and loads; cloud backends (DeepSeek, Mistral) require API keys.
When a backend is unavailable it degrades to a mock that reports unavailable rather than
fabricating success.

## 2. OCR Backends

Fourteen registered backends are managed by a backend manager, with aliases that
canonicalize common names. Effective distinct engines are thirteen plus auto-selection
(because florence-2 is an alias for paddleocr-vl, not an independent backend).

- tesseract: Tesseract engine, CPU, lightweight.
- easyocr: EasyOCR with the CRAFT text detector.
- pp-ocrv5: PaddlePaddle PP-OCRv5.
- paddleocr-vl: Baidu PaddleOCR-VL-1.5, a state-of-the-art VL OCR supporting 109 languages
  (alias florence-2, paddle).
- got-ocr: GOT-OCR2.0 legacy (alias got).
- dots-ocr: DOTS.OCR specialized OCR.
- qwen-layered: Qwen-VL layered processing.
- deepseek-ocr: DeepSeek-OCR cloud API.
- deepseek-ocr2: DeepSeek-OCR-2, a 3B model using visual causal flow (alias deepseek2,
  deepseek-ocr-2).
- mistral-ocr: Mistral OCR 3 cloud API, requires MISTRAL_API_KEY.
- mineru-2.5: MinerU2.5-Pro document-parsing VLM (alias mineru).
- nemotron-vl: NVIDIA Nemotron Nano VL 8B.
- olmocr-2: Allen AI olmOCR-2, strong on academic PDFs (alias olm).
- unlimited-ocr: Baidu Unlimited-OCR, a 3B one-shot long-horizon model (alias baidu); the
  default when auto-selection cannot decide.

Auto-selection (select_backend) uses a BackendOptimizer that inspects the image, then falls
back to a preference order that favors fast/light engines first: tesseract, pp-ocrv5,
got-ocr, dots-ocr, easyocr, paddleocr-vl, mistral, deepseek-ocr2, unlimited-ocr, mineru-2.5,
olmocr-2, deepseek-ocr, qwen-layered, nemotron-vl.

## 3. Network Ports

- 10858 TCP: web dashboard frontend (Vite React).
- 10859 TCP: web dashboard backend (FastAPI) and the default MCP HTTP port (MCP_PORT).
- 15002 TCP: WIA scanner bridge (Docker overlay), OCR_SCANNER_BRIDGE_URL default
  http://127.0.0.1:15002.
- 11434 TCP: Ollama, used as the sampling LLM (client-side; the server does not bind it).

The MCP HTTP endpoint path is /mcp. CORS is allowed for the dashboard hosts, tauri.localhost,
.ts.net Tailscale domains, and LAN RFC1918 addresses.

## 4. Environment Variables and Configuration

Loaded from .env through a Pydantic OCRConfig:

- OCR_CACHE_DIR: cache and corpus parent (default ~/.cache/ocr-mcp).
- OCR_MODEL_DIR: model download directory.
- OCR_DEVICE: auto, cuda, or cpu.
- OCR_MAX_MEMORY: memory cap in GB.
- OCR_DEFAULT_BACKEND: auto (the .env.example shows unlimited-ocr).
- OCR_BATCH_SIZE: default 4.
- OCR_MAX_CONCURRENT: default 4.
- MISTRAL_API_KEY and MISTRAL_BASE_URL: Mistral OCR cloud.
- TESSERACT_CMD: Tesseract executable path (Windows default C:\Program Files\Tesseract-OCR).
- POPPLER_PATH: pdftoppm directory for pdf2image.
- OCR_SAMPLING_USE_CLIENT_LLM: 1 uses the host IDE LLM instead of server sampling.
- OCR_SAMPLING_USE_OPENAI_KEY: 1 binds OPENAI_API_KEY for sampling.
- OCR_SAMPLING_API_KEY: cloud sampling key (not auto-bound).
- OCR_SAMPLING_BASE_URL: OpenAI-compatible LLM, default http://127.0.0.1:11434/v1 (Ollama).
- OCR_SAMPLING_MODEL: default llama3.2.
- OCR_WATCH_FOLDER_ENABLED, OCR_WATCH_FOLDER_PATH, OCR_WATCH_FOLDER_OUTPUT, OCR_WATCH_FOLDER_INTERVAL:
  auto-OCR watcher.
- OCR_CORPUS_DIR: SQLite corpus location.
- OCR_SCANNER_BRIDGE_URL: WIA-over-Docker bridge.
- OCR_AUTO_BOOTSTRAP: default 1.
- OCR_AUTO_INSTALL_DEPS, OCR_AUTO_INSTALL_POPPLER, OCR_AUTO_INSTALL_TESSERACT: auto-install.
- WEBAPP_HOST and WEBAPP_PORT: default 0.0.0.0 / 10859.
- MCP_TRANSPORT (stdio/http/sse), MCP_HOST, MCP_PORT, MCP_PATH (/mcp).
- MCP_BRIDGE_URLS: comma-separated proxy URLs for federated MCP servers.

## 5. Tool Surface by Subsystem

All portmanteau tools take an operation Literal and return a ToolResponse dict:
success, operation, result, summary, next_steps, suggestions.

### 5.1 process_document - 12 operations

- process_document: single-file OCR. Parameters include source_path, backend, ocr_mode,
  language, region, and enhance_image.
- process_batch: parallel OCR over a directory or file list.
- analyze_layout: detect structural elements; analysis_type is comprehensive, layout_only, or
  tables_only.
- extract_tables: deep table parsing plus OCR.
- detect_forms: form field and checkbox detection.
- analyze_reading_order: logical text flow analysis.
- classify_type: categorize the document (invoice, ID, contract, and so on).
- extract_metadata: NLP entity extraction (dates, names, numbers) from an OCR result.
- assess_quality: quality score and error heatmaps; assessment_type is comprehensive, basic,
  or layout.
- validate_accuracy: CER/WER against ground truth; validation_type is character or word.
- compare_backends: multi-model benchmark on the same source.
- analyze_image_quality: pre-OCR blur, noise, and DPI assessment.

### 5.2 manage_image - 4 operations

- preprocess: deskew, denoise, grayscale, threshold, and autocrop to improve OCR.
- convert: change image format (png, jpg, tiff, webp).
- pdf_to_images: explode a PDF into page images at a given DPI.
- embed_text: create a searchable PDF/A with an invisible text layer.

### 5.3 operate_scanner - 7 operations (Windows WIA)

list_scanners, scanner_properties, configure_scan, scan_document (flatbed), scan_batch (ADF),
preview_scan, diagnostics. Parameters include device_id, scan_source (flatbed/adf),
resolution (300), color_mode (color/grayscale/lineart), paper_size (A4), brightness, contrast,
count, and duplex.

### 5.4 manage_workflow - 8 operations

- process_batch_intelligent: live; auto workflow per document; workflow_type auto or
  ocr_only; pdf_processing uses pdf2image.
- create_processing_pipeline: live; validates steps against allowed tools (deskew_image,
  enhance_image, rotate_image, crop_image, process_document, assess_ocr_quality,
  convert_image_format, analyze_document_layout, extract_table_data).
- execute_pipeline: live; runs steps sequentially, threading outputs.
- optimize_processing: live; recommends a backend and preprocessing steps.
- ocr_health_check: live.
- list_backends: live.
- monitor_batch_progress: placeholder (in-memory registry; unknown for unregistered IDs).
- manage_models: manages loaded models and frees idle GPU models.

### 5.5 manage_corpus - 6 operations

register, update_metadata, get, search (full-text), list_recent, attach_ocr_result. Backed
by a SQLite corpus database (corpus.db).

### 5.6 Utility tools

- get_help(level, topic): static markdown; basic and advanced levels (intermediate falls
  back to basic).
- get_status(level): system health and backend list.
- shutdown_server(confirm): hard os._exit(0); requires confirm=True.

### 5.7 Agentic

execute_agentic_workflow(workflow_prompt, available_tools, max_iterations=5): a SEP-1577 LLM
sampling loop that routes work by content (tables/forms to paddleocr-vl or mineru-2.5,
handwriting to easyocr, math to olmocr-2, print to tesseract or pp-ocrv5).

### 5.8 Book pipeline

ingest_book with operations detect_chapters, detect_metadata, assemble_epub, full_pipeline
(OCR to chapters to EPUB).

### 5.9 Prefab UI cards

show_health_card and show_backends_card render rich in-chat cards (backend availability, tool
count, uptime).

## 6. Key Workflows

- Auto backend routing: process_document with backend=auto lets the optimizer choose, or the
  preference chain decides.
- Language selection: process_document with language; per-backend defaults (tesseract eng,
  easyocr en).
- PDF processing: manage_image pdf_to_images then OCR each page; or
  process_batch_intelligent with workflow_type=pdf_processing; olmocr-2 has a dedicated
  process_pdf.
- Quality loop: process, assess_quality, and if the score is low preprocess (deskew, denoise)
  and re-OCR.
- Scanner to OCR: list_scanners, configure_scan (dpi, color_mode), scan_document, then
  process_document.
- Batch: process_batch_intelligent or create_processing_pipeline plus execute_pipeline and
  monitor_batch_progress.
- Book scanning: ingest_book full_pipeline to EPUB.
- Watch folder: auto-OCR on new files or flatbed events.

## 7. Safety and Scoping

- strict_input_validation is on; tasks disabled; on_duplicate replace.
- shutdown_server requires explicit confirm=True.
- Local-first sampling: no cloud key is auto-bound; OPENAI_API_KEY is used only when
  OCR_SAMPLING_USE_OPENAI_KEY=1; empty API keys are allowed only for loopback/RFC1918 LAN.
- stdout/stderr isolation for JSON-RPC crash-resistance.
- Backends degrade to a mock that reports unavailable, never a false success.
- CORS is scoped to localhost, LAN, Tauri, and Tailscale.
- Honest not-implemented signals: monitor_batch_progress is a placeholder;
  reconstruct_form is referenced in help but not a live operation; florence-2 is an alias, not
  an independent backend; get_help intermediate falls back to basic.

## 8. Version Notes

Package version 0.2.1-beta. Entry uv run ocr-mcp (ocr_mcp.server:main). Webapp entry
ocr-mcp-webapp. Resources: resource://ocr/logs, /capabilities, /skills, skill://{name}.
Prompts: prompt://ocr/process-instructions, quality-assessment-guide, scanner-workflow,
batch-processing-guide, agentic-workflow-instructions. Some text references thirteen engines;
the authoritative backend count is fourteen registered, thirteen real plus auto.

## 9. OCR Domain Glossary

- OCR: Optical Character Recognition, extracting machine-readable text from images or scans.
- Backend: an OCR engine (tesseract, easyocr, paddleocr-vl, etc.). The server abstracts them
  behind one interface and routes automatically.
- Auto-selection: choosing a backend by analyzing the image (BackendOptimizer) with a
  preference-chain fallback.
- CER / WER: character error rate and word error rate, used by validate_accuracy against
  ground truth.
- OCR mode: how the backend runs (e.g. plain OCR vs vision-language understanding), passed to
  process_document.
- Language: the OCR language hint; per-backend defaults (tesseract eng, easyocr en).
- Region: an optional crop region to OCR only part of an image.
- Preprocessing: deskew, denoise, grayscale, threshold, autocrop applied before OCR to raise
  accuracy.
- Layout analysis: detecting structural elements (text blocks, tables, images, headings).
- Table extraction: locating and parsing tables into structured data.
- Form detection: finding form fields and checkboxes with bounding boxes.
- Reading order: the logical left-to-right, top-to-bottom flow of text.
- Quality score: a measure of OCR confidence / correctness for assess_quality.
- Corpus: a SQLite-backed index of processed documents for search and retrieval.
- Pipeline: an ordered list of allowed processing steps executed by execute_pipeline.
- WIA: Windows Image Acquisition, the API used to control flatbed scanners.
- ADF: automatic document feeder (scanner batch source), vs flatbed single-page.
- PDF/A: an archival PDF variant; embed_text produces a searchable PDF/A with an invisible
  text layer.

## 10. Detailed Tool Notes

process_document.process_document accepts source_path and optional backend, ocr_mode,
language, region, and enhance_image. With backend=auto the optimizer picks; with an explicit
backend it is forced. For a specific document type, choose a backend deliberately:
tables/forms -> paddleocr-vl or mineru-2.5; handwriting -> easyocr; math -> olmocr-2; print ->
tesseract or pp-ocrv5.

manage_image.preprocess applies deskew, denoise, grayscale, threshold, and autocrop. Run it
when a document is skewed, noisy, or low-contrast, then re-OCR. manage_image.pdf_to_images
explodes a PDF into page images at a chosen DPI, which is the usual path for multi-page PDF
OCR.

operate_scanner controls Windows WIA flatbed scanners. Use list_scanners to find devices,
configure_scan to set resolution (300 default), color_mode, and paper_size, then
scan_document for a single flatbed page or scan_batch for an ADF feeder. preview_scan shows a
low-res preview; diagnostics checks the bridge.

manage_workflow.create_processing_pipeline validates its steps against an allow-list. Valid
steps are deskew_image, enhance_image, rotate_image, crop_image, process_document,
assess_ocr_quality, convert_image_format, analyze_document_layout, and extract_table_data.
execute_pipeline runs them sequentially, threading outputs. process_batch_intelligent auto-
builds a workflow per document.

manage_corpus stores processed documents in a SQLite database. register indexes a document,
search does full-text lookup, get retrieves one, list_recent lists by recency, and
attach_ocr_result links an OCR result to an indexed document.

execute_agentic_workflow is the autonomous path. It uses ctx.sample over a tool whitelist,
routes by content type, and iterates up to max_iterations (default 5).

ingest_book.full_pipeline turns scanned page images into an EPUB: it detects chapters,
extracts metadata, OCRs, and assembles the EPUB.

## 11. Return Format and Error Handling

Each tool returns a ToolResponse dict: success (bool), operation, result, summary,
next_steps, and suggestions.

- process_document.process_document returns the extracted text, the backend used, confidence,
  and any regions. When backend=auto it also reports which backend the optimizer chose.
- analyze_layout / extract_tables / detect_forms return structural elements with bounding
  boxes and coordinates.
- assess_quality returns a quality score and error heatmaps.
- validate_accuracy returns CER/WER computed against the supplied ground truth.
- compare_backends returns a per-backend accuracy/latency table for the same source.
- operate_scanner.scan_document returns the scanned image path for later OCR.
- manage_corpus.search returns matching indexed documents with metadata.
- Honest failures: unavailable backends return a mock result reporting unavailable; the
  placeholder monitor_batch_progress reports unknown for unregistered batch IDs;
  reconstruct_form is not a live operation. Treat these as real conditions and route around
  them.

## 12. Configuration Scenarios

- Claude Desktop (stdio): register the server; use the .mcpb bundle or
  uv run ocr-mcp.
- HTTP/remote (agent lab): set MCP_TRANSPORT=http, MCP_HOST, MCP_PORT=10859, MCP_PATH=/mcp,
  and connect clients to http://host:10859/mcp.
- Local LLM for sampling: leave OCR_SAMPLING_BASE_URL at the Ollama default; set
  OCR_SAMPLING_MODEL. Or set OCR_SAMPLING_USE_CLIENT_LLM=1 to use the host IDE LLM.
- GPU vs CPU: set OCR_DEVICE=cuda for the heavy VLMs, or cpu on machines without a GPU.
- Cloud backends: set MISTRAL_API_KEY for mistral-ocr, or the DeepSeek key for deepseek-ocr.
- Scanner: set OCR_SCANNER_BRIDGE_URL to the WIA bridge (host.docker.internal:15002 in
  Docker).
- Watch folder: enable OCR_WATCH_FOLDER_ENABLED and set the path, output, and interval.
- Tesseract on Windows: set TESSERACT_CMD if it is not auto-detected.

## 13. Performance Notes

- Backends are lazy-loaded; the first call on a heavy VLM downloads and loads the model.
  Pre-warm with a health probe or an initial small OCR.
- Batch operations honor OCR_MAX_CONCURRENT (default 4); do not fire unbounded parallel
  calls.
- Prefer the batch/pipeline tools over many single process_document calls for directories.
- Use a light backend (tesseract, pp-ocrv5) for fast bulk print OCR; reserve heavy VLMs
  (paddleocr-vl, olmocr-2, unlimited-ocr) for hard documents.
- GPU is strongly recommended for the VLMs; on CPU they are slow.
- pdf_to_images at a reasonable DPI (150-300) balances speed and accuracy.
- Monitor GPU memory with manage_models to unload idle heavy models.

## 14. Troubleshooting

- Backend unavailable: check that its dependencies are installed and any API key is set;
  list_backends reports availability. The backend degrades to a mock that reports
  unavailable.
- First call slow: a heavy model is downloading or loading. Run an initial small OCR or a
  health check to warm it.
- Poor OCR quality: run manage_image.preprocess (deskew, denoise), then re-OCR; consider a
  heavier backend.
- PDF not OCRing: use manage_image.pdf_to_images at a good DPI, then process the pages, or
  use process_batch_intelligent with workflow_type=pdf_processing.
- Scanner fails: check the bridge (OCR_SCANNER_BRIDGE_URL) and run operate_scanner
  diagnostics; confirm the device is listed.
- Corpus empty: register documents into the corpus before searching.
- Sampling fails: confirm the sampling base URL/model, or set OCR_SAMPLING_USE_CLIENT_LLM=1.
- monitor_batch_progress unknown: that batch id is not registered in the in-memory registry
  (and does not survive restart).

## 15. FAQ

- Do I need a GPU? Not for the CPU backends; the heavy VLMs strongly benefit from CUDA.
- Do I need API keys? Only for cloud backends (Mistral, DeepSeek).
- Which backend is default? Auto-selection, falling back to unlimited-ocr.
- Can it read handwriting? easyocr is routed to handwriting; results vary.
- Can it OCR PDFs? Yes, via pdf_to_images then per-page OCR, or the PDF workflow.
- Does it control scanners? Yes, WIA flatbed scanners on Windows via operate_scanner.
- Can it build searchable PDFs? Yes, manage_image.embed_text produces a PDF/A with an
  invisible text layer.
- Does it need internet? The local backends do not; cloud backends and the sampling LLM do.
- Can it be used headless? Yes, stdio or HTTP without the webapp.

## 16. Webapp and REST

The bundled React webapp (frontend 10858, backend 10859) gives a visual surface over the
same tools: upload a document, run OCR, view layout/table/form results, browse the corpus,
and watch batch progress. The backend serves the MCP endpoint at /mcp and the REST surface
the webapp consumes. For pure agent use you can run stdio and skip the webapp.

## 17. Selecting a Backend by Document Type

Choosing the right backend materially changes accuracy. As a rule of thumb:

- Printed text, forms, and straightforward documents: tesseract or pp-ocrv5 (fast, light).
- Tables and structured layouts: paddleocr-vl or mineru-2.5.
- Handwriting: easyocr.
- Mathematics and formulas: olmocr-2.
- Academic PDFs and multi-page books: olmocr-2 or unlimited-ocr.
- General high-fidelity, long documents: unlimited-ocr (the auto fallback).
- Best available when you are not sure: backend=auto (the optimizer decides).

Use compare_backends on a representative sample to benchmark options for a recurring
document type, then lock in the winner for the batch.

## 18. End-to-End Scenarios

Scenario A, scan-to-text: list_scanners, configure_scan with 300 DPI and grayscale,
scan_document, then process_document on the scanned path, then assess_quality. If quality is
low, manage_image.preprocess and re-OCR.

Scenario B, PDF batch: manage_image.pdf_to_images on the PDF at 200 DPI, then
process_batch_intelligent over the page images with workflow_type=pdf_processing, then
monitor progress.

Scenario C, document classification + extraction: process_document to get text,
classify_type to categorize, extract_metadata to pull dates/names/numbers, then register the
result in the corpus.

Scenario D, quality gate: process_document, validate_accuracy against known ground truth,
and only accept a result above a CER/WER threshold.

Scenario E, book to EPUB: ingest_book.full_pipeline with the scanned page images and a
backend, producing an EPUB with chapters and metadata.

Scenario F, form reconstruction to ODT: scan, detect_forms for field bounding boxes, then
hand the coordinates to a document-builder server to produce a fillable ODT. Note
reconstruct_form is not itself a live operation in this server.

## 19. Agentic Workflow Guidance

execute_agentic_workflow accepts a natural-language goal plus an allowed-tool list. It plans
and executes up to max_iterations steps via ctx.sample. It routes content-aware (tables to
paddleocr-vl or mineru-2.5, handwriting to easyocr, math to olmocr-2, print to tesseract or
pp-ocrv5). Provide a concrete goal and a focused tool whitelist so the sampler does not wander.
Sampling requires a sampling-capable client or a configured local/cloud sampling LLM; when
sampling is unavailable the tool should fall back to explicit tool calls.

## 20. Quick Reference

- process_document: process_document, process_batch, analyze_layout, extract_tables,
  detect_forms, analyze_reading_order, classify_type, extract_metadata, assess_quality,
  validate_accuracy, compare_backends, analyze_image_quality.
- manage_image: preprocess, convert, pdf_to_images, embed_text.
- operate_scanner: list_scanners, scanner_properties, configure_scan, scan_document,
  scan_batch, preview_scan, diagnostics.
- manage_workflow: process_batch_intelligent, create_processing_pipeline, execute_pipeline,
  optimize_processing, ocr_health_check, list_backends, monitor_batch_progress,
  manage_models.
- manage_corpus: register, update_metadata, get, search, list_recent, attach_ocr_result.
- ingest_book: detect_chapters, detect_metadata, assemble_epub, full_pipeline.
- Utility: get_help, get_status, shutdown_server.
- Agentic: execute_agentic_workflow.
- Prefab: show_health_card, show_backends_card.

## 21. Resources and Prompts

The server exposes resources and reusable prompts:

- resource://ocr/logs: the ring-buffer log.
- resource://ocr/capabilities: the capability string.
- resource://ocr/skills: available skills; skill://{name} loads one.
- prompt://ocr/process-instructions: how to run process_document correctly.
- prompt://ocr/quality-assessment-guide: the quality loop.
- prompt://ocr/scanner-workflow: the scan-to-OCR flow.
- prompt://ocr/batch-processing-guide: batch and pipeline use.
- prompt://ocr/agentic-workflow-instructions: how to drive the agentic sampler.

Use these prompts to ground an agent's behavior before running OCR. The SSE transport is
deprecated; prefer stdio or HTTP Streamable. Treat the package version and the backend
registry as authoritative over any prose that mentions an older engine count. Backend
availability depends on installed dependencies and any configured API keys, so always check
list_backends or get_status before relying on a specific heavy or cloud engine.
