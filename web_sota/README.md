# ocr-mcp webapp (`web_sota/`)

React + Vite + TypeScript + TailwindCSS frontend for OCR-MCP.
Backend: FastAPI in `backend/app.py` (port 10859); dev server proxies `/api` there.

## Run

```powershell
# from repo root
.\web_sota\start.ps1        # backend :10859 + frontend :10858
```

Or directly: `bun run dev` (port 10858).

## Gates

```powershell
bun run check      # tsc -b
bun run biome:ci   # lint + format check (Biome is the linter here)
```

There is no ESLint in this repo — Biome + `tsc` are the fleet standard
(see root README "Industrial Quality Stack" and `just lint`).
