# OCR-MCP Webapp Redesign (July 2026)

**Goal:** Streamline the webapp from a multi-page maze to a single-purpose dashboard
where users can drop/scan a document, OCR it, and read the result without navigating.

## What Changed

| Before | After |
|--------|-------|
| Two frontends (`frontend/` + `web_sota/`) | One frontend (`web_sota/`) |
| 10 sidebar nav items | 5 sidebar nav items |
| Scan workflow spans 4 pages | Everything on the dashboard |
| Static hardcoded KPIs on dashboard | Live API-driven KPIs |
| Sidebar collapse toggle at bottom | Sidebar collapse toggle at top (fleet standard) |
| No `data-testid` attributes | `data-testid` on all interactive elements |

## Removed Pages

| Page | Reason |
|------|--------|
| `/import` | Absorbed into dashboard drop zone |
| `/scanner` | Absorbed into dashboard scanner control |
| `/scan-viewer` | Absorbed into dashboard preview |
| `/process` (Pipelines) | Rarely used; removed from sidebar, page retained |
| `/chat` | Rarely used; removed from sidebar, page retained |

## Dashboard Layout (Single Page, All Actions)

```
TOP:   Backend health dot | Scanner dropdown | Backend selector | [Quick Scan & OCR]
MID:   Drop zone OR image preview
       ┌─────────────────────────────────────┐
       │  OCR Result (editable textarea)     │
       │  [Copy] [Download .txt] [Download]  │
       └─────────────────────────────────────┘
BOT:   KPI row (models, backends, jobs) | Recent image thumbnails
```

## Workflow (No Page Navigation)

1. **Pick input:** Drop a file on the zone, click to browse, or select a scanner
2. **Click "Quick Scan & OCR":** One button does everything
3. **Wait:** Progress bar + status text
4. **Read:** OCR result appears inline in the editable textarea
5. **Export:** Copy, download as .txt, or download as .md

## Sidebar (5 Items)

| Route | Label | Icon | Data-testid |
|-------|-------|------|-------------|
| `/` | Dashboard | LayoutDashboard | `nav-dashboard` |
| `/editor` | Editor | FileEdit | `nav-editor` |
| `/status` | Activity | Activity | `nav-activity` |
| `/settings` | Settings | Settings | `nav-settings` |
| `/help` | Help | HelpCircle | `nav-help` |

Chat and Pipelines are removed from sidebar but still accessible via direct URL.

## Data-testid Attributes

| Element | data-testid |
|---------|-------------|
| Dashboard container | `dashboard` |
| Drop zone | `drop-zone` |
| Quick Scan button | `quick-scan-ocr` |
| Backend selector | `backend-select` |
| OCR result textarea | `ocr-result` |
| Backend health indicator | `backend-dot` |
| KPI: server name | `kpi-server` |
| KPI: tool count | `kpi-tools` |
| KPI: available backends | `kpi-backends` |
| KPI: jobs completed | `kpi-jobs` |
| Export copy button | `export-copy` |
| Export download txt | `export-txt` |
| Export download md | `export-md` |

## Files Changed

| File | Action |
|------|--------|
| `frontend/` | Deleted (legacy v2) |
| `docs/WEBAPP_REDESIGN.md` | Created (this file) |
| `web_sota/src/store/index.ts` | Expanded — OCRTextState added |
| `web_sota/src/pages/dashboard.tsx` | Rewritten — Quick Scan + inline editor |
| `web_sota/src/components/layout/sidebar.tsx` | Simplified to 5 items, toggle at top |
| `web_sota/src/App.tsx` | Removed Import/Scanner/ScanViewer/Process/Chat routes |
| `web_sota/src/components/layout/topbar.tsx` | Added live backend health dot |
| `web_sota/src/pages/help.tsx` | Updated page list |
| `web_sota/start.ps1` | Removed legacy frontend references |

## Dependencies (unchanged)

No new npm packages added. Existing stack: React 19, Vite 7, Tailwind, Zustand,
Lucide icons, Radix primitives.
