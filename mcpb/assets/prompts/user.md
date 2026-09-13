# OCR-MCP - User Guide and Tutorials

Version 0.2.1-beta. This guide is the companion to system.md. It walks through installing
and configuring the server, then gives concrete tutorials for the workflows people actually
run: single-document OCR, quality improvement, PDF processing, scanner capture, batch and
pipeline processing, corpus management, and book scanning.

## 1. Introduction

OCR-MCP turns natural language into document-understanding operations. You ask an assistant
to "OCR this scanned receipt and extract the date and total" and the server runs an OCR
backend, extracts the text, and pulls out the metadata. It supports fourteen OCR backends,
from lightweight CPU engines to large vision-language models, and chooses the best one
automatically. It can also control WIA flatbed scanners on Windows, so a fully scanned
document can go from the scanner to OCR in one flow.

This guide assumes you have Python 3.12+, uv, and have installed the server. Heavy
vision-language backends benefit from a CUDA GPU but are not required; the lightweight
engines (tesseract, pp-ocrv5) run on CPU.

## 2. Installation and First Run

### 2.1 Install and bootstrap

```powershell
git clone https://github.com/sandraschi/ocr-mcp
cd ocr-mcp
uv sync
```

The first run may bootstrap model downloads. You can pre-install models with:

```powershell
uv run ocr-mcp-install-models
```

### 2.2 Verify a backend

Call get_status (or ocr_health_check) to confirm the server is up and which backends are
available. Backends that lack installed dependencies or an API key report unavailable rather
than failing.

### 2.3 Run it

For an AI-only MCP server (Claude Desktop / Cursor):

```powershell
uv run ocr-mcp
```

For HTTP/remote use:

```powershell
set MCP_TRANSPORT=http
uv run ocr-mcp
```

The server then listens on http://127.0.0.1:10859/mcp by default.

### 2.4 Register in an MCP host

Add to your MCP host config (or use the packaged .mcpb bundle):

```json
"mcpServers": {
  "ocr-mcp": { "command": "uv", "args": ["run", "ocr-mcp"] }
}
```

## 3. Configuration Reference

Most settings come from environment variables (see system.md section 4). The ones you are
most likely to change:

- OCR_DEVICE: set cuda for GPU, or cpu.
- OCR_DEFAULT_BACKEND: force a default backend instead of auto.
- MISTRAL_API_KEY: needed for the mistral-ocr cloud backend.
- TESSERACT_CMD: Tesseract path on Windows if not auto-detected.
- OCR_SAMPLING_MODEL / OCR_SAMPLING_BASE_URL: the sampling LLM for agentic work.
- OCR_WATCH_FOLDER_ENABLED: turn on the auto-OCR watcher.

## 4. Tutorial 1 - OCR a Single Image

Goal: extract text from one image.

1. Call process_document with operation=process_document and source_path.
2. Let backend default to auto, or pass an explicit backend.
3. Read the result: text, backend used, and confidence.
4. If the text is poor, see Tutorial 2.

## 5. Tutorial 2 - Improve OCR Quality

Goal: get a better result from a poor scan.

1. Call process_document to get a baseline.
2. Call manage_image with operation=preprocess and source_path to deskew, denoise, grayscale,
   threshold, and autocrop.
3. Call process_document again on the preprocessed image.
4. Optionally analyze image quality first with process_document operation=analyze_image_quality
   to see whether blur, noise, or DPI is the problem.

## 6. Tutorial 3 - OCR a PDF

Goal: extract text from a multi-page PDF.

1. Call manage_image with operation=pdf_to_images and source_path to explode pages to images
   at a chosen DPI (150-300).
2. OCR each page with process_document operation=process_batch, or run the PDF workflow with
   manage_workflow operation=process_batch_intelligent and workflow_type=pdf_processing.
3. If you have the olmocr-2 backend, use its dedicated process_pdf for academic PDFs.

