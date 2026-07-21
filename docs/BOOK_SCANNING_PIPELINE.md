# Book Scanning Pipeline: Spine to EPUB

A one-shot flow from a sliced paperback to a finished EPUB in Calibre.

---

## Hardware

| Item | Why | Cost |
|------|-----|------|
| **Guillotine paper cutter** | Slice the spine off, get loose pages. Sandra already has one. | ~$150 (owned) |
| **Duplex document feeder scanner** | Feeds loose pages fast. **Fujitsu ScanSnap iX1400** (new, ~$350) or **iX500** (used, ~$200-300). Key spec: duplex, 25+ ppm, auto-detect page size. | ~$200-350 |
| Optional: **CUT/SAW jig** | Guides the guillotine for clean, consistent spine cuts across 200 pages. Not necessary for paperbacks — paperback spines are soft enough to cut freehand. | $0 |

**Why not a flatbed or CZUR?** 200 pages on a flatbed is 100 flips, each requiring a manual scan trigger — 30+ minutes of tedium. A duplex document feeder does all 200 pages in ~4 minutes unattended.

**Why not outsource?** Sending books to digitisation services costs $10-30/book. After ~15 books the scanner pays for itself.

---

## Software Pipeline

```
  Duplex scanner     OCR-MCP batch      Chapter detection      EPUB assembly       Calibre
   (200 pages)        (page OCR)          (heading regex)      (ebooklib)         (import)
       |                   |                    |                    |                |
  page_001.png -->  OCR text chunks -->  split by chapter -->  wrap in EPUB -->  calibre-mcp
  page_002.png                                                                   calibre_add_book
  ...
  page_200.png
```

### Step 1: Scan

Feed the loose page stack into the duplex scanner. Output: `page_001.png` through `page_200.png`.
The ScanSnap auto-feeds, double-sided, at 300 DPI grayscale. Saves to a folder.

**Manual step:** Place the pages face-up in the feeder. The scanner handles the rest.

### Step 2: OCR (exists)

```
manage_workflow(
    operation="process_batch_intelligent",
    image_paths=["scans/book/page_*.png"],
    backend="unlimited-ocr"
)
```

Returns a list of `{page_number, text, confidence}` dicts. The batch tool already handles
this, but it returns results independently — no assembly logic.

### Step 3: Chapter Detection (needs build)

Rules-based approach using the OCR output:

```python
CHAPTER_PATTERNS = [
    r"^(?:Chapter|CHAPTER|Chapter\s+\d+|CHAPTER\s+\d+)\s*$",
    r"^\d+\.$",                          # "1." on its own line
    r"^[IVXLCDM]+\.$",                   # "I.", "II." roman numerals
    r"^(?:\d+\s+)?[A-Z][a-z\s]{3,50}$",  # Standalone heading line
]
```

Each candidate heading is scored: isolated on its own line, followed by a blank line,
doesn't end with punctuation, shorter than 80 chars. Anything scoring above 0.6 is a
chapter boundary.

### Step 4: EPUB Assembly (needs build)

Using `ebooklib` (pure Python, no Calibre dependency):

```python
from ebooklib import epub

book = epub.EpubBook()
book.set_identifier("book-2026-001")
book.set_title("Ingested Title")
book.set_language("en")

for chapter_num, chapter_text in chapters.items():
    c = epub.EpubHtml(title=f"Chapter {chapter_num}",
                       file_name=f"chap_{chapter_num}.xhtml")
    c.content = f"<h1>Chapter {chapter_num}</h1><p>{chapter_text}</p>"
    book.add_item(c)
    book.toc.append(epub.Link(f"chap_{chapter_num}.xhtml",
                              f"Chapter {chapter_num}", f"chap_{chapter_num}"))

epub.write_epub("output/book.epub", book)
```

**Metadata prompt:** The user enters title, author, ISBN (or the LLM extracts it from
the first few pages — title page, copyright page). We can prompt for this in the webapp.

### Step 5: Calibre Ingest (exists, via calibre-mcp)

```python
calibre_add_book(file_path="output/book.epub",
                 title="Scanned Book Title",
                 authors=["Author Name"],
                 tags=["from-ocr-mcp", "scanned"])
```

Calibre handles EPUB validation, cover extraction, and library organisation.

---

## Webapp Workflow

A new page or dashboard panel:

```
┌──────────────────────────────────────────────┐
│  Book Pipeline                               │
│                                              │
│  Title: [________________________]           │
│  Author: [________________________]          │
│                                              │
│  Page folder: [scans/my-book/]  [Browse]     │
│                                              │
│  [Detect Chapters]  [Assemble EPUB]          │
│  [Send to Calibre]                           │
│                                              │
│  Progress: ████████░░ 80%                    │
│  Status: Building EPUB...                    │
│  Output: output/my-book.epub (2.4MB)         │
│                                              │
│  ── Chapter Preview ──                       │
│  ✓ Ch1: The Beginning                        │
│  ✓ Ch2: A New Chapter                        │
│  ? Ch3: Untitled (low confidence)            │
│  ✓ Ch4: Conclusion                           │
└──────────────────────────────────────────────┘
```

---

## New MCP Tools Required

| Tool | Operation | Purpose |
|------|-----------|---------|
| `ingest_book` | `detect_chapters` | Scan OCR output, find chapter boundaries |
| `ingest_book` | `assemble_epub` | Build EPUB from chapter text + metadata |
| `ingest_book` | `detect_metadata` | Extract title/author from first pages |
| `ingest_book` | `full_pipeline` | OCR → chapters → EPUB → Calibre in one call |

---

## Files

| File | Purpose |
|------|---------|
| `src/ocr_mcp/tools/book_pipeline.py` | Portmanteau tool: `ingest_book` |
| `src/ocr_mcp/services/book_assembler.py` | EPUB assembly logic (ebooklib) |
| `src/ocr_mcp/services/chapter_detector.py` | Heading detection and scoring |
| `web_sota/src/pages/book-pipeline.tsx` | Webapp page for the pipeline |
| `pyproject.toml` | Add `ebooklib` dependency |

---

## Estimated Implementation

| Task | Time | Depends on |
|------|------|-----------|
| Chapter detector | 2-3 hours | — |
| EPUB assembler | 2-3 hours | — |
| `ingest_book` MCP tool | 1 hour | chapter detector + assembler |
| Webapp pipeline page | 3-4 hours | MCP tool |
| Calibre integration test | 1 hour | calibre-mcp running |
| **Total** | **~10-12 hours** | — |

---

## See Also

- `docs/BOOK_SCANNING.md` — scanner hardware guide, CZUR vs DIY vs cut-and-feed
- calibre-mcp: `calibre_add_book`, `calibre_search`, `calibre_metadata`
