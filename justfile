set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]
import 'scripts/just/fleet.just'

# --- Dashboard ---

# Open the interactive recipe dashboard in the browser
default:
    @just --list


# Synchronize deps, pre-commit hooks, and web frontend
bootstrap:
    uv sync --extra dev --group dev
    uv run pre-commit install
    Set-Location web_sota; npm ci; if ($LASTEXITCODE -ne 0) { npm install }
    Write-Host "Pre-commit hooks installed." -ForegroundColor Green
# --- Quality ---

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'; uv run ruff check .; Set-Location '{{justfile_directory()}}\web_sota'; npx @biomejs/biome ci .

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'; uv run ruff check . --fix --unsafe-fixes; uv run ruff format .; Set-Location '{{justfile_directory()}}\web_sota'; npx @biomejs/biome check --write .

# --- Hardening ---

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check

# OCR-MCP Justfile - justfiles standard (https://github.com/casey/just)
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
serve: run
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

# Pack .mcpb bundle via the fleet shim (wipe+recopy src -> mcpb/src, checks, release assets).
# Never bare `mcpb pack` (stale-bundle class). Shim: scripts/mcpb-pack.ps1.
pack:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File '{{justfile_directory()}}\scripts\mcpb-pack.ps1'

# Alias: canonical fleet recipe name per PACKAGING_STANDARDS
mcpb-pack:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File '{{justfile_directory()}}\scripts\mcpb-pack.ps1'

# Format Python + check formatting (canonical `fmt` recipe name)
fmt:
    uv run ruff format src/ backend/ run_server.py

# All quality gates: ruff lint + format check + pyright types + unit tests
gates-green:
    uv run ruff check src/ backend/ run_server.py
    uv run ruff format src/ backend/ run_server.py --check
    uv run --with pyright pyright src/
    uv run pytest tests/unit -q --no-cov -p no:cacheprovider

# Install OCR models (optional, large download)
install-models:
    uv run ocr-mcp-install-models

# One-time dev setup (pre-commit, env)
setup-dev:
    uv run ocr-mcp-setup-dev

# Pre-commit run on all files
check:
    uv run pre-commit run --all-files

# Bootstrap: install dev deps + pre-commit hook
