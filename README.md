# OCR-MCP

**Complete AI OCR webapp and MCP server.** A **web app** for people (drag‑and‑drop OCR, scanner, batch) and a **FastMCP 3.1 MCP server** for agentic IDEs—Claude, Cursor, Windsurf—so agents can run OCR, preprocessing, and workflows as tools. Same 10+ engines, WIA scanner (Windows), and pipelines; one repo.

**Topics:** `ocr`, `mcp`, `fastmcp`, `document-processing`, `scanner`, `wia`, `pdf`, `computer-vision`, `model-context-protocol`, `llm`

[![Version](https://img.shields.io/badge/Version-0.2.0--alpha-blue)](https://github.com/sandraschi/ocr-mcp/releases)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.1-0066CC)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![OCR Engines](https://img.shields.io/badge/OCR%20Engines-10%2B-orange)](docs/OCR_MODELS.md)
[![Scanner](https://img.shields.io/badge/Scanner-WIA%20%28Windows%29-0078D4?logo=windows)](docs/INSTALL.md)
[![Web UI](https://img.shields.io/badge/Web%20UI-React-61DAFB?logo=react&logoColor=black)](docs/INSTALL.md)
[![Status](https://img.shields.io/badge/Status-Alpha-green)](OCR-MCP_MASTER_PLAN.md)

## What it does

- **Web app** — React + FastAPI: upload or scan, pick engine, get text/PDF/JSON. Ports **10858** (frontend) and **10859** (backend).
- **MCP server** — Tools for OCR, preprocessing, scanner, workflows. Sampling and agentic workflow (SEP-1577) supported.

**Features:** 10+ backends (PaddleOCR-VL-1.5, DeepSeek-OCR-2, Mistral OCR, …) · Auto backend selection · Preprocessing (deskew, enhance, crop) · Layout & table extraction · Quality assessment · WIA scanner · Batch & pipelines · Multi-format export

## Docs

| Doc | Description |
|-----|-------------|
| [**Install**](docs/INSTALL.md) | Install, run MCP, Web UI (ports 10858/10859), client config |
| [**Technical**](docs/TECHNICAL.md) | Architecture, tools, config, development, packaging |
| [**OCR models**](docs/OCR_MODELS.md) | Engines, capabilities, hardware (see also [AI_MODELS.md](AI_MODELS.md)) |
| [**AI features**](docs/AI_FEATURES.md) | Sampling, SEP-1577, agentic workflows, prompts |

Also: [JUSTFILE.md](docs/JUSTFILE.md) (just recipes) · [OCR-MCP_MASTER_PLAN.md](OCR-MCP_MASTER_PLAN.md) (roadmap) · [tests/README.md](tests/README.md) (testing)

## Quick start

```powershell
uv sync
just run
```

Web UI: `just webapp` → http://localhost:10858

## License

MIT — see [LICENSE](LICENSE).
