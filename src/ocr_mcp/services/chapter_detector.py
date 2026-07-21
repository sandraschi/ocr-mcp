"""Chapter detection from OCR page text.

Rules-based: scores each line as a possible chapter heading using
typographic heuristics, then selects the best candidates across all pages.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_CHAPTER_PATTERNS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"^(?:Chapter|CHAPTER|Chapitre|Kapitel|Cap[íi]tulo)\s+\d+\s*$"), 1.0),
    (re.compile(r"^(?:Chapter|CHAPTER)\s+[IVXLCDM]+\s*$"), 0.95),
    (re.compile(r"^\d+\.\s*$"), 0.8),
    (re.compile(r"^[IVXLCDM]+\.\s*$"), 0.85),
    (re.compile(r"^(?:Part|PART|Section|SECTION)\s+\d+\s*$"), 0.9),
    (
        re.compile(
            r"^(?:Prologue|Prolog|Foreword|Introduction|Epilogue|Epilog|Afterword|Appendix|Appendice|Index)\s*$",
            re.IGNORECASE,
        ),
        0.9,
    ),
    (re.compile(r"^\d{1,2}\s{2,}[A-Z][a-z]"), 0.6),
]


def detect_chapters(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Scan OCR page text and return chapter boundaries.

    Args:
        pages: List of {page_number, text, confidence} from batch OCR.

    Returns:
        List of {chapter_number, title, start_page, confidence} sorted by page.
    """
    candidates: list[dict[str, Any]] = []

    for page in pages:
        page_num = page.get("page_number", 0)
        text = page.get("text", "")
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

        for i, line in enumerate(lines):
            if len(line) > 100 or len(line) < 2:
                continue
            is_isolated = (i == 0 or not lines[i - 1]) and (i == len(lines) - 1 or not lines[i + 1])
            for pattern, base_score in _CHAPTER_PATTERNS:
                if pattern.match(line):
                    score = base_score
                    if is_isolated:
                        score += 0.1
                    if line.istitle():
                        score += 0.05
                    if line.endswith((".", "!", "?")):
                        score -= 0.2
                    if page.get("confidence", 1.0) < 0.5:
                        score -= 0.2
                    score = max(0.0, min(1.0, score))
                    candidates.append(
                        {
                            "page": page_num,
                            "line": line,
                            "score": round(score, 2),
                        }
                    )
                    break

    candidates.sort(key=lambda c: c["page"])
    candidates = [c for c in candidates if c["score"] >= 0.55]

    # De-duplicate: keep highest-scoring per page
    seen_pages: set[int] = set()
    deduped: list[dict[str, Any]] = []
    for c in candidates:
        if c["page"] not in seen_pages:
            seen_pages.add(c["page"])
            deduped.append(c)

    chapters = []
    for i, c in enumerate(deduped):
        start_page = c["page"]
        end_page = deduped[i + 1]["page"] - 1 if i + 1 < len(deduped) else None
        chapters.append(
            {
                "chapter_number": i + 1,
                "title": c["line"],
                "start_page": start_page,
                "end_page": end_page,
                "confidence": c["score"],
            }
        )

    return chapters


def detect_metadata(pages: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract title and author from the first few pages.

    Looks at the first 3 pages for patterns common on title pages.
    """
    meta: dict[str, Any] = {"title": "", "author": ""}
    first_text = "\n".join(p.get("text", "") for p in pages[:3])

    lines = [ln.strip() for ln in first_text.split("\n") if ln.strip()]

    title_candidates = []
    author_candidates = []

    for i, line in enumerate(lines):
        if re.match(r"^by\s+", line, re.IGNORECASE):
            author_candidates.append(re.sub(r"^by\s+", "", line, flags=re.IGNORECASE))
        if re.search(r"Copyright|Published by|ISBN|All rights reserved", line, re.IGNORECASE):
            if i > 0:
                author_candidates.insert(0, lines[i - 1])
        if line.istitle() and len(line) > 5 and len(line) < 80:
            title_candidates.append(line)

    if title_candidates:
        meta["title"] = title_candidates[0]
    if author_candidates:
        meta["author"] = author_candidates[0]

    return meta
