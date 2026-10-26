# Recent improvements

Incremental improvements to ocr-mcp, newest first — what got better and how
to use it. Release notes live in [CHANGELOG.md](../CHANGELOG.md); per-model
details in [AI_MODELS.md](../AI_MODELS.md).

Convention: add one entry per improvement (date, title, what/why, how to
use, files touched).

## 2026-10-26 — Status page: Backends card (model download + probe)

**What:** the Status (`/status`) page grew a Backends card listing all 14
engines with availability dot, model size, and per-backend **Download** and
**Test** buttons. Download polls `POST /api/models/download/{name}` with
live progress; Test runs `POST /api/backends/test` and shows the probe text
or the failure reason.

**Why:** model downloads (Indra ~76MB, VLMs several GB) used to look like a
hung job — now they show progress, and a backend can be verified without
running a full OCR job first. No `.env` edits needed for any of it.

**Files:** `web_sota/src/pages/status.tsx`

## 2026-10-26 — Indra OCR backend (14th engine)

**What:** new `indra-ocr` backend (Datalab-to 1M-param CPU OCR, ONNX, no
Torch/GPU). PDFs/images to markdown/text/JSON with layout blocks, reading
order, and per-line boxes + confidence. Auto `auto` mode prefers it first
among CPU engines.

**Why:** ~15x Tesseract and ~10x PP-OCR throughput, 92.2 layout score, 95
scripts, ~76MB auto-downloaded models — the new default for CPU-only,
high-volume, and offline use. Note: weights are OpenRAIL-M (free for
research/personal/startups <$20M; no competitive API use).

**Use:** Dashboard → OCR Backend → `indra-ocr`, or Settings → default
backend. First run downloads models (~30–60s), then ~200ms/page.

**Files:** `src/ocr_mcp/backends/indra_ocr_backend.py`,
`src/ocr_mcp/core/{backend_manager,config,backend_optimizer}.py`,
`pyproject.toml`, `AI_MODELS.md`

## 2026-10-26 — ESLint removed, Biome-only webapp lint

**What:** deleted the leftover Vite-template `eslint.config.js`, the `lint`
script, six ESLint devDependencies, and rewrote `web_sota/README.md` (was
pure template text).

**Why:** fleet standard is Biome + `tsc` (`just lint`, CI, root README all
agree) — ESLint was dead weight that failed `biome:ci` runs conceptually
and confused contributors.

**Files:** `web_sota/{eslint.config.js,package.json,bun.lock,package-lock.json,README.md}`
