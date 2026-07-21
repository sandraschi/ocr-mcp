# OCR-MCP

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>

**Complete AI OCR webapp and MCP server.** A **web app** with a streamlined dashboard (drag-and-drop or scanner, pick an engine, click one button) and a **FastMCP 3.1 MCP server** for agentic IDEsClaude, Cursor, Windsurfso agents can run OCR, preprocessing, and workflows as tools. Same 14 engines, WIA scanner (Windows), and pipelines; one repo.

**Topics:** `ocr`, `mcp`, `fastmcp`, `document-processing`, `scanner`, `wia`, `pdf`, `computer-vision`, `model-context-protocol`, `llm`

[![Version](https://img.shields.io/badge/Version-0.2.0--alpha-blue)](https://github.com/sandraschi/ocr-mcp/releases)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.1-0066CC)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![OCR Engines](https://img.shields.io/badge/OCR%20Engines-14-orange)](docs/OCR_MODELS.md)
[![Scanner](https://img.shields.io/badge/Scanner-WIA%20%28Windows%29-0078D4?logo=windows)](docs/INSTALL.md)
[![Web UI](https://img.shields.io/badge/Web%20UI-React-61DAFB?logo=react&logoColor=black)](docs/INSTALL.md)
[![Status](https://img.shields.io/badge/Status-Alpha-green)](OCR-MCP_MASTER_PLAN.md)

## What it does

- **Web app**  React (`web_sota/`) + FastAPI (`backend/app.py`): upload or scan, pick engine, get text/PDF/JSON. Ports **10858** (Vite) and **10859** (API). In-app **Help** (`/help`) documents the web UI, the MCP server, and OCR backends.
- **MCP server**  FastMCP 3.1 stdio: tools for OCR, preprocessing, scanner, workflows. **Sampling defaults to local [Ollama](https://ollama.com)** (`http://127.0.0.1:11434/v1`, model `llama3.2`)  no cloud API key. Set **`OCR_SAMPLING_USE_CLIENT_LLM=1`** to use the host IDEs LLM instead. Mistral OCR uses **`MISTRAL_API_KEY`** when you call that backend. See [AI_FEATURES.md](docs/AI_FEATURES.md).

**Features:** 14 backends (Unlimited-OCR, PaddleOCR-VL-1.5, Nemotron VL 8B, DeepSeek-OCR-2, MinerU2.5-Pro, Mistral OCR)  Auto backend selection  Preprocessing (deskew, enhance, crop)  Layout & table extraction  Quality assessment  WIA scanner  **Auto-Scan watcher** (detect documents on flatbed, auto-OCR)  Batch & pipelines  Multi-format export

## Docs

| Doc | Description |
|-----|-------------|
| [**Install**](docs/INSTALL.md) | Install, run MCP, Web UI (`start.ps1`, ports 10858/10859), PyYAML notes, client config |
| [**Backend deps**](docs/BACKEND_DEPS.md) | Web FastAPI backend: same venv as `ocr-mcp`, `pyproject.toml`, PyTorch, `OCR_AUTO_INSTALL_DEPS` |
| [**Technical**](docs/TECHNICAL.md) | Architecture, tools, config, development, packaging |
| [**OCR models**](docs/OCR_MODELS.md) | Engines, capabilities, hardware (see also [AI_MODELS.md](AI_MODELS.md)) |
| [**Backend requirements**](docs/OCR_BACKEND_REQUIREMENTS.md) | Per-model pip packages, system deps, env/config |
| [**MCP toolset matrix**](docs/MCP_TOOLSET_MATRIX.md) | Portmanteau tools, operation status, corpus v0 |
| [**AI features**](docs/AI_FEATURES.md) | Sampling, SEP-1577, agentic workflows, prompts |
| [**Webapp redesign**](docs/WEBAPP_REDESIGN.md) | July 2026 redesign: dashboard-first workflow, removed legacy frontend, 5-page sidebar |
| [**Book scanning**](docs/BOOK_SCANNING.md) | Home book scanning guide: V-cradle, CZUR, auto-scan integration |
| [**Book pipeline**](docs/BOOK_SCANNING_PIPELINE.md) | Spine-to-EPUB pipeline plan: cut, scan, OCR, chapter detect, EPUB, Calibre |
| [**In-app Help**](web_sota/src/pages/help.tsx) | Source for `/help`: webapp vs MCP vs backends (mirrors INSTALL / TECHNICAL) |
| [**SOTA Compliance**](../mcp-central-docs/standards/AGENT_PROTOCOLS.md) |  Verified SOTA v12.0 Architecture |

Also: [JUSTFILE.md](docs/JUSTFILE.md) (just recipes)  [OCR-MCP_MASTER_PLAN.md](OCR-MCP_MASTER_PLAN.md) (roadmap)  [tests/README.md](tests/README.md) (testing)

## Quick Start

```powershell
git clone https://github.com/sandraschi/ocr-mcp
cd ocr-mcp
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

### Manual Setup

If you don't have `just` installed:

## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 14.1** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting. Strict `noConsoleLog` enforcement.
- **Protocol Compliance**: Hardened `stdout/stderr` isolation to ensure crash-resistant JSON-RPC communication.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations (`just lint`, `just fix`, `just dev`).
- **Security**: Automated audits via `bandit` and `safety`.

## License

MIT  see [LICENSE](LICENSE).
