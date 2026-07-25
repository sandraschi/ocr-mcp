# Form Reconstruction — Implementation Plan

**Feature:** `form_reconstruct` (ocr-mcp + libreoffice-mcp bridge)
**Date:** 2026-07-25
**Status:** Planned

## Task Breakdown

### Phase 1: ocr-mcp — Bbox Enhancements

| Task | File | Effort | Dependencies |
|------|------|--------|--------------|
| 1.1 Add `dpi` to `detect_forms` response | `_analysis.py` | Small | - |
| 1.2 Add `associated_text` to each detected field | `_analysis.py` | Small | 1.1 |
| 1.3 Add px→mm conversion utility | `_analysis.py` | Small | 1.1 |
| 1.4 Update `ToolResponse` result schema | `models.py` | Small | 1.1 |

**Verify:** Run `detect_forms` on a known form image; confirm response includes `dpi` and fields have `associated_text`.

### Phase 2: ocr-mcp — `reconstruct_form` Assembly

| Task | File | Effort | Dependencies |
|------|------|--------|--------------|
| 2.1 Add `FormReconstruction` Pydantic models | `models.py` | Medium | - |
| 2.2 Create `_form_recon.py` with assembly logic | `_form_recon.py` (new) | Medium | 2.1, 1.3 |
| 2.3 Add `reconstruct_form` operation to portmanteau | `ocr_tools.py` | Small | 2.2 |
| 2.4 Add `form_reconstruct` to `_STEP_TOOL_MAP` | `_workflow.py` | Small | 2.3 |

**Verify:** Call `process_document(operation="reconstruct_form", source_path="form-scan.png")`; inspect JSON output.

### Phase 3: libreoffice-mcp — ODT Form Generation

| Task | File | Effort | Dependencies |
|------|------|--------|--------------|
| 3.1 Create `odf_form.py` with form control primitives | `odf_form.py` (new) | Large | - |
| 3.2 Create `form_recon.py` consuming JSON → ODT | `form_recon.py` (new) | Large | 3.1, 2.2 |
| 3.3 Add `build_form_document` operation | `operations.py` | Small | 3.2 |
| 3.4 Register in `libreoffice` portmanteau | `operations.py` | Small | 3.3 |

**Verify:** Feed a FormReconstruction JSON to build_form_document; open resulting ODT in LO; verify positions match source.

### Phase 4: libreoffice-mcp — Print Modes

| Task | File | Effort | Dependencies |
|------|------|--------|--------------|
| 4.1 Add `print_filled_form` (full doc print) | `form_recon.py` | Small | 3.2 |
| 4.2 Add `print_entries_only` (entries overlay) | `form_recon.py` | Medium | 3.2 |
| 4.3 Add alignment marks for overlay mode | `form_recon.py` | Small | 4.2 |
| 4.4 Register operations in portmanteau | `operations.py` | Small | 4.1, 4.2 |

**Verify:** Fill a form in LO, run print_entries_only, confirm PDF has only the field values at correct positions with alignment marks.

### Phase 5: Cross-repo Integration Test

| Task | Effort | Dependencies |
|------|--------|--------------|
| 5.1 Write end-to-end test script | Small | Phase 4 |
| 5.2 Document in `llms-full.txt` (both repos) | Small | 5.1 |
| 5.3 Update help content in both repos | Small | 5.1 |

**Verify:** Full pipeline executes: scan → detect → reconstruct → build → print.

## Effort Summary

| Phase | Effort | Key Risk |
|-------|--------|----------|
| 1 — Bbox enhancements | ~2h | None (simple additions) |
| 2 — FormReconstruction assembly | ~3h | Paper size auto-detection edge cases |
| 3 — ODT form generation | ~6h | ODF draw:text-box vs form:control positioning |
| 4 — Print modes | ~3h | Printer alignment variance (±2mm) |
| 5 — Integration test + docs | ~2h | - |

**Total:** ~16h

## Verification Gates

After each phase:
1. `ruff check src/` — zero errors
2. `ruff format src/ --check` — clean
3. Phase-specific functional test (documented in phase verify section)

After all phases:
1. Cross-repo pipeline test passes
2. Both repos' `llms-full.txt` updated
3. Both repos' help systems reference the new feature
