"""EPUB assembly from chapter text using ebooklib.

Takes a list of {title, text} chapters and wraps them in a valid EPUB container.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from ebooklib import epub

    EBOOOKLIB_OK = True
except ImportError:
    EBOOOKLIB_OK = False


def assemble_epub(
    title: str,
    author: str,
    chapters: list[dict[str, Any]],
    output_path: str | Path = "",
    language: str = "en",
) -> dict[str, Any]:
    """Build an EPUB from chapter text.

    Args:
        title: Book title.
        author: Author name.
        chapters: List of {chapter_number, title, text} dicts.
        output_path: Output file path. If empty, auto-generate.
        language: Language code (default: en).

    Returns:
        {success, path, size_bytes, chapter_count}
    """
    if not EBOOOKLIB_OK:
        return {"success": False, "error": "ebooklib not installed. pip install ebooklib"}

    if not chapters:
        return {"success": False, "error": "No chapters provided"}

    book = epub.EpubBook()
    book.set_identifier(f"ocr-mcp-{hash(title + author) % 10**12:012d}")
    book.set_title(title.strip() or "Untitled")
    book.set_language(language)
    if author:
        book.add_author(author.strip())

    style = """
    body { font-family: serif; line-height: 1.6; margin: 2em; }
    h1 { text-align: center; margin-top: 2em; }
    p { text-indent: 1.5em; margin: 0; }
    """

    css = epub.EpubItem(uid="style", file_name="style/default.css", media_type="text/css", content=style)
    book.add_item(css)

    spine = ["nav"]
    toc = []

    for ch in chapters:
        chap_num = ch.get("chapter_number", 1)
        chap_title = ch.get("title", f"Chapter {chap_num}")
        chap_text = ch.get("text", "")

        file_name = f"chap_{chap_num:03d}.xhtml"
        content = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>{chap_title}</title>
<link rel="stylesheet" type="text/css" href="style/default.css"/>
</head>
<body>
<h1>{chap_title}</h1>
{" ".join(f"<p>{p}</p>" for p in chap_text.split("\n") if p.strip())}
</body>
</html>"""

        c = epub.EpubHtml(title=chap_title, file_name=file_name, lang=language)
        c.content = content
        c.add_item(css)
        book.add_item(c)
        spine.append(c)
        toc.append(epub.Link(file_name, chap_title, file_name))

    book.toc = toc
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = spine

    if not output_path:
        safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip() or "book"
        output_path = f"{safe_title[:60]}.epub"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    epub.write_epub(str(output_path), book)
    size = output_path.stat().st_size

    logger.info("EPUB written: %s (%d bytes, %d chapters)", output_path, size, len(chapters))

    return {
        "success": True,
        "path": str(output_path),
        "size_bytes": size,
        "chapter_count": len(chapters),
    }
