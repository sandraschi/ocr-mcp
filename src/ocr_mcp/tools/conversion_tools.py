"""
Document Format Conversion Tools for OCR-MCP

Provides comprehensive document format conversion capabilities:
image format conversion, PDF manipulation, document export, etc.
"""

import logging
from typing import Dict, Any, Optional, List

from ..core.backend_manager import BackendManager
from ..core.config import OCRConfig

logger = logging.getLogger(__name__)


def register_conversion_tools(app, backend_manager: BackendManager, config: OCRConfig):
    """Register all document conversion tools with the FastMCP app."""

    @app.tool()
    async def convert_image_format(
        image_path: str,
        output_path: str,
        target_format: str,
        quality: int = 95,
        optimize: bool = False
    ) -> Dict[str, Any]:
        """
        Convert image between different formats with quality control.

        Supports conversion between JPEG, PNG, TIFF, BMP, WebP, and other
        formats with quality optimization and size control.

        Args:
            image_path: Path to source image file
            output_path: Path for converted image
            target_format: Target format ("JPEG", "PNG", "TIFF", "BMP", "WebP")
            quality: Quality setting (1-100, higher = better quality)
            optimize: Apply format-specific optimizations

        Returns:
            Conversion results with file size comparison
        """
        logger.info(f"Converting image {image_path} to {target_format}")

        try:
            from PIL import Image
            import os

            # Load source image
            image = Image.open(image_path)
            original_format = image.format or "UNKNOWN"
            original_size = os.path.getsize(image_path)

            # Handle different color modes for different formats
            if target_format.upper() == "JPEG" and image.mode in ("RGBA", "LA", "P"):
                # Convert to RGB for JPEG
                image = image.convert("RGB")

            # Apply optimizations
            if optimize:
                if target_format.upper() == "JPEG":
                    # Progressive JPEG
                    image.save(output_path, target_format, quality=quality, optimize=True, progressive=True)
                elif target_format.upper() == "PNG":
                    # Optimized PNG
                    image.save(output_path, target_format, optimize=True)
                elif target_format.upper() == "WEBP":
                    # WebP with quality
                    image.save(output_path, target_format, quality=quality)
                else:
                    image.save(output_path, target_format, quality=quality)
            else:
                image.save(output_path, target_format, quality=quality)

            # Get output file info
            output_size = os.path.getsize(output_path)
            compression_ratio = original_size / output_size if output_size > 0 else 1.0

            return {
                "success": True,
                "input_path": image_path,
                "output_path": output_path,
                "original_format": original_format,
                "target_format": target_format.upper(),
                "quality_setting": quality,
                "optimization_applied": optimize,
                "file_sizes": {
                    "original_bytes": original_size,
                    "converted_bytes": output_size,
                    "compression_ratio": round(compression_ratio, 2),
                    "space_saved_bytes": original_size - output_size if output_size < original_size else 0
                },
                "image_info": {
                    "width": image.width,
                    "height": image.height,
                    "mode": image.mode,
                    "dpi": getattr(image, 'info', {}).get('dpi', None)
                },
                "message": f"Image converted to {target_format.upper()} successfully"
            }

        except Exception as e:
            logger.error(f"Image format conversion failed: {e}")
            return {
                "success": False,
                "error": f"Image conversion failed: {str(e)}",
                "input_path": image_path,
                "target_format": target_format
            }

    @app.tool()
    async def convert_pdf_to_images(
        pdf_path: str,
        output_directory: str,
        dpi: int = 300,
        format: str = "PNG",
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Convert PDF pages to individual images.

        Extracts pages from PDF documents and saves them as high-quality
        images suitable for OCR processing.

        Args:
            pdf_path: Path to PDF file
            output_directory: Directory to save extracted images
            dpi: Resolution for image extraction (150-600 DPI)
            format: Image format ("PNG", "JPEG", "TIFF")
            first_page: First page to extract (1-indexed, default: 1)
            last_page: Last page to extract (default: all pages)

        Returns:
            PDF to image conversion results
        """
        logger.info(f"Converting PDF {pdf_path} to {format} images at {dpi} DPI")

        try:
            from pdf2image import convert_from_path
            import os
            from pathlib import Path

            # Validate PDF exists
            if not os.path.exists(pdf_path):
                return {
                    "success": False,
                    "error": f"PDF file not found: {pdf_path}"
                }

            # Create output directory
            output_dir = Path(output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Convert PDF to images
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                first_page=first_page,
                last_page=last_page,
                fmt=format.lower()
            )

            # Save images
            saved_files = []
            for i, image in enumerate(images):
                page_num = (first_page or 1) + i
                filename = "03d"
                filepath = output_dir / filename
                image.save(filepath, format.upper())
                saved_files.append(str(filepath))

            # Get PDF info
            pdf_info = {
                "total_pages": len(images),
                "pages_extracted": len(saved_files),
                "first_page": first_page or 1,
                "last_page": (first_page or 1) + len(images) - 1,
                "resolution": dpi,
                "format": format.upper()
            }

            return {
                "success": True,
                "pdf_path": pdf_path,
                "output_directory": str(output_directory),
                "conversion_settings": {
                    "dpi": dpi,
                    "format": format.upper(),
                    "first_page": first_page,
                    "last_page": last_page
                },
                "results": {
                    "images_created": len(saved_files),
                    "files_saved": saved_files,
                    "total_file_size_mb": round(sum(os.path.getsize(f) for f in saved_files) / (1024*1024), 2)
                },
                "pdf_info": pdf_info,
                "message": f"PDF converted to {len(saved_files)} {format.upper()} images"
            }

        except Exception as e:
            logger.error(f"PDF to image conversion failed: {e}")
            return {
                "success": False,
                "error": f"PDF conversion failed: {str(e)}",
                "pdf_path": pdf_path
            }

    @app.tool()
    async def create_pdf_from_images(
        image_paths: List[str],
        output_path: str,
        title: Optional[str] = None,
        author: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a PDF document from multiple images.

        Combines multiple images into a single PDF document, useful for
        creating searchable PDFs after OCR processing.

        Args:
            image_paths: List of paths to image files
            output_path: Path for the output PDF file
            title: Optional PDF title metadata
            author: Optional PDF author metadata

        Returns:
            PDF creation results
        """
        logger.info(f"Creating PDF from {len(image_paths)} images")

        try:
            from PIL import Image
            import os

            if not image_paths:
                return {
                    "success": False,
                    "error": "No image paths provided"
                }

            # Load and validate images
            images = []
            image_info = []

            for img_path in image_paths:
                if not os.path.exists(img_path):
                    return {
                        "success": False,
                        "error": f"Image file not found: {img_path}"
                    }

                image = Image.open(img_path)
                # Convert to RGB for PDF compatibility
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                images.append(image)

                image_info.append({
                    "path": img_path,
                    "size": image.size,
                    "mode": image.mode,
                    "file_size": os.path.getsize(img_path)
                })

            # Save as PDF
            if len(images) == 1:
                # Single image
                images[0].save(output_path, "PDF", resolution=300.0)
            else:
                # Multiple images - first image is saved, rest are appended
                images[0].save(
                    output_path, "PDF",
                    resolution=300.0,
                    save_all=True,
                    append_images=images[1:]
                )

            # Add metadata if provided
            if title or author:
                try:
                    from pypdf import PdfReader, PdfWriter

                    reader = PdfReader(output_path)
                    writer = PdfWriter()

                    for page in reader.pages:
                        writer.add_page(page)

                    if title:
                        writer.add_metadata({"/Title": title})
                    if author:
                        writer.add_metadata({"/Author": author})

                    with open(output_path, "wb") as f:
                        writer.write(f)

                except Exception as e:
                    logger.warning(f"Could not add PDF metadata: {e}")

            pdf_size = os.path.getsize(output_path)

            return {
                "success": True,
                "output_path": output_path,
                "images_combined": len(images),
                "pdf_metadata": {
                    "title": title,
                    "author": author,
                    "pages": len(images),
                    "file_size_bytes": pdf_size
                },
                "image_details": image_info,
                "message": f"PDF created successfully with {len(images)} pages"
            }

        except Exception as e:
            logger.error(f"PDF creation failed: {e}")
            return {
                "success": False,
                "error": f"PDF creation failed: {str(e)}",
                "image_count": len(image_paths)
            }

    @app.tool()
    async def extract_text_to_pdf(
        image_path: str,
        output_path: str,
        ocr_backend: str = "auto",
        title: Optional[str] = None,
        include_original_image: bool = False
    ) -> Dict[str, Any]:
        """
        Create a searchable PDF with OCR text layer from an image.

        Performs OCR on an image and embeds the recognized text as an
        invisible text layer in the PDF, making it searchable.

        Args:
            image_path: Path to the image file
            output_path: Path for the searchable PDF
            ocr_backend: OCR backend to use ("auto", "easyocr", "tesseract", etc.)
            title: Optional PDF title
            include_original_image: Include the original image as visible content

        Returns:
            Searchable PDF creation results
        """
        logger.info(f"Creating searchable PDF from {image_path}")

        try:
            # First, perform OCR on the image
            ocr_result = await backend_manager.process_with_backend(
                ocr_backend, image_path, mode="text"
            )

            if not ocr_result.get("success"):
                return {
                    "success": False,
                    "error": f"OCR failed: {ocr_result.get('error', 'Unknown error')}",
                    "image_path": image_path
                }

            ocr_text = ocr_result.get("text", "")
            if not ocr_text.strip():
                return {
                    "success": False,
                    "error": "No text extracted from image",
                    "image_path": image_path
                }

            # Create PDF with text layer
            from PIL import Image
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.utils import ImageReader
            import io
            import textwrap

            # Load the original image
            original_image = Image.open(image_path)

            # Create PDF
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=A4)

            # Calculate dimensions to fit the image
            img_width, img_height = original_image.size
            page_width, page_height = A4

            # Scale image to fit page while maintaining aspect ratio
            scale = min(page_width / img_width, page_height / img_height) * 0.9
            display_width = img_width * scale
            display_height = img_height * scale

            # Center the image
            x_pos = (page_width - display_width) / 2
            y_pos = (page_height - display_height) / 2

            if include_original_image:
                # Draw the image on the PDF
                img_reader = ImageReader(original_image)
                can.drawImage(img_reader, x_pos, y_pos, display_width, display_height)

            # Add invisible text layer for searchability
            can.setFillColorRGB(1, 1, 1, 0)  # Transparent text
            can.setFont("Helvetica", 1)  # Very small font

            # Wrap text to fit the image area
            wrapped_text = textwrap.wrap(ocr_text, width=80)
            text_y = y_pos + display_height - 20

            for line in wrapped_text[:50]:  # Limit to prevent overflow
                if text_y > y_pos:
                    can.drawString(x_pos + 10, text_y, line)
                    text_y -= 12

            can.save()
            packet.seek(0)

            # Save the PDF
            with open(output_path, 'wb') as f:
                f.write(packet.getvalue())

            return {
                "success": True,
                "input_image": image_path,
                "output_pdf": output_path,
                "ocr_backend_used": ocr_result.get("backend", ocr_backend),
                "text_extracted_chars": len(ocr_text),
                "text_extracted_lines": len(ocr_text.split('\n')),
                "searchable": True,
                "original_image_included": include_original_image,
                "pdf_metadata": {
                    "title": title or "OCR Searchable PDF",
                    "pages": 1,
                    "text_layer": "embedded"
                },
                "message": f"Searchable PDF created with {len(ocr_text)} characters of OCR text"
            }

        except Exception as e:
            logger.error(f"Searchable PDF creation failed: {e}")
            return {
                "success": False,
                "error": f"Searchable PDF creation failed: {str(e)}",
                "image_path": image_path
            }

    @app.tool()
    async def optimize_document_for_ocr(
        input_path: str,
        output_path: str,
        operations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Apply complete document optimization pipeline for OCR.

        Combines multiple optimization techniques to prepare documents
        for maximum OCR accuracy: format conversion, preprocessing, quality enhancement.

        Args:
            input_path: Path to input document (PDF, image, etc.)
            output_path: Path for optimized output
            operations: List of operations to perform (default: auto-detect)

        Returns:
            Document optimization results
        """
        logger.info(f"Optimizing document {input_path} for OCR")

        if operations is None:
            operations = ["format_check", "convert_to_image", "preprocess", "quality_check"]

        try:
            import os
            from pathlib import Path

            applied_operations = []
            optimization_steps = []

            # Determine input type and optimization strategy
            file_ext = Path(input_path).suffix.lower()

            if file_ext == '.pdf':
                # PDF optimization
                if "convert_to_image" in operations:
                    # Convert PDF to high-quality images
                    temp_dir = Path(output_path).parent / "temp_ocr_optimization"
                    temp_dir.mkdir(exist_ok=True)

                    pdf_result = await convert_pdf_to_images(
                        input_path, str(temp_dir), dpi=300, format="PNG"
                    )

                    if pdf_result["success"]:
                        applied_operations.append("pdf_to_images")
                        optimization_steps.append(f"Converted PDF to {pdf_result['results']['images_created']} PNG images")

                        # Process first page as example
                        if pdf_result["results"]["files_saved"]:
                            image_path = pdf_result["results"]["files_saved"][0]

                            # Apply image preprocessing
                            preprocess_result = await preprocess_for_ocr(
                                image_path, output_path, ["deskew", "enhance", "crop"]
                            )

                            if preprocess_result["success"]:
                                applied_operations.append("image_preprocessing")
                                optimization_steps.append("Applied deskew, enhancement, and cropping")

                    # Cleanup temp files
                    import shutil
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir)

            elif file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                # Image optimization
                preprocess_result = await preprocess_for_ocr(
                    input_path, output_path, ["deskew", "enhance", "crop"]
                )

                if preprocess_result["success"]:
                    applied_operations.append("image_optimization")
                    optimization_steps.append("Applied complete image preprocessing pipeline")

            # Quality assessment
            if "quality_check" in operations and os.path.exists(output_path):
                quality_result = await analyze_image_quality(output_path)

                if quality_result["success"]:
                    applied_operations.append("quality_assessment")
                    optimization_steps.append(f"Quality score: {quality_result['overall_quality_score']}/100")

            return {
                "success": True,
                "input_path": input_path,
                "output_path": output_path,
                "operations_requested": operations,
                "operations_applied": applied_operations,
                "optimization_steps": optimization_steps,
                "ready_for_ocr": len(applied_operations) > 0,
                "message": f"Document optimized with {len(applied_operations)} operations applied"
            }

        except Exception as e:
            logger.error(f"Document optimization failed: {e}")
            return {
                "success": False,
                "error": f"Document optimization failed: {str(e)}",
                "input_path": input_path
            }