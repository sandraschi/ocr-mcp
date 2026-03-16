# AI features: sampling and agentic workflows

OCR-MCP uses **FastMCP 3.1** with **sampling** and **SEP-1577** (sampling with tools) so the server can use the client’s LLM to run multi-step document workflows without extra round-trips.

## What you get

- **Single prompt → full workflow.** e.g. *“Process all invoices this month”* or *“Scan and analyze the document, then show me a formatted analysis.”*
- **Agentic tool use.** The server calls list_scanner → scan → OCR (chosen backend) → layout/analysis → formatting in one go.
- **Prompts for the LLM:** `quality-assessment-guide`, `scanner-workflow`, `batch-processing-guide`, `agentic-workflow-instructions`, plus `process-instructions`.

## SEP-1577 (agentic document workflow)

The **`agentic_document_workflow`** tool takes a natural-language workflow prompt and runs it autonomously:

- **Sampling with tools** — server borrows the client’s LLM to decide tool order and logic
- **Fewer round-trips** — one prompt instead of many tool calls
- **Error recovery** — validation and retries inside the workflow
- **Batch-friendly** — multiple documents in one workflow

Example prompts the LLM can orchestrate:

1. **Invoice batch** — find invoices → OCR → extract tables → validate → export JSON/CSV  
2. **Digitization** — discover files → preprocess → OCR → layout analysis → searchable PDFs  
3. **Forms** — identify forms → OCR → structured fields → validation → export  

## Technical detail

- **FastMCP 3.1** with sampling handler and `context.sample_step` for tool execution
- **Implementation:** [adn-notes/SEP-1577-in-OCR-MCP-Agentic-Document-Processing.md](adn-notes/SEP-1577-in-OCR-MCP-Agentic-Document-Processing.md)
