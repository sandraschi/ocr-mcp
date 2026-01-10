"""
Document Format Conversion Helpers for OCR-MCP
"""

import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path

from ..core.backend_manager import BackendManager
from ..core.config import OCRConfig
from ..core.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


async def convert_image(
    source_path: str,
    target_path: Optional[str] = None,
    format: str = "png",
    dpi: Optional[int] = None,
    quality: int = 95,
    optimize: bool = False,
    backend_manager: Optional[BackendManager] = None,
    config: Optional[OCRConfig] = None,
) -> Dict[str, Any]:
    """
    Convert image between different formats.
    """
    logger.info(f"Converting image {source_path} to {format}")

    try:
        from PIL import Image

        if not os.path.exists(source_path):
            return ErrorHandler.create_error(
                "FILE_NOT_FOUND", f"File not found: {source_path}"
            ).to_dict()

        if not target_path:
            p = Path(source_path)
            target_path = str(p.with_suffix(f".{format.lower()}"))

        img = Image.open(source_path)

        # Handle transparency if converting to JPEG
        if format.upper() in ["JPG", "JPEG"] and img.mode in ("RGBA", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        elif format.upper() in ["JPG", "JPEG"] and img.mode == "P":
            img = img.convert("RGB")

        save_kwargs = {"format": format.upper()}
        if format.upper() in ["JPG", "JPEG", "WEBP"]:
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = optimize

        if dpi:
            save_kwargs["dpi"] = (dpi, dpi)

        img.save(target_path, **save_kwargs)

        return {
            "success": True,
            "source_path": source_path,
            "target_path": target_path,
            "format": format.upper(),
            "size_bytes": os.path.getsize(target_path),
        }

    except Exception as e:
        return ErrorHandler.handle_exception(e, context=f"convert_image_{source_path}")


async def convert_pdf_to_images(
    pdf_path: str,
    output_directory: str,
    dpi: int = 300,
    format: str = "PNG",
    first_page: Optional[int] = None,
    last_page: Optional[int] = None,
    backend_manager: Optional[BackendManager] = None,
    config: Optional[OCRConfig] = None,
) -> Dict[str, Any]:
    """
    Convert PDF pages to individual images.
    """
    logger.info(f"Converting PDF {pdf_path} to images")

    try:
        from pdf2image import convert_from_path

        if not os.path.exists(pdf_path):
            return ErrorHandler.create_error(
                "FILE_NOT_FOUND", f"PDF not found: {pdf_path}"
            ).to_dict()

        os.makedirs(output_directory, exist_ok=True)

        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=first_page,
            last_page=last_page,
            fmt=format.lower(),
        )

        saved_files = []
        for i, img in enumerate(images):
            page_num = (first_page or 1) + i
            out_file = os.path.join(
                output_directory, f"page_{page_num:03d}.{format.lower()}"
            )
            img.save(out_file, format.upper())
            saved_files.append(out_file)

        return {
            "success": True,
            "pdf_path": pdf_path,
            "output_directory": output_directory,
            "files_created": len(saved_files),
            "files": saved_files,
        }
    except Exception as e:
        return ErrorHandler.handle_exception(e, context=f"pdf_to_images_{pdf_path}")


async def embed_ocr_text(
    image_path: str,
    output_path: str,
    ocr_backend: str = "auto",
    title: Optional[str] = None,
    include_original_image: bool = True,
    backend_manager: Optional[BackendManager] = None,
    config: Optional[OCRConfig] = None,
) -> Dict[str, Any]:
    """
    Create a searchable PDF by embedding OCR text.
    """
    # This would involve calling an OCR backend and then using something like reportlab or pikepdf
    # For now, let's keep it as a placeholder that calls the backend manager
    if not backend_manager:
        return ErrorHandler.create_error(
            "INTERNAL_ERROR", "Backend manager missing"
        ).to_dict()

    return {
        "success": True,
        "message": "Searchable PDF embedding not yet fully implemented",
    }
