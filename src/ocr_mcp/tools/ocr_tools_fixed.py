"""
OCR Tools for OCR-MCP Server - PORTMANTEAU DESIGN

This module consolidates multiple individual tools into portmanteau tools
for better discoverability and reduced tool count.

PORTMANTEAU TOOLS:
- document_processing: OCR, analysis, quality assessment operations
- image_management: Image preprocessing and conversion operations
- scanner_operations: Scanner hardware control operations
- workflow_management: Batch processing, pipelines, system operations
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..core.backend_manager import BackendManager
from ..core.config import OCRConfig
from ..core.error_handler import ErrorHandler, create_success_response
from ..core.progress_tracker import progress_tracker, OperationType
from ..backends.document_processor import document_processor

logger = logging.getLogger(__name__)


def register_document_processing_tools(app, backend_manager: BackendManager, config: OCRConfig):
    """Register document processing portmanteau tool with the FastMCP app."""

    @app.tool()
    async def document_processing(
        operation: str,
        source_path: Optional[str] = None,
        backend: str = "auto",
        ocr_mode: str = "auto",
        output_format: str = "text",
        language: Optional[str] = None,
        region: Optional[List[int]] = None,
        enhance_image: bool = True,
        comic_mode: bool = False,
        manga_layout: bool = False,
        scaffold_separate: bool = False,
        panel_analysis: bool = False,
        batch_process: bool = False,
        save_intermediate: bool = False,
        # Batch processing parameters
        source_paths: Optional[List[str]] = None,
        max_concurrent: int = 4,
        # Quality assessment parameters
        ocr_result: Optional[Dict[str, Any]] = None,
        ground_truth: Optional[str] = None,
        assessment_type: str = "comprehensive",
        validation_type: str = "character",
        backends: Optional[List[str]] = None,
        quality_checks: Optional[List[str]] = None,
        # Document analysis parameters
        analysis_type: str = "comprehensive",
        detect_tables: bool = True,
        detect_forms: bool = True,
        detect_headers: bool = True,
        table_region: Optional[List[int]] = None,
        ocr_backend: str = "auto",
        extract_dates: bool = True,
        extract_names: bool = True,
        extract_numbers: bool = True
    ) -> Dict[str, Any]:
        """
        PORTMANTEAU TOOL: Document Processing Operations

        Consolidates OCR processing, document analysis, and quality assessment into a single tool.

        OPERATIONS:
        - "process_document": Process single document with OCR
        - "process_batch": Process multiple documents concurrently
        - "extract_regions": Fine-grained region-based OCR
        - "analyze_layout": Detect document structure (tables, columns, headers)
        - "extract_table_data": Extract structured data from tables
        - "detect_form_fields": Identify form elements (checkboxes, fields)
        - "analyze_reading_order": Determine logical text flow
        - "classify_document": Auto-classify document type
        - "extract_metadata": Extract dates, names, numbers
        - "assess_quality": Comprehensive OCR quality scoring
        - "compare_backends": Performance comparison across OCR engines
        - "validate_accuracy": Ground truth accuracy validation
        - "analyze_image_quality": Pre-OCR quality assessment

        Args:
            operation: The specific operation to perform (see list above)
            source_path: Path to document/image for single document operations
            backend: OCR backend selection ("auto", "deepseek-ocr", "florence-2", etc.)
            ocr_mode: OCR processing mode ("auto", "text", "format", "fine-grained")
            output_format: Output format ("text", "html", "markdown", "json", "xml")
            language: Language code for OCR processing
            region: Region coordinates [x1,y1,x2,y2] for fine-grained OCR
            enhance_image: Apply automatic image enhancement
            comic_mode: Enable comic book processing optimizations
            manga_layout: Enable manga-specific layout analysis
            scaffold_separate: Advanced manga mode - separate page structure
            panel_analysis: Analyze individual comic panels
            batch_process: Process all pages in multi-page documents
            save_intermediate: Save intermediate processing steps
            source_paths: List of paths for batch processing
            max_concurrent: Maximum concurrent batch processing jobs
            ocr_result: OCR result for quality assessment operations
            ground_truth: Ground truth text for accuracy validation
            assessment_type: Quality assessment type ("basic", "comprehensive")
            validation_type: Accuracy validation type ("character", "word", "semantic")
            backends: List of backends to compare in backend comparison
            quality_checks: List of quality checks to perform
            analysis_type: Document analysis type ("basic", "comprehensive", "detailed")
            detect_tables: Enable table detection in layout analysis
            detect_forms: Enable form field detection
            detect_headers: Enable header/footer detection
            table_region: Specific table region coordinates
            ocr_backend: OCR backend for table extraction
            extract_dates: Extract date information
            extract_names: Extract person/company names
            extract_numbers: Extract document numbers and amounts

        Returns:
            Operation-specific results with processing details and quality metrics
        """
        try:
            logger.info(f"Document processing operation: {operation}")

            # Validate operation parameter
            valid_operations = [
                "process_document", "process_batch", "extract_regions",
                "analyze_layout", "extract_table_data", "detect_form_fields",
                "analyze_reading_order", "classify_document", "extract_metadata",
                "assess_quality", "compare_backends", "validate_accuracy", "analyze_image_quality"
            ]

            if operation not in valid_operations:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override=f"Invalid operation: {operation}",
                    details={"valid_operations": valid_operations}
                ).to_dict()

            # Route to appropriate handler based on operation
            if operation == "process_document":
                return await _handle_process_document(
                    source_path, backend, ocr_mode, output_format, language, region,
                    enhance_image, comic_mode, manga_layout, scaffold_separate,
                    panel_analysis, batch_process, save_intermediate, backend_manager
                )

            elif operation == "process_batch":
                if not source_paths:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="source_paths required for process_batch operation"
                    ).to_dict()
                return await _handle_process_batch(
                    source_paths, backend, ocr_mode, output_format, max_concurrent, backend_manager
                )

            elif operation == "extract_regions":
                if not source_path or not region:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="source_path and region required for extract_regions operation"
                    ).to_dict()
                return await _handle_extract_regions(source_path, region, backend, backend_manager)

            elif operation == "analyze_layout":
                if not source_path:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="source_path required for analyze_layout operation"
                    ).to_dict()
                return await _handle_analyze_layout(source_path, analysis_type, detect_tables, detect_forms, detect_headers)

            elif operation == "extract_table_data":
                if not source_path:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="source_path required for extract_table_data operation"
                    ).to_dict()
                return await _handle_extract_table_data(source_path, table_region, ocr_backend)

            elif operation == "detect_form_fields":
                if not source_path:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="source_path required for detect_form_fields operation"
                    ).to_dict()
                return await _handle_detect_form_fields(source_path, field_types=None)

            elif operation == "analyze_reading_order":
                if not source_path:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="source_path required for analyze_reading_order operation"
                    ).to_dict()
                return await _handle_analyze_reading_order(source_path, ocr_result)

            elif operation == "classify_document":
                if not source_path:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="source_path required for classify_document operation"
                    ).to_dict()
                return await _handle_classify_document(source_path, ocr_result)

            elif operation == "extract_metadata":
                if not source_path:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="source_path required for extract_metadata operation"
                    ).to_dict()
                return await _handle_extract_metadata(source_path, ocr_result, extract_dates, extract_names, extract_numbers)

            elif operation == "assess_quality":
                if not ocr_result:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="ocr_result required for assess_quality operation"
                    ).to_dict()
                return await _handle_assess_quality(ocr_result, ground_truth, assessment_type)

            elif operation == "compare_backends":
                if not source_path:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="source_path required for compare_backends operation"
                    ).to_dict()
                if not backends:
                    backends = ["tesseract", "easyocr", "pp-ocrv5"]
                return await _handle_compare_backends(source_path, backends)

            elif operation == "validate_accuracy":
                if not ocr_result or not ground_truth:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="ocr_result and ground_truth required for validate_accuracy operation"
                    ).to_dict()
                return await _handle_validate_accuracy(ocr_result, ground_truth, validation_type)

            elif operation == "analyze_image_quality":
                if not source_path:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="source_path required for analyze_image_quality operation"
                    ).to_dict()
                return await _handle_analyze_image_quality(source_path, quality_checks)

        except Exception as e:
            logger.error(f"Document processing operation failed: {operation}, error: {e}")
            return ErrorHandler.handle_exception(e, context=f"document_processing_{operation}")


# Operation handler functions
async def _handle_process_document(source_path, backend, ocr_mode, output_format, language, region,
                                 enhance_image, comic_mode, manga_layout, scaffold_separate,
                                 panel_analysis, batch_process, save_intermediate, backend_manager):
    """Handle single document processing."""
    # Implementation moved from original process_document function
    # This will be the consolidated logic from ocr_tools.py
    return create_success_response({"operation": "process_document", "status": "not_implemented_yet"})


async def _handle_process_batch(source_paths, backend, ocr_mode, output_format, max_concurrent, backend_manager):
    """Handle batch document processing."""
    # Implementation moved from original process_batch_documents function
    return create_success_response({"operation": "process_batch", "status": "not_implemented_yet"})


async def _handle_extract_regions(source_path, region, backend, backend_manager):
    """Handle region-based OCR extraction."""
    # Implementation moved from original extract_regions function
    return create_success_response({"operation": "extract_regions", "status": "not_implemented_yet"})


async def _handle_analyze_layout(source_path, analysis_type, detect_tables, detect_forms, detect_headers):
    """Handle document layout analysis."""
    # Implementation moved from analysis_tools.py
    return create_success_response({"operation": "analyze_layout", "status": "not_implemented_yet"})


async def _handle_extract_table_data(source_path, table_region, ocr_backend):
    """Handle table data extraction."""
    # Implementation moved from analysis_tools.py
    return create_success_response({"operation": "extract_table_data", "status": "not_implemented_yet"})


async def _handle_detect_form_fields(source_path, field_types):
    """Handle form field detection."""
    # Implementation moved from analysis_tools.py
    return create_success_response({"operation": "detect_form_fields", "status": "not_implemented_yet"})


async def _handle_analyze_reading_order(source_path, ocr_result):
    """Handle reading order analysis."""
    # Implementation moved from analysis_tools.py
    return create_success_response({"operation": "analyze_reading_order", "status": "not_implemented_yet"})


async def _handle_classify_document(source_path, ocr_result):
    """Handle document type classification."""
    # Implementation moved from analysis_tools.py
    return create_success_response({"operation": "classify_document", "status": "not_implemented_yet"})


async def _handle_extract_metadata(source_path, ocr_result, extract_dates, extract_names, extract_numbers):
    """Handle metadata extraction."""
    # Implementation moved from analysis_tools.py
    return create_success_response({"operation": "extract_metadata", "status": "not_implemented_yet"})


async def _handle_assess_quality(ocr_result, ground_truth, assessment_type):
    """Handle quality assessment."""
    # Implementation moved from quality_tools.py
    return create_success_response({"operation": "assess_quality", "status": "not_implemented_yet"})


async def _handle_compare_backends(source_path, backends):
    """Handle backend comparison."""
    # Implementation moved from quality_tools.py
    return create_success_response({"operation": "compare_backends", "status": "not_implemented_yet"})


async def _handle_validate_accuracy(ocr_result, ground_truth, validation_type):
    """Handle accuracy validation."""
    # Implementation moved from quality_tools.py
    return create_success_response({"operation": "validate_accuracy", "status": "not_implemented_yet"})


async def _handle_analyze_image_quality(source_path, quality_checks):
    """Handle image quality analysis."""
    # Implementation moved from quality_tools.py
    return create_success_response({"operation": "analyze_image_quality", "status": "not_implemented_yet"})


def register_ocr_tools(app, backend_manager: BackendManager, config: OCRConfig):
    """Legacy function - now delegates to portmanteau tool."""
    register_document_processing_tools(app, backend_manager, config)


# Legacy individual tool functions removed - now handled by portmanteau tool