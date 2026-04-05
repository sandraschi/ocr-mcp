set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# ── Dashboard ─────────────────────────────────────────────────────────────────

# Display the SOTA Industrial Dashboard
default:
    @powershell -NoLogo -Command " \
        $lines = Get-Content '{{justfile()}}'; \
        Write-Host ' [SOTA] Industrial Operations Dashboard v1.3.1' -ForegroundColor White -BackgroundColor Cyan; \
        Write-Host '' ; \
        $currentCategory = ''; \
        foreach ($line in $lines) { \
            if ($line -match '^# ── ([^─]+) ─') { \
                $currentCategory = $matches[1].Trim(); \
                Write-Host \"`n  $currentCategory\" -ForegroundColor Cyan; \
                Write-Host '  ' + ('─' * 45) -ForegroundColor Gray; \
            } elseif ($line -match '^# ([^─].+)') { \
                $desc = $matches[1].Trim(); \
                $idx = [array]::IndexOf($lines, $line); \
                if ($idx -lt $lines.Count - 1) { \
                    $nextLine = $lines[$idx + 1]; \
                    if ($nextLine -match '^([a-z0-9-]+):') { \
                        $recipe = $matches[1]; \
                        $pad = ' ' * [math]::Max(2, (18 - $recipe.Length)); \
                        Write-Host \"    $recipe\" -ForegroundColor White -NoNewline; \
                        Write-Host \"$pad$desc\" -ForegroundColor Gray; \
                    } \
                } \
            } \
        } \
        Write-Host \"`n  [System State: PROD/HARDENED]\" -ForegroundColor DarkGray; \
        Write-Host ''"

# ── Quality ───────────────────────────────────────────────────────────────────

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check .

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .

# ── Hardening ─────────────────────────────────────────────────────────────────

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check

set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# ── Dashboard ─────────────────────────────────────────────────────────────────

# Display the SOTA Industrial Dashboard
# ── Quality ───────────────────────────────────────────────────────────────────

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check .

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .

# ── Hardening ─────────────────────────────────────────────────────────────────

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check

set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# ── Dashboard ─────────────────────────────────────────────────────────────────

# Display the SOTA Industrial Dashboard
# ── Quality ───────────────────────────────────────────────────────────────────

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check .

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .

# ── Hardening ─────────────────────────────────────────────────────────────────

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check

set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# ── Dashboard ─────────────────────────────────────────────────────────────────

# Display the SOTA Industrial Dashboard
# ── Quality ───────────────────────────────────────────────────────────────────

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check .

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .

# ── Hardening ─────────────────────────────────────────────────────────────────

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check

set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# ── Dashboard ─────────────────────────────────────────────────────────────────

# Display the SOTA Industrial Dashboard
# ── Quality ───────────────────────────────────────────────────────────────────

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check .

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .

# ── Hardening ─────────────────────────────────────────────────────────────────

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check

set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# ── Dashboard ─────────────────────────────────────────────────────────────────

# Display the SOTA Industrial Dashboard
# ── Quality ───────────────────────────────────────────────────────────────────

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check .

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix
    uv run ruff format .

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
