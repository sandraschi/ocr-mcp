# SPEC: Form Reconstruction Pipeline (OCR → LibreOffice → Print)

**Feature:** `form_reconstruct`
**Status:** Spec phase
**Date:** 2026-07-25
**Repos:** ocr-mcp (source), libreoffice-mcp (consumer)

## Problem & Goal

**Real-world problem:** City office forms (Meldezettel, Anmeldeformulare, Finanzamt,
Magistrat) must be filled by hand. Handwriting is illegible, you fill the same
personal data (name, address, Geburtsdatum, Staatsangehӧrigkeit) across 3-5 forms,
and rejection due to unreadable fields means another trip to the Amt.

**Solution:** Scan the blank form once, type answers on a computer, print only the
entries onto the blank form paper loaded in the printer tray. The office receives
a perfectly legible, typed-looking form. No OCR reconstruction of the form itself --
the physical original is the form; the printed text lands in the right boxes.

## Architecture

```
Scanner    →   OCR text          →   detect_forms      →   reconstruct_form
(WIA)          (14 backends)          (checkboxes,           (NEW: assemble
                                     text fields,            FormReconstruction
                                     signatures,             JSON)
                                     radio buttons)

FormReconstruction JSON   →   libreoffice-mcp: build_form
                                    →   fillable ODT
                                          ↓
                                    print_filled_form   OR   print_entries_only
                                    (full doc)                (user entries only,
                                                              positioned for
                                                              physical form overlay)
```

### Why two repos

ocr-mcp owns detection and structural analysis (it already has `detect_forms`,
`extract_tables`, `analyze_layout`). libreoffice-mcp owns document creation
(it already has ODT template merge, format conversion, writer bridge). Neither
should take on the other's domain. The bridge is a shared data contract.

## Requirements

### R1: `reconstruct_form` operation (ocr-mcp)

New operation on the existing `process_document` portmanteau tool.

**Input:**
- `source_path: str` — path to scanned form image (JPG/PNG/PDF)
- `backend: OCRBackend` — OCR engine for text extraction (default "auto")
- `paper_size: str | None` — "A4", "Letter", "Legal" (auto-detect if None)
- `include_tables: bool` — whether to reconstruct detected tables as ODT tables

