# AI features: sampling and agentic workflows

OCR-MCP uses **FastMCP 3.1** with **sampling** and **SEP-1577** (sampling with tools) so `agentic_document_workflow` can run multi-step document flows with an LLM choosing tools.

## Default: local LLM (Ollama), no API spend

Out of the box the server targets **Ollama’s OpenAI-compatible API**:

- **`OCR_SAMPLING_BASE_URL`** — default `http://127.0.0.1:11434/v1`
- **`OCR_SAMPLING_MODEL`** — default `llama3.2` (run `ollama pull llama3.2` or set another tag)
- **No API key** on `localhost` or **RFC1918 LAN** (e.g. `192.168.x.x`) so a 4090 box can run everything locally.

Start Ollama, pull a model, then use **`agentic_document_workflow`** — sampling hits your GPU, not a cloud bill.

## MCP host LLM (e.g. Cursor) instead

If you want the **client** to supply the LLM when it supports sampling + tools:

- Set **`OCR_SAMPLING_USE_CLIENT_LLM=1`** on the server process.  
  That sets `sampling_handler_behavior=fallback` so a capable host runs sampling; otherwise the server keeps **`always`** and uses the HTTP endpoint above.

## Cloud OpenAI-compatible (optional)

- **`OCR_SAMPLING_API_KEY`** — explicit key for the sampling HTTP client, or  
- **`OCR_SAMPLING_USE_OPENAI_KEY=1`** — also use **`OPENAI_API_KEY`** (off by default so a stray OpenAI key does not silently send sampling to the cloud).
- Set **`OCR_SAMPLING_BASE_URL`** to your provider’s `/v1` base (e.g. `https://api.openai.com/v1`).

## What you get

- **Single prompt → workflow** with tool use (scan → OCR → summarize, etc.).
- **Prompts:** `quality-assessment-guide`, `scanner-workflow`, `batch-processing-guide`, `agentic-workflow-instructions`, `process-instructions`.

**See also:** [TECHNICAL.md](TECHNICAL.md), in-app **Help** at `/help` in `web_sota` ([source](../web_sota/src/pages/help.tsx)).

## SEP-1577 (`agentic_document_workflow`)

- **Sampling with tools** — local Ollama by default, or host LLM if `OCR_SAMPLING_USE_CLIENT_LLM=1`.
- **Fewer round-trips** — one high-level prompt instead of many manual tool calls.

## Implementation note

[adn-notes/SEP-1577-in-OCR-MCP-Agentic-Document-Processing.md](adn-notes/SEP-1577-in-OCR-MCP-Agentic-Document-Processing.md)