## 7. Tutorial 4 - Analyze Layout and Extract Tables

Goal: understand the structure of a document.

1. Call process_document with operation=analyze_layout and source_path.
2. For tables specifically, call operation=extract_tables.
3. For reading order, call operation=analyze_reading_order.
4. Use the bounding-box coordinates to know where each element sits.

## 8. Tutorial 5 - Detect Forms

Goal: find form fields and checkboxes.

1. Call process_document with operation=detect_forms and source_path.
2. Read the field/checkbox bounding boxes.
3. To build a fillable form, hand the coordinates to a document-builder server (note:
   reconstruct_form is not a live operation in this server).

## 9. Tutorial 6 - Classify a Document and Extract Metadata

Goal: categorize a document and pull out key entities.

1. Call process_document to get the text.
2. Call process_document with operation=classify_type to categorize (invoice, ID, contract).
3. Call operation=extract_metadata to pull dates, names, and numbers from the OCR result.
4. Register the result in the corpus (Tutorial 11).

## 10. Tutorial 7 - Measure and Validate Accuracy

Goal: know how good the OCR is.

1. Call process_document with operation=assess_quality on the OCR result.
2. If you have ground truth, call operation=validate_accuracy with the ground_truth to get
   CER/WER.
3. Call operation=compare_backends on a representative sample to benchmark engines.

## 11. Tutorial 8 - Scan a Document (Windows WIA)

Goal: capture a page from a flatbed scanner and OCR it.

1. Call operate_scanner with operation=list_scanners to find devices.
2. Call operation=scanner_properties to see a device's capabilities.
3. Call operation=configure_scan with resolution=300, color_mode=grayscale, paper_size=A4.
4. Call operation=scan_document to capture (or scan_batch with count for an ADF feeder).
5. Pipe the scanned image to process_document.

## 12. Tutorial 9 - Batch Process a Directory

Goal: OCR every file in a folder.

1. Call manage_workflow with operation=process_batch_intelligent and the image paths or a
   directory, with workflow_type=auto or ocr_only.
2. Let the server build an auto workflow per document.
3. Call operation=monitor_batch_progress to check status (note: it is an in-memory registry
   and does not survive restart).

## 13. Tutorial 10 - Build and Run a Pipeline

Goal: run a fixed sequence of processing steps.

1. Call manage_workflow with operation=create_processing_pipeline and a list of steps from
   the allowed set (deskew_image, enhance_image, rotate_image, crop_image, process_document,
   assess_ocr_quality, convert_image_format, analyze_document_layout, extract_table_data).
2. Call operation=execute_pipeline with the pipeline id.
3. Review the threaded step outputs.

## 14. Tutorial 11 - Manage the Corpus

Goal: index and search processed documents.

1. Call manage_corpus with operation=register and a document path.
2. Call operation=update_metadata to add metadata.
3. Call operation=search with a full-text query to find documents.
4. Call operation=list_recent for the newest, or operation=attach_ocr_result to link an OCR
   result to an indexed document.

## 15. Tutorial 12 - Turn Scanned Pages into an EPUB

Goal: convert scanned book pages into a readable EPUB.

1. Scan or collect the page images.
2. Call ingest_book with operation=full_pipeline, image_paths, and a backend (unlimited-ocr
   is a good choice).
3. The server detects chapters, extracts metadata, OCRs, and assembles the EPUB.
4. You can also run detect_chapters and detect_metadata separately.

## 16. Tutorial 13 - Use the Watch Folder

Goal: auto-OCR files as they appear.

1. Set OCR_WATCH_FOLDER_ENABLED=true and configure the path, output, and interval.
2. Drop files into the watched folder; the server OCRs them automatically.
3. Retrieve results from the output directory or the corpus.

## 17. Tutorial 14 - Run an Agentic Workflow

Goal: accomplish a multi-step OCR task autonomously.

