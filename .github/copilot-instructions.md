## Session Context (OCR-MCP)

You have access to a FastMCP 3.4+ OCR server with 14 backends for document text extraction.

**Before starting work:**
1. Check registered backends: manage_workflow(operation="list_backends")
2. Check server health: get_status(level="basic")

**At end of work:**
- OCR results are persisted in the job queue for review
