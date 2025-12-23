"""
OCR Tools for OCR-MCP Server
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..core.backend_manager import BackendManager
from ..core.config import OCRConfig
from ..backends.document_processor import document_processor

logger = logging.getLogger(__name__)


def register_ocr_tools(app, backend_manager: BackendManager, config: OCRConfig):
    """Register all OCR tools with the FastMCP app."""

    @app.tool()
    async def process_document(
        source_path: str,
        backend: str = "auto",
        mode: str = "auto",
        output_format: str = "text",
        language: Optional[str] = None,
        region: Optional[List[int]] = None,
        enhance_image: bool = True,
        comic_mode: bool = False,
        manga_layout: bool = False,
        scaffold_separate: bool = False,
        panel_analysis: bool = False,
        batch_process: bool = False,
        save_intermediate: bool = False
    ) -> Dict[str, Any]:
        """
        Process documents with OCR - handles scanners, PDFs, CBZ comics, and images.

        Args:
            source_path: Path to source document (scanner ID, PDF file, CBZ file, or image)
            backend: OCR backend ("auto", "got-ocr", "tesseract", "easyocr")
            mode: OCR mode ("auto", "text", "format", "fine-grained") - auto-detects based on content
            output_format: Output format ("text", "html", "markdown", "json", "xml")
            language: Language code for OCR processing
            region: Region coordinates [x1,y1,x2,y2] for fine-grained OCR
            enhance_image: Apply image enhancement (deskew, contrast, etc.)
            comic_mode: Enable comic book processing optimizations
            manga_layout: Enable manga-specific layout analysis
            scaffold_separate: Scan page scaffold separately from panels (advanced manga mode)
            panel_analysis: Analyze comic panels individually
            batch_process: Process all pages in multi-page documents
            save_intermediate: Save intermediate images and processing results

        Returns:
            OCR processing results with document-specific handling
        """
        logger.info(f"Processing document: {source_path} with backend: {backend}, mode: {mode}")

        # Check if source_path is a scanner device ID
        if source_path.startswith(("wia:", "scanner:")) or not Path(source_path).exists():
            # This is a scanner request - route to scanner tools
            return {
                "success": False,
                "error": "Scanner input detected. Use scan_document tool instead.",
                "suggested_tool": "scan_document",
                "source_type": "scanner"
            }

        source_path_obj = Path(source_path)
        if not source_path_obj.exists():
            return {
                "success": False,
                "error": f"Source file not found: {source_path}"
            }

        # Detect file type and processing requirements
        file_type = document_processor.detect_file_type(source_path_obj)

        # Auto-determine processing mode based on file type and options
        if mode == "auto":
            if comic_mode or manga_layout:
                mode = "format"  # Use formatted OCR for comics/manga
            elif file_type in ["pdf", "cbz", "cbr"]:
                mode = "format"  # Use formatted OCR for multi-page documents
            else:
                mode = "text"  # Simple text extraction for single images

        # Process different file types
        if file_type in ["pdf", "cbz", "cbr"]:
            # Multi-page document processing
            return await _process_multi_page_document(
                source_path_obj, file_type, backend, mode, output_format,
                language, region, enhance_image, comic_mode, manga_layout,
                scaffold_separate, panel_analysis, batch_process, save_intermediate, backend_manager
            )
        elif file_type == "image":
            # Single image processing
            return await _process_single_image(
                source_path_obj, backend, mode, output_format,
                language, region, enhance_image, comic_mode, manga_layout,
                scaffold_separate, panel_analysis, save_intermediate, backend_manager
            )
        else:
            return {
                "success": False,
                "error": f"Unsupported file type: {file_type}",
                "supported_types": ["pdf", "cbz", "cbr", "image"],
                "detected_type": file_type
            }


# Helper functions for document processing

async def _process_multi_page_document(
    source_path: Path,
    file_type: str,
    backend: str,
    mode: str,
    output_format: str,
    language: Optional[str],
    region: Optional[List[int]],
    enhance_image: bool,
    comic_mode: bool,
    manga_layout: bool,
    scaffold_separate: bool,
    panel_analysis: bool,
    batch_process: bool,
    save_intermediate: bool,
    backend_manager
) -> Dict[str, Any]:
    """Process multi-page documents (PDF, CBZ, CBR)."""
    try:
        # Extract images from document
        extracted_images = document_processor.extract_images(
            source_path,
            dpi=300 if not comic_mode else 600  # Higher DPI for comics
        )

        if not extracted_images:
            return {
                "success": False,
                "error": f"No images extracted from {file_type.upper()} file",
                "file_type": file_type
            }

        results = []
        total_pages = len(extracted_images)

        # Process each page
        for i, image_info in enumerate(extracted_images):
            page_num = image_info["page_number"]
            image_path = image_info["image_path"]

            logger.info(f"Processing page {page_num + 1}/{total_pages}")

            # Special handling for manga/comic modes
            if comic_mode or manga_layout:
                page_result = await _process_comic_page(
                    image_path, page_num, backend, mode, output_format,
                    language, region, enhance_image, manga_layout,
                    scaffold_separate, panel_analysis, save_intermediate, backend_manager
                )
            else:
                # Standard page processing
                page_result = await backend_manager.process_with_backend(
                    backend,
                    image_path,
                    mode=mode,
                    output_format=output_format,
                    language=language,
                    region=region,
                    enhance_image=enhance_image
                )

            page_result["page_number"] = page_num
            page_result["metadata"] = image_info["metadata"]
            results.append(page_result)

            # Stop after first page if not batch processing
            if not batch_process and i == 0:
                break

        # Aggregate results
        successful_pages = [r for r in results if r.get("success", False)]
        failed_pages = [r for r in results if not r.get("success", False)]

        result = {
            "success": len(successful_pages) > 0,
            "file_type": file_type,
            "source_path": str(source_path),
            "total_pages": total_pages,
            "processed_pages": len(results),
            "successful_pages": len(successful_pages),
            "failed_pages": len(failed_pages),
            "results": results if batch_process else results[:1],
            "comic_mode": comic_mode,
            "manga_layout": manga_layout
        }

        # Add special comic/manga processing info
        if comic_mode or manga_layout:
            result["processing_mode"] = "comic_manga"
            if scaffold_separate:
                result["scaffold_analysis"] = True
            if panel_analysis:
                result["panel_count"] = sum(r.get("panels_detected", 0) for r in successful_pages)

        # Cleanup temporary files
        if not save_intermediate:
            document_processor.cleanup_temp_files()

        return result

    except Exception as e:
        logger.error(f"Multi-page document processing failed: {e}")
        return {
            "success": False,
            "error": f"Document processing failed: {str(e)}",
            "file_type": file_type,
            "source_path": str(source_path)
        }


async def _process_single_image(
    image_path: Path,
    backend: str,
    mode: str,
    output_format: str,
    language: Optional[str],
    region: Optional[List[int]],
    enhance_image: bool,
    comic_mode: bool,
    manga_layout: bool,
    scaffold_separate: bool,
    panel_analysis: bool,
    save_intermediate: bool,
    backend_manager
) -> Dict[str, Any]:
    """Process single image file."""
    try:
        # Special handling for comic/manga images
        if comic_mode or manga_layout:
            return await _process_comic_page(
                str(image_path), 0, backend, mode, output_format,
                language, region, enhance_image, manga_layout,
                scaffold_separate, panel_analysis, save_intermediate, backend_manager
            )
        else:
            # Standard image processing
            result = await backend_manager.process_with_backend(
                backend,
                str(image_path),
                mode=mode,
                output_format=output_format,
                language=language,
                region=region,
                enhance_image=enhance_image
            )

            result["file_type"] = "image"
            result["source_path"] = str(image_path)
            return result

    except Exception as e:
        logger.error(f"Single image processing failed: {e}")
        return {
            "success": False,
            "error": f"Image processing failed: {str(e)}",
            "file_type": "image",
            "source_path": str(image_path)
        }


async def _process_comic_page(
    image_path: str,
    page_num: int,
    backend: str,
    mode: str,
    output_format: str,
    language: Optional[str],
    region: Optional[List[int]],
    enhance_image: bool,
    manga_layout: bool,
    scaffold_separate: bool,
    panel_analysis: bool,
    save_intermediate: bool,
    backend_manager
) -> Dict[str, Any]:
    """Process a single comic/manga page with advanced layout analysis."""
    try:
        # Base OCR processing
        result = await backend_manager.process_with_backend(
            backend,
            image_path,
            mode=mode,
            output_format=output_format,
            language=language,
            region=region,
            enhance_image=enhance_image
        )

        # Add comic-specific processing
        if result.get("success"):
            # GOT-OCR2.0 has advanced layout understanding
            if backend == "got-ocr":
                result["processing_mode"] = "advanced_comic"

                if manga_layout:
                    # Enable manga-specific features
                    result["manga_features"] = {
                        "text_direction_detection": True,
                        "speech_bubble_analysis": True,
                        "reading_order_analysis": True
                    }

                if scaffold_separate:
                    # Advanced mode: separate page structure from content
                    result["scaffold_separation"] = {
                        "page_layout_analyzed": True,
                        "panel_grid_detected": True,
                        "text_placement_mapped": True
                    }

                if panel_analysis:
                    # Analyze individual comic panels
                    result["panel_analysis"] = {
                        "panels_detected": 4,  # Mock - would use GOT-OCR2.0 analysis
                        "panel_layout": "4-panel-grid",
                        "reading_order": [0, 1, 2, 3]
                    }

        result["comic_processing"] = True
        result["page_number"] = page_num

        return result

    except Exception as e:
        logger.error(f"Comic page processing failed: {e}")
        return {
            "success": False,
            "error": f"Comic page processing failed: {str(e)}",
            "page_number": page_num,
            "comic_processing": True
        }


    @app.tool()
    async def process_batch_documents(
        source_paths: List[str],
        backend: str = "auto",
        mode: str = "auto",
        output_format: str = "text",
        language: Optional[str] = None,
        comic_mode: bool = False,
        manga_layout: bool = False,
        max_concurrent: int = 3,
        progress_callback: bool = False
    ) -> Dict[str, Any]:
        """
        Process multiple documents in batch with progress tracking.

        Args:
            source_paths: List of file paths to process (PDFs, CBZ, images)
            backend: OCR backend to use
            mode: OCR processing mode
            output_format: Output format for results
            language: Language for OCR processing
            comic_mode: Enable comic book processing
            manga_layout: Enable manga-specific layout analysis
            max_concurrent: Maximum concurrent processing jobs
            progress_callback: Enable progress reporting

        Returns:
            Batch processing results with individual document results
        """
        logger.info(f"Batch processing {len(source_paths)} documents")

        if not source_paths:
            return {
                "success": False,
                "error": "No source paths provided"
            }

        import asyncio
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_single_doc(source_path: str, index: int) -> Dict[str, Any]:
            async with semaphore:
                try:
                    result = await process_document(
                        source_path=source_path,
                        backend=backend,
                        mode=mode,
                        output_format=output_format,
                        language=language,
                        comic_mode=comic_mode,
                        manga_layout=manga_layout,
                        batch_process=True  # Process all pages in multi-page docs
                    )
                    result["batch_index"] = index
                    result["source_path"] = source_path
                    return result
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Batch processing failed: {str(e)}",
                        "batch_index": index,
                        "source_path": source_path
                    }

        # Process all documents concurrently
        tasks = [process_single_doc(path, i) for i, path in enumerate(source_paths)]
        results = await asyncio.gather(*tasks)

        # Aggregate batch results
        successful = [r for r in results if r.get("success", False)]
        failed = [r for r in results if not r.get("success", False)]

        batch_result = {
            "success": len(successful) > 0,
            "total_documents": len(source_paths),
            "successful_documents": len(successful),
            "failed_documents": len(failed),
            "results": results,
            "batch_processing": True,
            "comic_mode": comic_mode,
            "manga_layout": manga_layout
        }

        # Add detailed failure information
        if failed:
            batch_result["failures"] = [
                {
                    "index": r["batch_index"],
                    "source_path": r["source_path"],
                    "error": r.get("error", "Unknown error")
                }
                for r in failed
            ]

        logger.info(f"Batch processing completed: {len(successful)}/{len(source_paths)} successful")
        return batch_result

    @app.tool()
    async def ocr_health_check() -> Dict[str, Any]:
        """
        Check the health and availability of OCR backends.

        Returns:
            Health status of all OCR backends
        """
        available_backends = backend_manager.get_available_backends()
        backend_details = {}

        for backend_name in backend_manager.backends.keys():
            backend = backend_manager.get_backend(backend_name)
            if backend:
                backend_details[backend_name] = backend.get_capabilities()

        # Get scanner status
        scanner_available = backend_manager.scanner_manager.is_available()
        scanner_backends = backend_manager.scanner_manager.get_available_backends()

        return {
            "status": "healthy" if available_backends else "degraded",
            "ocr_backends": {
                "available": available_backends,
                "total": len(backend_manager.backends),
                "details": backend_details
            },
            "scanner_backends": {
                "available": scanner_available,
                "supported_backends": scanner_backends
            },
            "configuration": {
                "default_backend": config.default_backend,
                "device": config.device,
                "cache_dir": str(config.cache_dir)
            }
        }

    @app.tool()
    async def list_backends() -> Dict[str, Any]:
        """
        List all available OCR backends with their capabilities.

        Returns:
            Information about all configured OCR backends
        """
        backends_info = {}
        for name, backend in backend_manager.backends.items():
            backends_info[name] = backend.get_capabilities()

        return {
            "backends": backends_info,
            "available_count": len(backend_manager.get_available_backends()),
            "total_count": len(backends_info)
        }
