"""
Core Document Processor for OCR-MCP

Handles single document and batch processing logic, coordinating
backends and image preprocessing.
"""

import asyncio
import logging
import os
import time
from typing import Any

from ..core.backend_manager import BackendManager
from ..core.config import OCRConfig
from ..core.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


async def process_document(
    source_path: str,
    backend: str = "auto",
    mode: str = "text",
    enhance: bool = True,
    region: list[int] | None = None,
    backend_manager: BackendManager | None = None,
    config: OCRConfig | None = None,
) -> dict[str, Any]:
    """
    Backend handler for process_document. See ocr_tools.document_processing for MCP tool docstring.

    Args:
    - source_path (str, required): Path to the document.
    - backend (str): OCR backend. Default: auto.
    - mode (str): OCR mode. Default: text.
    - enhance (bool): Apply image enhancement. Default: True.
    - region (list[int] | None): [x, y, w, h] region of interest.
    - backend_manager: Injected BackendManager.
    - config: Injected OCRConfig.

    Returns:
    FastMCP 3.1 dialogic response: success, operation, result or error,
    recommendations, next_steps, recovery_options (on error), related_operations.
    """
    logger.info(f"Processing document: {source_path} (backend: {backend}, mode: {mode})")

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

        start_time = time.time()

        # Process with backend manager
        result = await backend_manager.process_with_backend(
            backend_name=backend, image_path=source_path, mode=mode, region=region
        )

        execution_time = time.time() - start_time

        # Enhance with conversational response elements
        if result.get("success", False):
            # Add conversational elements for successful processing
            backend_used = result.get("backend_used", backend)

            # Generate backend recommendations based on result quality
            confidence = result.get("confidence", 0.0)
            recommendations = []

            if confidence > 0.9:
                recommendations.append(
                    "High confidence result - this backend works well for your document"
                )
            elif confidence > 0.7:
                recommendations.append(
                    "Good confidence - consider trying other backends for comparison"
                )
                recommendations.append("Use assess_quality operation for detailed analysis")
            else:
                recommendations.append(
                    "Low confidence - try different backends or image preprocessing"
                )
                recommendations.append(
                    "Use image_management(operation='preprocess') to enhance image quality"
                )

            # Add next steps based on content
            text_content = result.get("text", "")
            next_steps = []

            if "table" in text_content.lower() or result.get("tables_detected", False):
                next_steps.append(
                    "document_processing(operation='extract_tables') - Extract structured table data"
                )
            if result.get("forms_detected", False):
                next_steps.append(
                    "document_processing(operation='detect_forms') - Analyze form fields"
                )
            if len(text_content.split()) > 100:
                next_steps.append(
                    "document_processing(operation='analyze_layout') - Get document structure analysis"
                )

            # Add timing and quality metrics
            enhanced_result = {
                "success": True,
                "operation": "process_document",
                "backend_used": backend_used,
                "backend": backend_used,
                "text": text_content,
                "execution_time": round(execution_time, 2),
                "confidence_score": confidence,
                "text_length": len(text_content),
                "word_count": len(text_content.split()),
                "language_detected": result.get("language", "unknown"),
                "result": result,
                "recommendations": recommendations,
                "next_steps": next_steps
                if next_steps
                else ["document_processing(operation='assess_quality') - Validate OCR accuracy"],
                "related_operations": [
                    "document_processing(operation='assess_quality')",
                    "document_processing(operation='analyze_layout')",
                    "image_management(operation='convert')",
                ],
            }

            return enhanced_result
        else:
            # Enhance error responses with recovery options
            error_msg = result.get("error", "Unknown error")
            enhanced_result = {
                "success": False,
                "operation": "process_document",
                "error": error_msg,
                "execution_time": round(execution_time, 2),
                "recovery_options": [
                    "Try a different backend: backend='tesseract' or backend='easyocr'",
                    "Use image preprocessing: image_management(operation='preprocess')",
                    "Check file format and try conversion: image_management(operation='convert')",
                    "Use batch processing for multiple files: document_processing(operation='process_batch')",
                ],
                "troubleshooting_steps": [
                    "Verify file exists and is readable",
                    "Check if file is a supported format (PNG, JPG, PDF, TIFF)",
                    "Try with enhance_image=False if preprocessing fails",
                    "Use scanner_operations if document needs scanning first",
                ],
                "related_operations": [
                    "image_management(operation='preprocess')",
                    "document_processing(operation='assess_quality')",
                    "scanner_operations(operation='list_scanners')",
                ],
            }

            return enhanced_result

    except Exception as e:
        return ErrorHandler.handle_exception(e, context=f"process_document_{source_path}")


