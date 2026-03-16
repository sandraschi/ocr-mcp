# OCR-MCP Justfile – justfiles standard (https://github.com/casey/just)
# Run with: just <recipe> or just --list

default:
    just --list

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
lint:
    uv run ruff check .
    uv run ruff format --check .

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
