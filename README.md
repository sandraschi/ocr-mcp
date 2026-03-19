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

- **Web app** — React (`web_sota/`) + FastAPI (`backend/app.py`): upload or scan, pick engine, get text/PDF/JSON. Ports **10858** (Vite) and **10859** (API). In-app **Help** (`/help`) documents the web UI, the MCP server, and OCR backends.
- **MCP server** — FastMCP 3.1 stdio: tools for OCR, preprocessing, scanner, workflows. Sampling and agentic workflow (SEP-1577) supported. Same Python env and engines as the web backend; Mistral key for agents is typically **`MISTRAL_API_KEY`** in the client config (web Settings only affect the FastAPI process).

**Features:** 10+ backends (PaddleOCR-VL-1.5, DeepSeek-OCR-2, Mistral OCR, …) · Auto backend selection · Preprocessing (deskew, enhance, crop) · Layout & table extraction · Quality assessment · WIA scanner · Batch & pipelines · Multi-format export

## Docs

| Doc | Description |
|-----|-------------|
| [**Install**](docs/INSTALL.md) | Install, run MCP, Web UI (`start.ps1`, ports 10858/10859), PyYAML notes, client config |
| [**Backend deps**](docs/BACKEND_DEPS.md) | Web FastAPI backend: same venv as `ocr-mcp`, `pyproject.toml`, PyTorch, `OCR_AUTO_INSTALL_DEPS` |
| [**Technical**](docs/TECHNICAL.md) | Architecture, tools, config, development, packaging |
| [**OCR models**](docs/OCR_MODELS.md) | Engines, capabilities, hardware (see also [AI_MODELS.md](AI_MODELS.md)) |
| [**Backend requirements**](docs/OCR_BACKEND_REQUIREMENTS.md) | Per-model pip packages, system deps, env/config |
| [**AI features**](docs/AI_FEATURES.md) | Sampling, SEP-1577, agentic workflows, prompts |
| [**In-app Help**](web_sota/src/pages/help.tsx) | Source for `/help`: webapp vs MCP vs backends (mirrors INSTALL / TECHNICAL) |
| [**SOTA Compliance**](../mcp-central-docs/standards/AGENT_PROTOCOLS.md) | 🚀 Verified SOTA v12.0 Architecture |

Also: [JUSTFILE.md](docs/JUSTFILE.md) (just recipes) · [OCR-MCP_MASTER_PLAN.md](OCR-MCP_MASTER_PLAN.md) (roadmap) · [tests/README.md](tests/README.md) (testing)

## Quick start

```powershell
uv sync
just run
```

**Web UI (recommended):** from repo root run `web_sota\start.ps1` (PowerShell). It clears ports **10858/10859**, runs `uv sync`, restores PyYAML if needed (see [docs/INSTALL.md](docs/INSTALL.md)), starts the FastAPI backend in a new window, starts Vite in another window, then opens **http://localhost:10858** in your browser.

Or: `just webapp` if your [justfile](docs/JUSTFILE.md) wraps the same flow.

**If the start script fails**, use two terminals from the **ocr-mcp** repo root:

- **Terminal 1 (backend):**  
  `$env:PYTHONPATH = (Get-Location).Path; uv run uvicorn backend.app:app --host 127.0.0.1 --port 10859`
- **Terminal 2 (frontend):**  
  `cd web_sota; npm run dev -- --port 10858 --host`

Then open http://localhost:10858

**Tests:** `uv sync --extra dev` then `uv run python -m pytest` or `python scripts/run_tests.py --suite quick`. See [tests/README.md](tests/README.md).

## License

MIT — see [LICENSE](LICENSE).
