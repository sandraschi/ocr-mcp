# Installation

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/) (recommended). GPU optional for SOTA models.

**Fastest path (if you have [just](https://github.com/casey/just)):** clone repo, then `just install` and `just run`. See [JUSTFILE.md](JUSTFILE.md) for all recipes.

## From repo (recommended)

```powershell
# Clone (or open repo)
cd D:\Dev\repos\ocr-mcp

# Install deps (or: just install)
uv sync

# For local ML OCR in the web API, install PyTorch separately (not pinned in pyproject)
# uv pip install torch --index-url https://download.pytorch.org/whl/cu124   # example CUDA
# uv pip install torch   # CPU example

# Run MCP server (stdio)
just run
# or: uv run ocr-mcp
```

**Web backend vs MCP:** Both use the **same** Python environment and **`pyproject.toml`**. See **[BACKEND_DEPS.md](BACKEND_DEPS.md)** for what is declared, what is optional, and `OCR_AUTO_INSTALL_DEPS`.

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

Replace `D:/Dev/repos/ocr-mcp` with your repo path. Optional env: `OCR_CACHE_DIR`, `OCR_DEVICE` (cuda/cpu/auto). For **mistral-ocr** from the MCP server, add **`MISTRAL_API_KEY`** (and optionally **`MISTRAL_BASE_URL`**) under `env` — the web UI Settings page does not inject keys into the stdio MCP process.

## Web UI

React + FastAPI app in `web_sota/`. **Frontend: port 10858. Backend: port 10859.**

### Recommended: `web_sota\start.ps1` (Windows PowerShell)

From the **ocr-mcp repo root**, run:

```powershell
.\web_sota\start.ps1
```

The script:

1. Stops processes listening on **10858** and **10859**
2. Runs `uv pip uninstall yaml` (removes the PyPI **stub** package named `yaml` if present; it shadows **PyYAML**)
3. Runs `uv sync`
4. Runs `scripts\ensure_pyyaml_init.py` if present (restores `yaml/__init__.py` when a broken PyYAML wheel omits it)
5. Verifies `import yaml` exposes `dump` (PaddleOCR-VL / Hugging Face need it)
6. Starts **backend** in a new PowerShell window: `uv run uvicorn backend.app:app --host 127.0.0.1 --port 10859` with `PYTHONPATH` set to the repo root
7. After a short delay, starts **Vite** in another window (`npm run dev` on 10858)
8. Opens **http://localhost:10858** in the default browser

**Manual alternative:** from repo root set `PYTHONPATH` to the repo path, run `uv run uvicorn backend.app:app --host 127.0.0.1 --port 10859`. In `web_sota/`, run `npm install` once, then `npm run dev -- --port 10858 --host`. Vite proxies `/api` to `http://127.0.0.1:10859`.

**If `just webapp` exists** in your justfile, it may mirror the same steps.

### PyYAML / `yaml.dump` errors (PaddleOCR-VL)

If you see **`module 'yaml' has no attribute 'dump'`**:

- Ensure you use **PyYAML** (`pyyaml` on pip), not the stub PyPI package **`yaml`**. From repo root: `uv pip uninstall yaml` then `uv sync`.
- Run `uv run python scripts\ensure_pyyaml_init.py` (copies a known-good `yaml/__init__.py` into the venv when the wheel is incomplete).
- Restart the backend after fixing the environment.

The backend also runs a small **startup** check that tries to repair PyYAML in the current interpreter (see `backend/app.py`).

### Optional: auto-install pip deps on backend start

By default the backend does **not** auto-install missing pip packages. To enable (not recommended unless you know the risks): set **`OCR_AUTO_INSTALL_DEPS=1`** before starting uvicorn.

### Web interface

- **URL**: `http://127.0.0.1:10858` (or `localhost`)
- **Help**: **`/help`** — overview of the **web app** (routes, ports, proxy), **MCP server** (stdio, tools, env), and **OCR backends** (comparison + doc links)
- **Dashboard** — overview and shortcuts
- **Import** — upload files; OCR runs in the background
- **Scanner** — WIA hardware (Windows)
- **Process** — quality-focused pipelines
- **Editor** — OCR text for the latest job loads automatically; export JSON/CSV/XML; job IDs optional (advanced / **Status**)
- **Status** — activity / job debugging
- **Settings** — default OCR backend (browser **localStorage**); **Mistral** API key + base URL + **Test API key** (stored only in the **backend process**); backend and scanner lists; **`POST /api/settings/mistral/test`** validates the key via Mistral **`GET {base}/models`**

## API (when backend is running)

- **OpenAPI / Swagger**: http://127.0.0.1:10859/docs
- **Health**: http://127.0.0.1:10859/api/health
- **Mistral (web session)**:
  - `GET /api/settings/mistral` — key configured flag, base URL, last-4 hint (never full key)
  - `POST /api/settings/mistral` — JSON `{ "api_key"?, "base_url"? }` — updates in-process `OCRConfig`, invalidates **mistral-ocr** backend
  - `POST /api/settings/mistral/test` — JSON `{ "api_key"?, "base_url"? }` — optional overrides; uses saved key if `api_key` omitted; calls Mistral **`GET …/models`**; returns `{ valid, message, http_status? }`

## Tests and lint

```powershell
uv sync --extra dev
uv run python -m pytest
# or: python scripts/run_tests.py --suite quick
uv run ruff check src backend tests scripts
uv run ruff format src backend tests scripts
```

See [tests/README.md](../tests/README.md) for suites (`smoke`, `unit`, `integration`, etc.).
