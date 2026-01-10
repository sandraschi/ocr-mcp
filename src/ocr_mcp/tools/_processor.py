"""
Core Document Processor for OCR-MCP

Handles single document and batch processing logic, coordinating
backends and image preprocessing.
"""

import logging
import os
from typing import Dict, Any, Optional, List
import asyncio

from ..core.backend_manager import BackendManager
from ..core.config import OCRConfig
from ..core.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


async def process_document(
    source_path: str,
    backend: str = "auto",
    mode: str = "text",
    enhance: bool = True,
    region: Optional[List[int]] = None,
    backend_manager: Optional[BackendManager] = None,
    config: Optional[OCRConfig] = None,
) -> Dict[str, Any]:
    """
    Process a single document image or PDF.

    Args:
        source_path: Path to the document
        backend: OCR backend to use
        mode: OCR mode (text, document, layout, etc.)
        enhance: Whether to apply image enhancement
        region: Optional [x, y, w, h] region of interest
        backend_manager: Dependency injected backend manager
        config: Dependency injected OCR configuration

    Returns:
        OCR extraction result
    """
    logger.info(
        f"Processing document: {source_path} (backend: {backend}, mode: {mode})"
    )

    if not backend_manager:
        return ErrorHandler.create_error(
            "INTERNAL_ERROR", "Backend manager not initialized"
        ).to_dict()

    try:
        if not os.path.exists(source_path):
            return ErrorHandler.create_error(
                "FILE_NOT_FOUND", f"File not found: {source_path}"
            ).to_dict()

        # Handle backend selection
        if backend == "auto":
            backend = config.default_backend if config else "tesseract"

        # Process with backend manager
        result = await backend_manager.process_with_backend(
            backend_name=backend, image_path=source_path, mode=mode, region=region
        )

        return result

    except Exception as e:
        return ErrorHandler.handle_exception(
            e, context=f"process_document_{source_path}"
        )


async def process_batch(
    source_dir: str,
    backend: str = "auto",
    mode: str = "text",
    max_concurrent: int = 4,
    backend_manager: Optional[BackendManager] = None,
    config: Optional[OCRConfig] = None,
) -> Dict[str, Any]:
    """
    Process all documents in a directory.

    Args:
        source_dir: Directory containing documents
        backend: OCR backend to use
        mode: OCR mode
        max_concurrent: Maximum number of concurrent processing tasks
        backend_manager: Dependency injected backend manager
        config: Dependency injected OCR configuration

    Returns:
        Batch processing summary and results
    """
    logger.info(f"Processing batch in: {source_dir}")

    if not backend_manager:
        return ErrorHandler.create_error(
            "INTERNAL_ERROR", "Backend manager not initialized"
        ).to_dict()

    try:
        if not os.path.isdir(source_dir):
            return ErrorHandler.create_error(
                "FILE_NOT_FOUND", f"Directory not found: {source_dir}"
            ).to_dict()

        # Find all images
        supported_exts = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".pdf"}
        files = [
            os.path.join(source_dir, f)
            for f in os.listdir(source_dir)
            if os.path.splitext(f)[1].lower() in supported_exts
        ]

        if not files:
            return {
                "success": True,
                "processed_count": 0,
                "message": "No supported files found in directory",
                "results": [],
            }

        # Process in parallel with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent)

        async def sem_process(file_path):
            async with semaphore:
                return await process_document(
                    source_path=file_path,
                    backend=backend,
                    mode=mode,
                    backend_manager=backend_manager,
                    config=config,
                )

        tasks = [sem_process(f) for f in files]
        results = await asyncio.gather(*tasks)

        # Summarize results
        processed = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        return {
            "success": True,
            "total_count": len(files),
            "processed_count": len(processed),
            "failed_count": len(failed),
            "results": results,
        }

    except Exception as e:
        return ErrorHandler.handle_exception(e, context=f"process_batch_{source_dir}")
