---
name: ocr-mcp
description: OCR server with 14 backends for text extraction, form detection, layout analysis, and scanner control
---

## Session Context (OCR-MCP)

FastMCP 3.4+ OCR server with 14 backends. Ports: backend 10859, frontend 10858.

**Before starting work:**
1. Check available backends: manage_workflow(operation="list_backends")
2. Check server health: get_status(level="basic")

**At end of work:**
- OCR results are persisted in the job queue for review
