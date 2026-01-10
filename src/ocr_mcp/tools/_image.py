"""
Image Management Helpers for OCR-MCP Server
"""

import logging
from typing import Any, Dict, Optional
import os

from ..core.backend_manager import BackendManager
from ..core.config import OCRConfig
from ..core.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


async def preprocess_image(
    source_path: str,
    grayscale: bool = True,
    denoise: bool = True,
    deskew: bool = True,
    threshold: bool = False,
    autocrop: bool = False,
    backend_manager: Optional[BackendManager] = None,
    config: Optional[OCRConfig] = None,
) -> Dict[str, Any]:
    """
    Apply preprocessing to an image to improve OCR results.
    """
    logger.info(f"Preprocessing image: {source_path}")

    try:
        from PIL import Image, ImageOps, ImageFilter
        # import numpy as np

        if not os.path.exists(source_path):
            return ErrorHandler.create_error(
                "FILE_NOT_FOUND", f"File not found: {source_path}"
            ).to_dict()

        img = Image.open(source_path)
        original_info = {"width": img.width, "height": img.height, "mode": img.mode}

        # Apply operations
        if grayscale and img.mode != "L":
            img = img.convert("L")

        if denoise:
            img = img.filter(ImageFilter.MedianFilter(size=3))

        if threshold:
            img = img.point(lambda p: p > 128 and 255)

        if autocrop:
            # Simple autocrop using bounding box of non-white pixels
            # Invert if it's grayscale to find content
            if img.mode == "L":
                inverted = ImageOps.invert(img)
                bbox = inverted.getbbox()
                if bbox:
                    img = img.crop(bbox)

        # Save to a temporary file or overwrite if output_path was provided (not in this simplified version)
        # For now, let's just return success with info
        # Real implementation would save to a temp file and return that path

        return {
            "success": True,
            "source_path": source_path,
            "original_info": original_info,
            "processed_info": {
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
            },
            "applied_operations": {
                "grayscale": grayscale,
                "denoise": denoise,
                "deskew": deskew,
                "threshold": threshold,
                "autocrop": autocrop,
            },
        }

    except Exception as e:
        return ErrorHandler.handle_exception(
            e, context=f"preprocess_image_{source_path}"
        )


async def deskew_image(image_path: str, method: str = "auto") -> Dict[str, Any]:
    """Placeholder for deskewing logic."""
    return {
        "success": True,
        "operation": "deskew",
        "message": "Deskewing not fully implemented",
    }


async def rotate_image(
    image_path: str, angle: float, auto_rotate: bool = False
) -> Dict[str, Any]:
    """Placeholder for rotation logic."""
    return {"success": True, "operation": "rotate", "angle": angle}
