# OCR Expert Skill

You are connected to OCR-MCP, a FastMCP 3.4+ server with 14 OCR backends. This skill teaches you how to use it effectively.

## Available Backends (14)

| Backend | Params | VRAM | License | Best For |
|---------|--------|------|---------|----------|
| unlimited-ocr | 3B | ~6GB | MIT | Long docs, unbounded parsing |
| paddleocr-vl | 0.9B | 3.3GB | Apache | General docs, tables, 109 langs |
| mineru-2.5 | 1.2B | ~4GB | Apache | Academic/technical docs |
| nemotron-vl | 8B | ~16GB | NV Open | Invoices, forms, charts (EN only) |
| deepseek-ocr2 | 3B | ~8GB | MIT | Structured markdown extraction |
| olmocr-2 | 7B | ~16GB | Apache | Academic PDFs, math |
| mistral-ocr | API | 0 | Cloud | High accuracy cloud OCR |
| got-ocr | 580M | ~2GB | Apache | Fast, lean VRAM |
| tesseract | CPU | 0 | Apache | CPU fallback, always available |

Default backend: `unlimited-ocr`. Auto-selection falls back through the chain.

## Core Workflows

### Single document OCR
```
process_document(operation="process_document", image_path="doc.png", backend="unlimited-ocr")
```

### Scan then OCR
```
operate_scanner(operation="scan_document", device_id="...", dpi=300)
process_document(operation="process_document", image_path="<result.path>", backend="unlimited-ocr")
```

### Table extraction
```
process_document(operation="extract_tables", image_path="table.png", backend="paddleocr-vl")
```

## Key Configuration

- `OCR_DEVICE`: `cuda` (default if GPU), `cpu`
- `OCR_CACHE_DIR`: model download cache
- `MISTRAL_API_KEY`: required for mistral-ocr backend
- `OCR_SAMPLING_USE_CLIENT_LLM=1`: use host IDE's LLM instead of local Ollama

## Agentic Workflow

For multi-step tasks, use `execute_agentic_workflow` with a natural language goal.
The agent will autonomously call tools in sequence.