1. Call execute_agentic_workflow with a concrete goal (for example "OCR this batch of
   invoices and extract the totals").
2. Pass an allowed tool whitelist.
3. The sampler plans and executes up to max_iterations steps, routing by content type.

## 18. Tutorial 15 - Use a Local or Cloud Sampling LLM

Goal: enable the agentic sampler.

1. By default sampling uses Ollama at http://127.0.0.1:11434/v1 with model llama3.2.
2. To use the host IDE LLM, set OCR_SAMPLING_USE_CLIENT_LLM=1.
3. To use a cloud key, set OCR_SAMPLING_API_KEY and OCR_SAMPLING_BASE_URL, or set
   OCR_SAMPLING_USE_OPENAI_KEY=1 to bind OPENAI_API_KEY.
4. Verify sampling works with a small execute_agentic_workflow call.

## 19. REST and Webapp Notes

The webapp (frontend 10858, backend 10859) gives a visual surface: upload, OCR, layout/table/
form views, corpus browsing, and batch progress. The MCP endpoint is served at /mcp on the
backend port. For pure agent use, stdio mode needs no webapp.

## 20. Troubleshooting

- A backend reports unavailable: its dependencies or API key are missing; list_backends shows
  availability. Install deps or set the key.
- First OCR is slow: a heavy model is downloading/loading. Run a warm-up OCR or a health
  check.
- Poor quality: preprocess (deskew, denoise) and re-OCR; consider a heavier backend; check
  image quality first.
- PDF fails: pdf_to_images at a good DPI, then per-page OCR or the PDF workflow.
- Scanner fails: check OCR_SCANNER_BRIDGE_URL and run operate_scanner diagnostics.
- Corpus search returns nothing: register documents first.
- Sampling fails: confirm the sampling URL/model, or use the client LLM.
- monitor_batch_progress unknown id: the registry is in-memory and resets on restart.

## 21. FAQ

- Do I need a GPU? Not for CPU backends; the heavy VLMs benefit strongly from CUDA.
- Do I need API keys? Only for cloud backends (Mistral, DeepSeek).
- Which backend is default? Auto, falling back to unlimited-ocr.
- Can it read handwriting? easyocr is routed to handwriting; results vary.
- Can it OCR PDFs? Yes, via pdf_to_images and the PDF workflow.
- Does it control scanners? Yes, WIA flatbed scanners on Windows.
- Can it build searchable PDFs? Yes, manage_image embed_text.
- Does it need internet? Local backends no; cloud backends and sampling LLM yes.
- Can I use it headless? Yes, stdio or HTTP without the webapp.
- How do I pick a backend? backend=auto, or force one based on document type; use
  compare_backends to benchmark.

## 22. Best Practices

- Inspect quality before trusting output: assess_quality or validate_accuracy.
- Preprocess poor sources before re-OCR.
- Use batch/pipeline tools for directories instead of many single calls.
- Use the light engines for bulk print OCR; reserve heavy VLMs for hard documents.
- Register important results in the corpus for later retrieval.
- Check list_backends / get_status before relying on a heavy or cloud engine.
- Keep API keys out of source control.

## 23. Choosing a Backend by Document Type

Matching the backend to the document materially changes accuracy:

- Printed text, forms, straightforward documents: tesseract or pp-ocrv5 (fast, light).
- Tables and structured layouts: paddleocr-vl or mineru-2.5.
- Handwriting: easyocr.
- Mathematics and formulas: olmocr-2.
- Academic PDFs and multi-page books: olmocr-2 or unlimited-ocr.
- General high-fidelity long documents: unlimited-ocr (the auto fallback).
- Not sure: backend=auto, let the optimizer decide.

To benchmark options for a recurring document type, run process_document
operation=compare_backends on a representative sample and lock in the winner.

## 24. Understanding Backend Availability

Backends are lazy-loaded and local-first. Availability depends on:

- Installed Python dependencies (torch, transformers, addict, matplotlib for the heavy VLMs).
- A configured API key for cloud backends (mistral-ocr needs MISTRAL_API_KEY; deepseek-ocr
  needs the DeepSeek key).
- Hardware (CUDA strongly helps the VLMs; on CPU they are slow).

When a backend is unavailable it degrades to a mock that reports unavailable rather than a
false success. Always check list_backends or get_status before relying on a heavy or cloud
engine.

## 25. Deep Dive: process_document Parameters

process_document operation=process_document accepts:

- source_path: the image or PDF to OCR.
- backend: auto (default) or a specific backend key.
- ocr_mode: how the backend runs (plain OCR vs vision-language understanding).
- language: a language hint; defaults differ per backend (tesseract eng, easyocr en).
- region: an optional crop to OCR only part of the image.
- enhance_image: whether to preprocess before OCR.

For a two-page flow, call pdf_to_images first (Tutorial 3), then OCR the page images.

## 26. Deep Dive: manage_image Operations

- preprocess: deskew, denoise, grayscale, threshold, autocrop. Run on skewed or noisy scans
  before OCR.
- convert: change format to png, jpg, tiff, or webp.
- pdf_to_images: explode a PDF into page images at a chosen DPI (150-300 is a good balance).
- embed_text: create a searchable PDF/A with an invisible text layer, useful for archiving.

## 27. Deep Dive: operate_scanner Operations

The scanner tools drive WIA flatbed scanners on Windows:

- list_scanners: discover connected devices.
- scanner_properties: show a device's capabilities.
- configure_scan: set resolution (300 default), color_mode (color/grayscale/lineart),
  paper_size (A4), brightness, contrast.
- scan_document: capture a single flatbed page.
- scan_batch: feed an ADF with a count and optional duplex.
- preview_scan: capture a low-res preview.
- diagnostics: check the scanner bridge.

The scanner is reached through a bridge (OCR_SCANNER_BRIDGE_URL, default
http://127.0.0.1:15002; host.docker.internal:15002 in Docker). If scanning fails, run
diagnostics and confirm the bridge is up.

## 28. Deep Dive: manage_workflow and Pipelines

- process_batch_intelligent: auto-builds a workflow per document. workflow_type=auto or
  ocr_only; pdf_processing handles PDFs via pdf2image.
- create_processing_pipeline: validates steps against an allow-list. Allowed steps are
  deskew_image, enhance_image, rotate_image, crop_image, process_document,
  assess_ocr_quality, convert_image_format, analyze_document_layout, extract_table_data.
- execute_pipeline: runs the steps sequentially, threading outputs.
- optimize_processing: recommends a backend and preprocessing steps for a source.
- ocr_health_check: liveness.
- list_backends: enumerate backends and availability.
- monitor_batch_progress: placeholder, in-memory only.
- manage_models: inspect and unload loaded GPU models.

## 29. Deep Dive: manage_corpus

The corpus is a SQLite database (corpus.db) under OCR_CORPUS_DIR. Operations:

- register: index a document.
- update_metadata: attach metadata.
- get: retrieve one document.
- search: full-text query.
- list_recent: newest documents.
- attach_ocr_result: link an OCR result to an indexed document.

Use the corpus for repeated retrieval of processed documents and results.

## 30. REST / Webapp Worked Notes

The backend serves the MCP endpoint at /mcp on port 10859 and the webapp on 10858. Upload a
document in the webapp, run OCR, and browse layout/table/form results and the corpus. The
webapp is a visual front over the same tool surface; it is optional for agent use.

## 31. End-to-End Scenario: Receipt Extraction

1. manage_image operation=preprocess on the receipt photo (denoise, deskew).
2. process_document operation=process_document on the preprocessed image.
3. process_document operation=extract_metadata on the OCR result to pull the date and total.
4. process_document operation=classify_type to confirm it is a receipt.
5. manage_corpus operation=register and attach_ocr_result to index it.

## 32. End-to-End Scenario: Document Library Ingest

1. Collect scans or PDFs in a directory.
2. manage_workflow operation=process_batch_intelligent over the directory.
3. For PDFs, ensure workflow_type=pdf_processing.
4. manage_workflow operation=optimize_processing to refine.
5. manage_corpus operation=register each result with metadata.

## 33. End-to-End Scenario: Multi-Backend Benchmark

1. Pick a representative document.
2. process_document operation=compare_backends with source_path and a set of backends.
3. Read the per-backend accuracy/latency table.
4. Choose the best backend for the batch and pass it explicitly.

## 34. End-to-End Scenario: Book to EPUB

1. Scan or collect the page images.
2. ingest_book operation=full_pipeline with image_paths and backend=unlimited-ocr.
3. The server detects chapters, extracts metadata, OCRs, and assembles the EPUB.
4. Review the EPUB and metadata.

## 35. Prompts That Work Well

- "OCR this image and return the text."
- "Extract the tables from this scanned document."
- "Find the form fields and checkboxes."
- "Scan a page from the flatbed and OCR it."
- "Turn this folder of scans into a searchable corpus."
- "Convert this PDF to searchable PDF/A."
- "Benchmark OCR backends on this sample."
- "Ingest these book scans into an EPUB."

## 36. Performance and Resource Management

- Heavy VLMs download models on first use; warm them up or use manage_models to free GPU
  memory when done.
- Batch operations honor OCR_MAX_CONCURRENT (default 4). Use the batch tools rather than
  firing unbounded parallel calls.
- Use a light backend for bulk print OCR and reserve VLMs for hard documents.
- PDF pages should be rasterized at 150-300 DPI for a good speed/accuracy balance.
- If memory is tight, set OCR_MAX_MEMORY and use manage_models to unload idle models.

## 37. The Quality Improvement Loop

When OCR quality is not good enough, follow this loop:

1. process_document operation=analyze_image_quality on the source to see if blur, noise, or
   low DPI is the cause.
2. manage_image operation=preprocess to deskew, denoise, grayscale, threshold, and autocrop.
3. process_document again on the preprocessed image with a heavier backend if needed.
4. process_document operation=assess_quality on the result to get a score.
5. If you have ground truth, operation=validate_accuracy to get CER/WER.
6. Repeat until the score passes your threshold.

This loop is the core of getting dependable results from poor scans.

## 38. Working with Mixed-Language Documents

- Pass the language hint to process_document. Per-backend defaults: tesseract eng, easyocr
  en.
- paddleocr-vl supports many languages (109); use it for non-English text.
- For a document in several languages, OCR with a multilingual backend (paddleocr-vl) and
  review the output.

## 39. Working with Handwriting

- Route handwriting to easyocr (which uses a CRAFT detector), as the optimizer does.
- Preprocess to enhance contrast before OCR.
- Expect lower confidence; review manually or use validate_accuracy.

## 40. Working with Math and Formulas

- Route math-heavy documents to olmocr-2.
- Use the layout analysis to separate text from equations.
- Review the math output carefully; formula fidelity varies.

## 41. Working with Scanned Forms

- process_document operation=detect_forms returns field and checkbox bounding boxes.
- combine the boxes with analyze_layout for a full picture.
- To produce a fillable document, pass the coordinates to a document-builder server;
  reconstruct_form is not a live operation in this server.

## 42. Corpus Search Tips

- Register documents with meaningful metadata so full-text search returns useful matches.
- Use list_recent to keep track of what was processed.
- Attach OCR results to indexed documents so you can go from a search hit to its text.
- The corpus lives in a SQLite file under OCR_CORPUS_DIR.

## 43. Multi-Page Document Handling

- For PDFs, manage_image operation=pdf_to_images explodes pages at a chosen DPI.
- For books, ingest_book handles the whole flow to EPUB.
- For a set of page images, process_document operation=process_batch or
  manage_workflow operation=process_batch_intelligent.
- Keep page order by processing images in sequence.

## 44. Security Notes

- Local-first sampling: no cloud key is auto-bound; only use OCR_SAMPLING_API_KEY or
  OCR_SAMPLING_USE_OPENAI_KEY deliberately.
- Keep cloud keys out of source control.
- CORS is scoped to localhost, LAN, Tauri, and Tailscale; do not widen it unnecessarily.
- shutdown_server requires confirm=True; do not expose it to untrusted clients.
- Restrict the server to 127.0.0.1 unless you intend network access.

## 45. Advanced: Auto Backend Routing

The optimizer inspects the image to choose a backend. When it cannot decide, it falls back
to a preference order favoring fast engines first (tesseract, pp-ocrv5, got-ocr, dots-ocr,
easyocr, paddleocr-vl, mistral, deepseek-ocr2, unlimited-ocr, mineru-2.5, olmocr-2,
deepseek-ocr, qwen-layered, nemotron-vl). For predictable results on a known document type,
pass an explicit backend rather than relying on auto.

## 46. Getting Help

- get_help(level=basic) for an overview, get_help(level=advanced) for deep documentation
  (intermediate falls back to basic).
- get_status for health and backend availability.
- The server exposes prompts: prompt://ocr/process-instructions,
  quality-assessment-guide, scanner-workflow, batch-processing-guide,
  agentic-workflow-instructions.
- Resources: resource://ocr/logs, /capabilities, /skills.

## 47. More FAQ

- What is the difference between OCR modes? ocr_mode selects how a backend runs, from plain
  OCR to vision-language understanding.
- Can I force a backend? Yes, pass backend explicitly to process_document.
- How do I know which backends are installed? list_backends or get_status.
- What if a model is missing? Run uv run ocr-mcp-install-models or set OCR_AUTO_INSTALL_DEPS.
- Can I OCR from a URL? Provide a local path; download remote files first.
- Does it work offline? The local backends and corpus do; cloud backends and sampling need
  network.
- What formats does it read? Images (png, jpg, tiff, webp) and PDFs (via pdf_to_images).

## 48. REST and HTTP Worked Example

The HTTP mode exposes the MCP endpoint at /mcp on the backend port (10859). Using the HTTP
Streamable transport, a client connects to http://127.0.0.1:10859/mcp and calls the same
tools over JSON-RPC. The webapp on 10858 provides a browser front end with upload, OCR, and
result browsing. For scripting, the MCP HTTP transport is the integration surface; there is
no separate hand-written REST API beyond the FastAPI app that also hosts /mcp.

## 49. Example: Building a Reusable Pipeline

1. Decide the steps, e.g. deskew_image, process_document, assess_ocr_quality.
2. Call manage_workflow operation=create_processing_pipeline with those steps.
3. Call operation=execute_pipeline with the pipeline id to run it on a source.
4. Review the threaded outputs; adjust the steps and re-run.

The allow-list of valid steps is deskew_image, enhance_image, rotate_image, crop_image,
process_document, assess_ocr_quality, convert_image_format, analyze_document_layout, and
extract_table_data.

## 50. Example: Watch-Folder Auto-OCR

1. Set OCR_WATCH_FOLDER_ENABLED=true, OCR_WATCH_FOLDER_PATH, OCR_WATCH_FOLDER_OUTPUT, and
   OCR_WATCH_FOLDER_INTERVAL.
2. Start the server; it monitors the folder.
3. Drop images or PDFs in; the server OCRs them and writes results.
4. This is ideal for a scan-to-text pipeline on a Windows machine.

## 51. Example: Benchmark and Lock a Backend

1. process_document operation=compare_backends on a representative sample.
2. Read accuracy/latency per backend.
3. Set OCR_DEFAULT_BACKEND or pass the chosen backend explicitly to batch runs.
4. Re-run compare_backends when you change document types.

## 52. Environment Setups

- GPU workstation: OCR_DEVICE=cuda, install CUDA torch, use paddleocr-vl/olmocr-2/
  unlimited-ocr.
- CPU-only laptop: OCR_DEVICE=cpu, stick to tesseract/pp-ocrv5/easyocr.
- No local GPU, want heavy OCR: use a cloud backend (mistral-ocr with a key).
- Fully offline: local backends + Ollama sampling at 127.0.0.1:11434.
- Windows scanner: run the WIA bridge (OCR_SCANNER_BRIDGE_URL) and use operate_scanner.

## 53. Troubleshooting Expansion

- torch import error: the heavy VLMs need CUDA torch; install the matching wheel or fall back
  to CPU backends.
- "Backend unavailable" for mistral: set MISTRAL_API_KEY and MISTRAL_BASE_URL.
- Slow first call: the model is downloading; use ocr-mcp-install-models to pre-download.
- pdf_to_images error: set POPPLER_PATH to the pdftoppm directory.
- Scanner bridge unreachable: confirm the bridge container is running on the port.
- Corpus DB locked: close other writers; SQLite is single-writer.
- Sampling loop hangs: reduce max_iterations and narrow the tool whitelist.

## 54. Operation Quick Reference

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

## 55. Getting Started in Ten Calls

1. get_status - confirm health and backends.
2. manage_workflow operation=list_backends - see what is available.
3. process_document operation=process_document on a sample image.
4. process_document operation=analyze_image_quality on the same source.
5. manage_image operation=preprocess and re-OCR.
6. process_document operation=analyze_layout.
7. process_document operation=assess_quality.
8. manage_corpus operation=register and search.
9. manage_workflow operation=create_processing_pipeline and execute_pipeline.
10. get_help level=advanced.

This gives you the feel of the surface and confirms end-to-end function.

## 56. Glossary

- CER/WER: character/word error rate for accuracy validation.
- VLM: vision-language model, the heavy backends that understand document structure.
- ADF: automatic document feeder for batch scanning.
- WIA: Windows Image Acquisition, the scanner API.
- PDF/A: an archival PDF variant produced by embed_text.
- Corpus: the SQLite index of processed documents.
- Pipeline: an ordered allow-listed set of processing steps.

## 57. Extended Scenario: Invoice Triage

1. process_document operation=process_batch over an invoice folder.
2. For each, process_document operation=classify_type to confirm invoice.
3. process_document operation=extract_metadata for dates, vendor, and totals.
4. process_document operation=assess_quality to flag low-confidence scans.
5. manage_corpus operation=register each with metadata, and operation=search to retrieve.

## 58. Extended Scenario: Health and Maintenance

- Use get_status and manage_workflow operation=ocr_health_check regularly.
- manage_workflow operation=list_backends to know availability.
- manage_models to unload idle heavy models when GPU memory is tight.
- For heavy use, set OCR_MAX_CONCURRENT to a sane value and prefer batch tools.
- Set up a watch folder for unattended OCR of incoming scans.

## 59. Integration with the Fleet

OCR results can feed the rest of the fleet. Register recognized text into the corpus for
retrieval, hand extracted metadata to other servers, and use the webapp for a visual review.
The server supports MCP_BRIDGE_URLS for federated MCP servers, letting it route work to and
from other tools. For form reconstruction, pass detected field coordinates to a
document-builder server to produce a fillable document.

## 60. Final Notes

OCR-MCP is a document-understanding control plane: many backends, one interface, automatic
routing, and hardware scanning. Use the quality loop to get dependable results, choose
backends deliberately for hard document types, and lean on the corpus for retrieval. When in
doubt, call get_help or get_status to orient before acting. Prefer explicit backends and
preprocessing for documents you process repeatedly, and benchmark with compare_backends to
lock in the best engine for each recurring workflow. Keep the server healthy with
ocr_health_check and manage models with manage_models when GPU memory is a constraint. For
batch work, prefer the batch and pipeline tools and honor OCR_MAX_CONCURRENT for smooth
operation.
