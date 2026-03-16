# Justfile (just) – Technical reference

OCR-MCP uses a [justfile](https://github.com/casey/just) at repo root. If you have **just** installed, the fastest install and run is:

```powershell
just install
just run
```

**Prerequisites:** [just](https://github.com/casey/just) and [uv](https://docs.astral.sh/uv/) (with Python 3.12+). On Windows you can install just via `winget install just` or from GitHub releases.

---

## Recipes

List all recipes: `just` or `just --list`.

| Recipe | What it does |
|--------|----------------|
| **install** | `uv sync` — install project dependencies. Fastest install path when you have just. |
| **run** | `uv run ocr-mcp` — run the MCP server (stdio). |
| **server** | Alias for `run`. |
| **test** | `uv run pytest` — run the test suite. |
| **lint** | `ruff check .` and `ruff format --check` — lint and format-check only (no fixes). |
| **format** | `ruff format .` and `ruff check --fix` — format and fix lint. |
| **webapp** | Start the web UI: runs `web_sota/start.ps1` (backend + Vite; ports 10858/10859). |
| **pack** | `mcpb pack . dist/ocr-mcp.mcpb` — build .mcpb bundle (requires `mcpb` installed). |
| **install-models** | `uv run ocr-mcp-install-models` — optional, large download of OCR models. |
| **setup-dev** | `uv run ocr-mcp-setup-dev` — one-time dev setup (pre-commit, env). |
| **check** | `uv run pre-commit run --all-files` — run pre-commit on all files. |

---

## Conventions

- All commands assume you are in the **repo root**.
- The justfile follows the [justfiles standard](https://github.com/casey/just); no custom syntax.
- **install** does not install system tools (just, uv, Python); those are prerequisites.