**Output:** `FormReconstruction` JSON with:
- `paper_size`, `orientation` (detected)
- `source_path` (path to the scanned image)
- `dpi` (detected image DPI, needed for px→mm conversion)
- `pages`: list of per-page field arrays
  - Each field: `field_type`, `label` (OCR'd nearby text), `bbox_mm` (x,y,w,h in mm),
    `page`, `state` (checkbox checked/unchecked), `group` (radio group name)
- `tables`: array of extracted table grids with headers + cell data
- `text_blocks`: non-field text labels positioned for reproduction

### R2: `build_form_document` operation (libreoffice-mcp)

New operation on the existing `libreoffice` portmanteau tool.

**Input:**
- `form_reconstruction_path: str` — path to JSON from ocr-mcp
- `output_format: Literal["odt", "pdf"]` — output format (default "odt")
- `with_background: bool` — include scanned form as background layer (default True)
- `font_size: int` — base font size for labels (default 10)
- `save_path: str | None` — where to save the output (default: auto-generated path in output dir)

**Output:** Path to generated fillable document.

**Behavior:** The generated ODT is an **empty template** -- all fields are blank,
ready for filling. The user opens it, fills the fields, saves a copy for each
instance. The blank ODT can be archived and reused indefinitely without
re-scanning the original form.

**What it builds:**
1. ODT document at the detected paper size
2. Background layer: scanned form image at 15% opacity (positioning guide)
3. Text labels at their detected positions (read-only, from ocr-mcp text blocks)
4. Editable form controls at each detected field position:
   - Text inputs → `draw:text-box` shapes at bbox position
   - Checkboxes → `draw:text-box` with click-to-toggle
   - Radio groups → grouped draw elements
   - Signature areas → empty framed `draw:rect`
   - Date fields → text input with date format hint
5. Tables: proper LO `table:table` elements with OCR'd headers and data cells

### R3: `print_filled_form` operation (libreoffice-mcp)

Print the full document (background guide + labels + user entries).

### R4: `print_entries_only` operation (libreoffice-mcp)

Print only the user-filled field values at their exact bbox positions, with the
background guide and all labels stripped. The output aligns precisely with the
physical form if the paper is loaded with the same orientation in the printer tray.

**Use case A -- City office forms (have blank form, need clean text):**
1. Pick up blank forms at the Magistrat / Bezirksamt
2. Scan each form once (different forms have different layouts)
3. Type personal data (name, address, Geburtsdatum, etc.) once per form
4. Print entries-only overlay onto the blank form paper from the printer tray
5. Result: typed-looking Amt-formular, perfectly legible, no rejection risk

**Use case B -- Full reconstruction (no blank form, need a full copy):**
1. Scan the form once (any paper form -- tax, registration, medical intake)
2. OCR text + detect fields + reconstruct layout as fillable ODT
3. **Save the blank ODT as a reusable template** (skip this step on repeat use)
4. Fill in fields in LibreOffice for each instance
5. `print_filled_form` prints the complete document -- background + labels + entries
6. Result: a clean, type-written stand-alone form. The blank ODT template is a one-time scan investment; subsequent fills (different dates, different data) reuse the same file.

### R5: Form Detection Enhancement (ocr-mcp `detect_forms`)

The existing `detect_forms` returns bbox in pixel coordinates. Add `dpi` to the
response so the `reconstruct_form` step can convert px→mm. Also improve text
label association: each field should have an `associated_text` field with the
OCR'd label text nearest to the field.

## Data Contract: `FormReconstruction` (cross-repo schema)

```python
from pydantic import BaseModel
from typing import Literal

class FormField(BaseModel):
    field_type: Literal["text_input", "checkbox", "radio", "signature", "date", "dropdown"]
    label: str | None          # OCR'd label text near the field
    bbox_mm: tuple[float, float, float, float]  # x, y, w, h in millimetres
    page: int                  # 1-based page number
    state: dict | None         # checkbox: {"checked": bool}
    group: str | None          # radio group name (shared by all buttons in group)
    confidence: float          # detection confidence 0.0-1.0

class DetectedTable(BaseModel):
    headers: list[str]
    rows: list[list[str]]      # cell text per row
    bbox_mm: tuple[float, float, float, float]
    page: int

class TextBlock(BaseModel):
    text: str
    bbox_mm: tuple[float, float, float, float]
    page: int
    block_type: Literal["label", "heading", "paragraph", "instruction"]

class FormReconstruction(BaseModel):
    version: str               # "1.0"
    paper_size: str            # "A4", "Letter", "Legal"
    orientation: Literal["portrait", "landscape"]
    source_path: str           # path to original scan
    dpi: int                   # scan DPI
    pages: list[FormPage]
    tables: list[DetectedTable]
    text_blocks: list[TextBlock]

class FormPage(BaseModel):
    page_num: int
    fields: list[FormField]
```

## Implementation Phases

### Phase 1: ocr-mcp — Bbox Enhancements
- Update `detect_forms` to return `dpi` alongside bbox pixels
- Add `associated_text` to each detected field (OCR label text nearest to field)
- Add px→mm conversion utility in `_analysis.py`
- **Verify:** `detect_forms` response includes `dpi` and `associated_text` per field

### Phase 2: ocr-mcp — `reconstruct_form` Assembly
- New function in `_analysis.py`: `reconstruct_form_reconstruction()`
- Add `reconstruct_form` operation to `process_document` portmanteau
- Assembles detect_forms output + analyze_layout output + OCR text into
  `FormReconstruction` JSON
- Auto-detects paper size from image dimensions + DPI
- **Verify:** JSON validates against FormReconstruction schema, px→mm conversion correct

### Phase 3: libreoffice-mcp — ODT Form Generation
- New module: `src/libreoffice_mcp/form_recon.py`
- Consumes FormReconstruction JSON
- Generates ODF XML with:
  - Scanned form background image (opacity toggle)
  - Draw frames with text-boxes at each bbox_mm position
  - Table elements from DetectedTable data
  - Proper ODF form namespace (`office:forms`, `form:form`, `form:text`, `form:checkbox`)
- Add `build_form_document` operation to `libreoffice` portmanteau
- **Verify:** Generated ODT opens in LO, fields are editable, positions match original

### Phase 4: libreoffice-mcp — Print Modes
- `print_filled_form`: converts ODT to PDF + triggers print
- `print_entries_only`: strips background + labels, produces overlay document
- Uses soffice `--print-to` for printing
- **Verify:** PDF output of entries-only has fields at correct positions

### Phase 5: Cross-repo Integration Test
- End-to-end: scan form → detect → reconstruct → build ODT → print
- Document in `llms-full.txt` for both repos
- **Verify:** Full pipeline executes without manual steps between tools

## Non-Goals

- Handwriting recognition in form fields (use existing OCR, user corrects errors)
- Automatic form filling (user fills manually in LO)
- PDF form creation (the ODT approach is simpler, more editable)
- Digital signature support
- Multi-page form alignment correction (assumes single scan pass)
- Hand-filled forms as input (the form must be blank for reconstruction;
  if it already has handwritten entries, scan it as a regular document instead)
- Persistent field data storage (the ODT is the persistence layer -- fill, save-as
  for each instance. No separate database of field values.)

## New Files

| Repo | File | Purpose |
|------|------|---------|
| ocr-mcp | `src/ocr_mcp/tools/_form_recon.py` | FormReconstruction JSON assembly |
| libreoffice-mcp | `src/libreoffice_mcp/form_recon.py` | ODT form document generation |
| libreoffice-mcp | `src/libreoffice_mcp/odf_form.py` | ODF XML form control primitives |

## Modified Files

| Repo | File | Change |
|------|------|---------|
| ocr-mcp | `src/ocr_mcp/tools/_analysis.py` | Add dpi to detect_forms, add associated_text |
| ocr-mcp | `src/ocr_mcp/tools/ocr_tools.py` | Add reconstruct_form operation + Literal entry |
| ocr-mcp | `src/ocr_mcp/tools/models.py` | Add FormReconstruction Pydantic models |
| libreoffice-mcp | `src/libreoffice_mcp/operations.py` | Add build_form_document, print_filled_form, print_entries_only operations |

## Open Questions

1. **ODF form controls vs. draw text-boxes**: ODF has real form controls (`form:text`, `form:checkbox`)
   but positioning them precisely at bbox coordinates may be limited. Draw text-boxes are positionable
   but not semantically "fillable." Which approach? (Answer: use draw shapes with text annotations
   for positioning, accept that the user types directly into the positioned text boxes.)

2. **Multi-page PDF forms**: If the form is scanned as a multi-page PDF, should each page be
   reconstructed separately? (Answer: yes — `FormReconstruction.pages` supports multi-page.)

3. **Form field label association accuracy**: The current `detect_forms` associates text by proximity
   heuristics. Should we add an LLM pass to improve label→field mapping? (Answer: not in v1,
   proximity heuristics with fuzzy OCR text matching is sufficient.)

4. **print_entries_only alignment guarantee**: Printer feed alignment varies by ±2mm. Should the
   spec include alignment marks (corner crosses) to help the user manually align? (Answer: add
   alignment marks as a `print_margins_mm` option — not mandatory but recommended.)
