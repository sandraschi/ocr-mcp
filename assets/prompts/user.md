# OCR-MCP User Guide

## Quick Start

```python
# OCR a document with auto-selected backend
result = await process_document(
    operation="process_document",
    image_path="invoice.jpg",
    backend="auto"
)
print(result["text"])

# Using Unlimited-OCR specifically
result = await process_document(
    operation="process_document",
    image_path="document.png",
    backend="unlimited-ocr"
)
```

## Scanner Workflow

```python
# List available scanners
scanners = await operate_scanner(operation="list_scanners")

# Scan a document
scan = await operate_scanner(
    operation="scan_document",
    device_id=scanners["scanners"][0]["device_id"],
    dpi=300
)

# OCR the scanned image
result = await process_document(
    operation="process_document",
    image_path=scan["image_path"],
    backend="unlimited-ocr"
)
```

## Batch Processing

```python
# Process multiple documents
batch = await manage_workflow(
    operation="process_batch_intelligent",
    image_paths=["doc1.png", "doc2.png", "doc3.png"],
    backend="auto"
)
```

## Table Extraction

```python
result = await process_document(
    operation="extract_tables",
    image_path="spreadsheet.png",
    backend="paddleocr-vl"
)
```

## Configuration

Set environment variables:
- `OCR_CACHE_DIR`: Model cache location (default: ~/.cache/ocr-mcp)
- `OCR_DEVICE`: `cuda`, `cpu`, or `auto`
- `MISTRAL_API_KEY`: Required for mistral-ocr backend
- `TESSERACT_CMD`: Path to tesseract.exe if not on PATH
- `OCR_DEFAULT_BACKEND`: Override default backend
