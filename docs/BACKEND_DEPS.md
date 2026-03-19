# Web backend dependencies

The FastAPI app lives in **`backend/app.py`**. It is **not** a separate Python package: it uses the same virtual environment as **`ocr-mcp`** from the repo root.

## How to install

From the **ocr-mcp repository root**:

```powershell
uv sync
```

Start the API with **`PYTHONPATH` set to the repo root** (so `backend.app` and `ocr_mcp` import correctly). `web_sota/start.ps1` does this automatically:

```powershell
$env:PYTHONPATH = (Get-Location).Path   # repo root
uv run uvicorn backend.app:app --host 127.0.0.1 --port 10859
```

## Where dependencies are declared

| Source | What it covers |
|--------|----------------|
| **`pyproject.toml`** → `[project] dependencies` | FastAPI, Uvicorn, Pillow, OpenCV, PDF libs, **transformers**, **accelerate**, **huggingface-hub**, **pyyaml**, EasyOCR, Tesseract wrapper, structlog, watchfiles, Windows scanner (**pywin32**, **comtypes**), etc. |
| **`pyproject.toml`** → `[project.optional-dependencies]` | **`dev`** — pytest, ruff, coverage, … · **`webapp`** / **`scanner`** / **`ml`** — optional groupings if you want a slimmer install (defaults already include most web + OCR stack) |
| **Not in `pyproject.toml`** | **`torch` (PyTorch)** — install yourself for CPU/GPU (`pip install torch` or [pytorch.org](https://pytorch.org)). Required for Hugging Face–based backends (PaddleOCR-VL, DeepSeek, GOT-OCR, …). |
| **[OCR_BACKEND_REQUIREMENTS.md](OCR_BACKEND_REQUIREMENTS.md)** | Per-engine extras (flash-attn, PaddlePaddle, API keys, Tesseract binary, …). |

## Runtime behaviour (bootstrap)

After **`OCRConfig()`**, **`run_ocr_startup_bootstrap`** (`ocr_mcp.utils.startup_bootstrap`) runs from **`backend/app.py`** and the **MCP server**:

- **PyYAML** dist-info / `yaml.dump` repair (`pyyaml_health`, `ensure_pyyaml_init.py` for wheels missing `__init__.py`). See [INSTALL.md](INSTALL.md).
- **Windows:** Tesseract + Poppler silent installs when configured.
- **`OCR_AUTO_INSTALL_DEPS=1`** — **`ocr_mcp.utils.ocr_pip_install.ensure_ocr_pip_dependencies`** may **`pip`/`uv` install** the ML stack and optional Paddle, then **restart** the process. **Off by default.**

## Checklist for a working OCR backend

1. `uv sync` from repo root  
2. Install **PyTorch** if you use local ML backends  
3. Run **`scripts/ensure_pyyaml_init.py`** after `uv sync` if you hit `yaml` has no attribute `dump` (or use `web_sota/start.ps1`)  
4. See [OCR_BACKEND_REQUIREMENTS.md](OCR_BACKEND_REQUIREMENTS.md) for engine-specific packages  

## Frontend

The React app in **`web_sota/`** uses **Node** (`npm install` / `npm run dev`). It does not share Python deps; it proxies **`/api`** and **`/static`** to the backend on **10859** (see **`web_sota/vite.config.ts`**).

- **Help** — in-app **`/help`** (`web_sota/src/pages/help.tsx`): webapp vs MCP vs OCR backends; keep aligned with **[INSTALL.md](INSTALL.md)** and **[TECHNICAL.md](TECHNICAL.md)**.
- **Settings** — Mistral key/base URL and test flow hit **`backend/app.py`** (`/api/settings/mistral`, `/api/settings/mistral/test`); default backend preference is stored in the browser only.
