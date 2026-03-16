# Installation

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/) (recommended). GPU optional for SOTA models.

**Fastest path (if you have [just](https://github.com/casey/just)):** clone repo, then `just install` and `just run`. See [JUSTFILE.md](JUSTFILE.md) for all recipes.

## From repo (recommended)

```powershell
# Clone (or open repo)
cd D:\Dev\repos\ocr-mcp

# Install deps (or: just install)
uv sync

# Run MCP server (stdio)
just run
# or: uv run ocr-mcp
```

## One-liner (no clone)

```powershell
uvx ocr-mcp
```
Requires [ocr-mcp on PyPI](https://pypi.org/project/ocr-mcp/) or `uvx --from . ocr-mcp` from repo root.

## Claude Desktop / MCP clients

Add to `claude_desktop_config.json` (or your client's MCP config):

**With uv (from repo):**
```json
"mcpServers": {
  "ocr-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/ocr-mcp", "run", "ocr-mcp"]
  }
}
```

**With Python (after `uv sync` or `pip install -e .`):**
```json
"ocr-mcp": {
  "command": "python",
  "args": ["-m", "ocr_mcp.server"],
  "env": {
    "OCR_CACHE_DIR": "C:/path/to/cache",
    "OCR_DEVICE": "cuda"
  }
}
```

Replace `D:/Dev/repos/ocr-mcp` with your repo path. Optional env: `OCR_CACHE_DIR`, `OCR_DEVICE` (cuda/cpu/auto).

## Web UI

React + FastAPI app in `web_sota/`. **Frontend: port 10858. Backend: port 10859.**

```powershell
just webapp
```
Opens backend + Vite; then open **http://localhost:10858**. Or from `web_sota/`: `npm install`; start backend (from project root: `uv run uvicorn backend.app:app --port 10859`), then `npm run dev -- --port 10858`.

### Web interface

- **URL**: `http://localhost:10858`
- **Dashboard**: Real-time monitoring of OCR and scanner operations
- **Scanner Control**: Direct hardware acquisition with live preview (WIA 2.0, Windows)
- **Batch Processing**: Parallel document processing with progress tracking

## API (when backend is running)

- **API docs**: http://localhost:10859/docs
- **Health**: http://localhost:10859/api/health
