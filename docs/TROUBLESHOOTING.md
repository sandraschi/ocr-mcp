# TROUBLESHOOTING — ocr-mcp

Symptom → cause → fix. Fleet-wide traps live in
`mcp-central-docs/troubleshooting/BUGS_DEPOT.md`.

## Startup

- **Backend never binds :10859** — stale zombie holds the port.
  `just zombie-clean`, then `.\start.ps1`. `start.ps1` clears the port
  before bind and polls TCP readiness (no fixed sleeps).
- **`uv sync` resolves forever** — torch CU126 index hiccup; retry, or
  `uv sync --offline` if the venv is already populated.
- **First VLM call hangs** — model download (`OCR_MODEL_DIR`), GBs.
  Watch `GET /api/models/status`; CPU fallback is 10–50x slower.

## OCR quality / backends

- **`florence-2` reports as `paddleocr-vl`** — by design
  (`canonical_backend_name`; Florence retired). Use canonical names.
- **Tesseract missing** — install binary or set `TESSERACT_CMD` in `.env`.
- **Blank-page garbage text** — preprocess first
  (`manage_image(operation="preprocess")`: deskew/denoise), or pick
  `ocr_mode="accurate"`.
- **GPU OOM on VLM** — `manage_workflow(operation="manage_models")` to
  unload idle models; `just gpu-status` shows who holds the 4090.

## Dashboard (web_sota)

- **Red backend dot** — backend down or wrong port; check
  `GET /api/health`, then `fleet-start.config.ps1` ports (10858/10859).
- **Chat empty / MOCK badges** — no provider configured yet (by design).
  Settings → test Ollama (`:11434`) or paste a key; badges clear on success.
- **Inbox empty** — nothing registered in the corpus yet. Process a file
  (auto-registers) or check `GET /api/corpus?sort_by=created_at`.

## Scanner (Windows WIA)

- **No scanners listed** — hardware off, or Windows Image Acquisition
  service stopped (`services.msc` → WIA → run). USB re-plug re-enumerates.
- **Scan saves to `./scans`** — pass `save_path`/`save_directory`
  explicitly; the CWD default is a fallback, not a feature.

## Tests

- **Perf lower-bound flakes** — by design: mock doubles return instantly,
  so only upper-bound (hang/regression) thresholds assert. Real inference
  timing is measured with real backends, not in CI.
- **`--ignore=tests/benchmarks`** for the fast gate; benchmarks need
  `pytest-benchmark` and real models.
- **Hypothesis `function_scoped_fixture`** — fuzz tests share the
  function-scoped `file_manager` deliberately (temp accumulation, teardown
  cleanup); the suppression is declared in-file, not a blanket ignore.

## CI

- `ci.yml` delegates to `sandraschi/fleet-ci` `hybrid.yml`. A red run with
  no code change usually means the reusable ref moved — pin or re-run.
- Frontend gates need webapp `check` script parity (`tsc -b`); if CI
  reports a skipped gate, the script name drifted, not the code.