async def process_batch(
    source_dir: str,
    backend: str = "auto",
    mode: str = "text",
    max_concurrent: int = 4,
    backend_manager: BackendManager | None = None,
    config: OCRConfig | None = None,
) -> dict[str, Any]:
    """
    Backend handler for process_batch. See ocr_tools.document_processing for MCP tool docstring.

    Args:
    - source_dir (str, required): Directory containing documents.
    - backend (str): OCR backend. Default: auto.
    - mode (str): OCR mode. Default: text.
    - max_concurrent (int): Parallel limit. Default: 4.
    - backend_manager: Injected BackendManager.
    - config: Injected OCRConfig.

    Returns:
    FastMCP 3.1 dialogic response: success, operation, result or error,
    recommendations, next_steps, recovery_options (on error), related_operations.
    """
    logger.info(f"Processing batch in: {source_dir}")

    if not backend_manager:
        return ErrorHandler.create_error(
            "INTERNAL_ERROR", "Backend manager not initialized"
        ).to_dict()

    try:
        start_time = time.time()

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

        # Calculate batch statistics
        total_words = sum(r.get("result", {}).get("word_count", 0) for r in processed)
        avg_confidence = (
            sum(r.get("result", {}).get("confidence_score", 0) for r in processed) / len(processed)
            if processed
            else 0
        )
        execution_time = time.time() - start_time

        # Generate conversational recommendations
        recommendations = []
        next_steps = []

        if len(processed) > 0:
            success_rate = len(processed) / len(files)
            if success_rate > 0.9:
                recommendations.append(
                    "High success rate - your batch processing setup is working well"
                )
            elif success_rate > 0.7:
                recommendations.append(
                    "Good success rate - consider optimizing failed documents individually"
                )
            else:
                recommendations.append(
                    "Low success rate - focus on preprocessing and backend selection"
                )

            if avg_confidence > 0.8:
                recommendations.append("High average confidence - results are reliable")
            elif avg_confidence > 0.6:
                recommendations.append(
                    "Moderate confidence - consider quality assessment on important documents"
                )

            # Suggest next steps based on results
            if total_words > 1000:
                next_steps.append(
                    "workflow_management(operation='create_processing_pipeline') - Create automated workflow"
                )
            if len(failed) > 0:
                next_steps.append(
                    "document_processing(operation='assess_quality') - Analyze failed documents"
                )
            next_steps.append(
                "workflow_management(operation='process_batch_intelligent') - Use AI-powered batch processing"
            )

        # Enhanced conversational response
        enhanced_result = {
            "success": True,
            "operation": "process_batch",
            "execution_time": round(execution_time, 2),
            "total_count": len(files),
            "processed_count": len(processed),
            "failed_count": len(failed),
            "success_rate": round(len(processed) / len(files), 2) if files else 0,
            "average_confidence": round(avg_confidence, 2),
            "total_words_extracted": total_words,
            "processing_rate": round(len(files) / execution_time, 2)
            if execution_time > 0
            else 0,  # files per second
            "results": results,
            "recommendations": recommendations,
            "next_steps": next_steps
            if next_steps
            else ["document_processing(operation='assess_quality') - Quality assessment"],
            "related_operations": [
                "document_processing(operation='assess_quality')",
                "workflow_management(operation='create_processing_pipeline')",
                "workflow_management(operation='process_batch_intelligent')",
            ],
            "performance_metrics": {
                "files_per_second": round(len(files) / execution_time, 2),
                "average_processing_time": round(execution_time / len(files), 2) if files else 0,
                "memory_usage": "Check server logs for detailed memory stats",
            },
        }

        return enhanced_result

    except Exception as e:
        return ErrorHandler.handle_exception(e, context=f"process_batch_{source_dir}")
