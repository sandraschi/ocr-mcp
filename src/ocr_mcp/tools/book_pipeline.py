"""Book pipeline portmanteau tool — ingest scanned pages to EPUB.

Operations:
- detect_chapters: Find chapter boundaries in OCR page text.
- assemble_epub: Build EPUB from chapter text + metadata.
- detect_metadata: Extract title/author from first pages.
- full_pipeline: OCR + chapters + EPUB in one call (requires page image paths).
"""

import logging
from typing import Any, Literal

from fastmcp import Context

from ..core.backend_manager import BackendManager
from ..core.config import OCRConfig
from .models import ToolResponse

logger = logging.getLogger(__name__)

try:
    from ..services.book_assembler import assemble_epub
    from ..services.chapter_detector import detect_chapters, detect_metadata

    SERVICES_OK = True
except ImportError:
    SERVICES_OK = False


def register_book_pipeline_tool(app, backend_manager: BackendManager | None, config: OCRConfig):
    """Register the ingest_book portmanteau tool."""

    @app.tool()
    async def ingest_book(
        operation: Literal[
            "detect_chapters",
            "detect_metadata",
            "assemble_epub",
            "full_pipeline",
        ],
        ctx: Context,
        pages: list[dict[str, Any]] | None = None,
        image_paths: list[str] | None = None,
        title: str = "",
        author: str = "",
        output_path: str = "",
        backend: str = "unlimited-ocr",
        chapter_page: str = "",
        chapter_text: str = "",
        language: str = "en",
    ) -> ToolResponse:
        """Ingest scanned book pages to EPUB via chapter detection + assembly.

        ## Operations
        - detect_chapters: Pass pages=[{page_number, text, confidence}] — returns
          chapter boundaries with title, start_page, end_page, confidence.
        - detect_metadata: Pass pages=[...] from first 3 pages — returns title, author.
        - assemble_epub: Pass chapters=[{chapter_number, title, text}] plus title/author.
          Returns path, size_bytes, chapter_count.
        - full_pipeline: Pass image_paths=[...] — OCRs all pages, detects chapters,
          assembles EPUB, returns the path.

        ## Return Format
        {"success": bool, "result": {...}, "summary": str}

        ## Examples
        ingest_book(operation="detect_chapters", pages=[{"page_number":1,"text":"Chapter 1\\n..."}])
        ingest_book(operation="assemble_epub", title="My Book", author="Me",
                    chapters=[{"chapter_number":1,"title":"Ch1","text":"..."}])
        """
        op = operation
        try:
            if op == "detect_chapters":
                return await _handle_detect_chapters(pages)

            if op == "detect_metadata":
                return await _handle_detect_metadata(pages)

            if op == "assemble_epub":
                return await _handle_assemble_epub(
                    title, author, pages, chapter_page, chapter_text, output_path, language
                )

            if op == "full_pipeline":
                return await _handle_full_pipeline(image_paths, backend, title, author, output_path, language, ctx)

            return ToolResponse(success=False, operation=op, summary=f"Unknown operation: {op}")

        except Exception as e:
            logger.exception("ingest_book (%s) failed", op)
            return ToolResponse(success=False, operation=op, summary=str(e))


async def _handle_detect_chapters(pages) -> ToolResponse:
    if not SERVICES_OK:
        return ToolResponse(success=False, operation="detect_chapters", summary="chapter_detector not available")
    if not pages:
        return ToolResponse(success=False, operation="detect_chapters", summary="No pages provided")
    chapters = detect_chapters(pages)
    return ToolResponse(
        success=True,
        operation="detect_chapters",
        summary=f"Found {len(chapters)} chapters across {len(pages)} pages",
        result={"chapters": chapters, "count": len(chapters)},
    )


async def _handle_detect_metadata(pages) -> ToolResponse:
    if not SERVICES_OK:
        return ToolResponse(success=False, operation="detect_metadata", summary="chapter_detector not available")
    if not pages:
        return ToolResponse(success=False, operation="detect_metadata", summary="No pages provided")
    meta = detect_metadata(pages)
    return ToolResponse(
        success=True,
        operation="detect_metadata",
        summary=f"Detected: {meta.get('title', '?')} by {meta.get('author', '?')}",
        result=meta,
    )


async def _handle_assemble_epub(
    title, author, chapters_data, chapter_page, chapter_text, output_path, language
) -> ToolResponse:
    if not SERVICES_OK:
        return ToolResponse(success=False, operation="assemble_epub", summary="book_assembler not available")

    chapters = []
    if chapters_data:
        chapters = chapters_data
    elif chapter_page and chapter_text:
        chapters = [{"chapter_number": 1, "title": chapter_page.strip(), "text": chapter_text.strip()}]

    if not chapters:
        return ToolResponse(success=False, operation="assemble_epub", summary="No chapters provided")

    result = assemble_epub(
        title=title or "Untitled",
        author=author,
        chapters=chapters,
        output_path=output_path,
        language=language,
    )
    if result.get("success"):
        return ToolResponse(
            success=True,
            operation="assemble_epub",
            summary=f"EPUB: {result['path']} ({result['size_bytes']}b, {result['chapter_count']}ch)",
            result=result,
        )
    return ToolResponse(success=False, operation="assemble_epub", summary=result.get("error", "Assembly failed"))


async def _handle_full_pipeline(image_paths, backend, title, author, output_path, language, ctx) -> ToolResponse:
    if not SERVICES_OK:
        return ToolResponse(success=False, operation="full_pipeline", summary="Services not available")
    if not image_paths:
        return ToolResponse(success=False, operation="full_pipeline", summary="No image paths provided")

    bm = getattr(ctx, "_backend_manager", None)
    if not bm:
        return ToolResponse(
            success=False, operation="full_pipeline", summary="Backend manager not available in context"
        )

    # OCR all pages
    pages = []
    for img_path in sorted(image_paths):
        result = await bm.process_with_backend(backend, img_path, "text")
        text = result.get("text", "")
        pages.append(
            {
                "page_number": len(pages) + 1,
                "text": text,
                "confidence": result.get("confidence", 0.0),
            }
        )

    if not pages:
        return ToolResponse(success=False, operation="full_pipeline", summary="OCR produced no pages")

    # Detect chapters
    if not title:
        meta = detect_metadata(pages)
        title = meta.get("title", title)
        author = author or meta.get("author", author)

    chapters = detect_chapters(pages)

    # Build chapter text
    chapter_texts = []
    for ch in chapters:
        start = ch["start_page"]
        end = ch["end_page"] or len(pages)
        ch_text = "\n".join(pages[i - 1]["text"] for i in range(start, end + 1) if i <= len(pages))
        chapter_texts.append(
            {
                "chapter_number": ch["chapter_number"],
                "title": ch["title"],
                "text": ch_text,
            }
        )

    if not chapter_texts:
        fallback_text = "\n".join(p["text"] for p in pages)
        chapter_texts = [{"chapter_number": 1, "title": "Chapter 1", "text": fallback_text}]

    # Assemble EPUB
    result = assemble_epub(
        title=title or "Scanned Book",
        author=author,
        chapters=chapter_texts,
        output_path=output_path,
        language=language,
    )

    return ToolResponse(
        success=result.get("success", False),
        operation="full_pipeline",
        summary=f"Processed {len(pages)} pages, {len(chapters)} chapters -> {result.get('path', '?')}",
        result={
            "pages_ocr": len(pages),
            "chapters_detected": len(chapters),
            "title": title,
            "author": author,
            "epub": result,
        },
    )
