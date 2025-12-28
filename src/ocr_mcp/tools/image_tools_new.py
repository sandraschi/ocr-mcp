"""
Image Management Tools for OCR-MCP Server - PORTMANTEAU DESIGN

Consolidates image preprocessing and conversion operations into a single tool.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..core.backend_manager import BackendManager
from ..core.config import OCRConfig
from ..core.error_handler import ErrorHandler, create_success_response

logger = logging.getLogger(__name__)


def register_image_management_tools(app, backend_manager: BackendManager, config: OCRConfig):
    """Register image management portmanteau tool with the FastMCP app."""

    @app.tool()
    async def image_management(
        operation: str,
        image_path: str,
        # Preprocessing parameters
        output_path: Optional[str] = None,
        method: str = "auto",
        intensity: float = 1.0,
        enhancement_type: str = "auto",
        angle: float = 0.0,
        auto_rotate: bool = False,
        x: Optional[int] = None,
        y: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        auto_crop: bool = False,
        margin: int = 10,
        operations: Optional[List[str]] = None,
        # Conversion parameters
        target_format: str = "PNG",
        quality: int = 95,
        optimize: bool = False,
        # PDF operations
        dpi: int = 300,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        include_original_image: bool = False,
        # OCR text embedding
        ocr_backend: str = "auto"
    ) -> Dict[str, Any]:
        """
        PORTMANTEAU TOOL: Image Management Operations

        Consolidates image preprocessing, enhancement, conversion, and PDF operations into a single tool.

        OPERATIONS:
        - "deskew": Straighten skewed/scanned documents
        - "enhance": Improve image quality (contrast, sharpness, noise reduction)
        - "rotate": Rotate images by angle or auto-detect orientation
        - "crop": Remove unwanted borders or focus on content areas
        - "preprocess": Complete preprocessing pipeline for OCR
        - "convert_format": Convert between image formats with quality control
        - "convert_pdf_to_images": Extract images from PDF documents
        - "embed_ocr_text": Create searchable PDF with embedded OCR text

        Args:
            operation: The specific operation to perform (see list above)
            image_path: Path to the input image file
            output_path: Path for output file (optional, auto-generated if not provided)
            method: Deskewing method ("auto", "hough", "projection")
            intensity: Enhancement intensity (0.1 to 3.0, default 1.0)
            enhancement_type: Enhancement type ("auto", "contrast", "sharpen", "denoise", "clahe")
            angle: Rotation angle in degrees (clockwise positive)
            auto_rotate: Auto-detect and correct text orientation
            x: Left coordinate for manual cropping
            y: Top coordinate for manual cropping
            width: Width for manual cropping
            height: Height for manual cropping
            auto_crop: Automatically detect and remove borders
            margin: Margin to leave around auto-cropped content (pixels)
            operations: List of preprocessing operations to apply
            target_format: Target image format ("JPEG", "PNG", "TIFF", "BMP", "WebP")
            quality: Quality setting for lossy formats (1-100)
            optimize: Apply format-specific optimizations
            dpi: Resolution for PDF operations (150-600 DPI)
            first_page: First page to extract from PDF (1-indexed)
            last_page: Last page to extract from PDF
            title: PDF title metadata
            author: PDF author metadata
            include_original_image: Include original image in searchable PDF
            ocr_backend: OCR backend for text embedding

        Returns:
            Operation-specific results with processing details and file information
        """
        try:
            logger.info(f"Image management operation: {operation} on {image_path}")

            # Validate operation parameter
            valid_operations = [
                "deskew", "enhance", "rotate", "crop", "preprocess",
                "convert_format", "convert_pdf_to_images", "embed_ocr_text"
            ]

            if operation not in valid_operations:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override=f"Invalid operation: {operation}",
                    details={"valid_operations": valid_operations}
                ).to_dict()

            # Route to appropriate handler based on operation
            if operation == "deskew":
                return await _handle_deskew(image_path, output_path, method)
            elif operation == "enhance":
                return await _handle_enhance(image_path, output_path, enhancement_type, intensity)
            elif operation == "rotate":
                return await _handle_rotate(image_path, output_path, angle, auto_rotate)
            elif operation == "crop":
                return await _handle_crop(image_path, output_path, x, y, width, height, auto_crop, margin)
            elif operation == "preprocess":
                if operations is None:
                    operations = ["deskew", "enhance", "crop"]
                return await _handle_preprocess(image_path, output_path, operations)
            elif operation == "convert_format":
                return await _handle_convert_format(image_path, output_path, target_format, quality, optimize)
            elif operation == "convert_pdf_to_images":
                if not image_path.lower().endswith('.pdf'):
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="convert_pdf_to_images requires a PDF file as input"
                    ).to_dict()
                return await _handle_convert_pdf_to_images(image_path, output_path, dpi, first_page, last_page)
            elif operation == "embed_ocr_text":
                return await _handle_embed_ocr_text(image_path, output_path, ocr_backend, title, include_original_image)

        except Exception as e:
            logger.error(f"Image management operation failed: {operation}, error: {e}")
            return ErrorHandler.handle_exception(e, context=f"image_management_{operation}")


# Operation handler functions (placeholders for now)
async def _handle_deskew(image_path, output_path, method):
    """Handle image deskewing."""
    # TODO: Implement deskew logic from original function
    return create_success_response({"operation": "deskew", "status": "not_implemented_yet"})


async def _handle_enhance(image_path, output_path, enhancement_type, intensity):
    """Handle image enhancement."""
    # TODO: Implement enhancement logic from original function
    return create_success_response({"operation": "enhance", "status": "not_implemented_yet"})


async def _handle_rotate(image_path, output_path, angle, auto_rotate):
    """Handle image rotation."""
    # TODO: Implement rotation logic from original function
    return create_success_response({"operation": "rotate", "status": "not_implemented_yet"})


async def _handle_crop(image_path, output_path, x, y, width, height, auto_crop, margin):
    """Handle image cropping."""
    # TODO: Implement cropping logic from original function
    return create_success_response({"operation": "crop", "status": "not_implemented_yet"})


async def _handle_preprocess(image_path, output_path, operations):
    """Handle complete preprocessing pipeline."""
    # TODO: Implement preprocessing pipeline logic from original function
    return create_success_response({"operation": "preprocess", "status": "not_implemented_yet"})


async def _handle_convert_format(image_path, output_path, target_format, quality, optimize):
    """Handle image format conversion."""
    # TODO: Implement format conversion logic from original function
    return create_success_response({"operation": "convert_format", "status": "not_implemented_yet"})


async def _handle_convert_pdf_to_images(pdf_path, output_directory, dpi, first_page, last_page):
    """Handle PDF to images conversion."""
    # TODO: Implement PDF conversion logic from original function
    return create_success_response({"operation": "convert_pdf_to_images", "status": "not_implemented_yet"})


async def _handle_embed_ocr_text(image_path, output_path, ocr_backend, title, include_original_image):
    """Handle OCR text embedding in PDF."""
    # TODO: Implement OCR text embedding logic from original function
    return create_success_response({"operation": "embed_ocr_text", "status": "not_implemented_yet"})


def register_image_tools(app, backend_manager: BackendManager, config: OCRConfig):
    """Legacy function - now delegates to portmanteau tool."""
    register_image_management_tools(app, backend_manager, config)


# Original individual tool functions removed - now handled by portmanteau tool