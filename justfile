set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# ── Dashboard ─────────────────────────────────────────────────────────────────

# Open the interactive recipe dashboard in the browser
default:
    @pwsh.exe -NoProfile -ExecutionPolicy Bypass -File ../mcp-central-docs/scripts/just-dashboard.ps1 -Path .

# ── Quality ───────────────────────────────────────────────────────────────────

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check .
    Set-Location '{{justfile_directory()}}\web_sota'
    npx @biomejs/biome ci .

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .
    Set-Location '{{justfile_directory()}}\web_sota'
    npx @biomejs/biome check --write .

# ── Hardening ─────────────────────────────────────────────────────────────────

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check

# OCR-MCP Justfile – justfiles standard (https://github.com/casey/just)
# Run with: just <recipe> or just --list

# Repo statistics (Markdown, tools, FastMCP, MCP tools)
stats:
    uv run python tools/repo_stats.py

# Install dependencies (uv)
install:
    uv sync

# Run the MCP server (stdio)
run:
    uv run ocr-mcp

# Run MCP server (alias)
server: run

# Run tests
test:
    uv run pytest

# Lint and format-check only
# Format and fix lint
format:
    uv run ruff format .
    uv run ruff check --fix .

# Start web UI (backend + Vite). Windows: uses web_sota/start.ps1
webapp:
    powershell -NoProfile -ExecutionPolicy Bypass -File web_sota/start.ps1

# Pack .mcpb bundle (requires mcpb installed: pip install mcpb)
pack:
    mcpb pack . dist/ocr-mcp.mcpb

# Install OCR models (optional, large download)
install-models:
    uv run ocr-mcp-install-models

# One-time dev setup (pre-commit, env)
setup-dev:
    uv run ocr-mcp-setup-dev

# Pre-commit run on all files
check:
    uv run pre-commit run --all-files
