# ocr-mcp — Claude Code Guide

## Overview
FastMCP server providing comprehensive OCR capabilities to the MCP ecosystem

## Entry Points
- `uv run ocr-mcp` → `ocr_mcp.server:main`
- `uv run ocr-mcp-webapp` → `ocr_mcp.webapp_runner:main`
- `uv run ocr-mcp-test` → `scripts.run_tests:main`
- `uv run ocr-mcp-install-models` → `scripts.install_models:main`
- `uv run ocr-mcp-setup-dev` → `scripts.setup_dev_env:main`

## Standards
- FastMCP 3.2+ portmanteau tool pattern — tools use `operation` enum param
- Responses: structured dicts with `success`, `message`, domain-specific fields
- Dual transport: stdio (Claude Desktop) + HTTP (`MCP_TRANSPORT=http`)
- See [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs) for fleet-wide coding standards

## Key Files
- `README.md` — full documentation
- `pyproject.toml` — build config and entry points
- `AGENTS.md` — OpenAI Codex agent context (if present)
