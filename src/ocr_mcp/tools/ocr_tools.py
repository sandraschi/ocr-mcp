"""
OCR Tools for OCR-MCP Server - PORTMANTEAU DESIGN

This module consolidates multiple individual tools into portmanteau tools
for better discoverability and reduced tool count.

PORTMANTEAU TOOLS:
- document_processing: OCR, analysis, quality assessment operations
- image_management: Image preprocessing and conversion operations
- scanner_operations: Scanner hardware control operations
- workflow_management: Batch processing, pipelines, system operations
- ocr_help: Help and documentation
- ocr_status: System health and status
"""

import logging
from typing import Any

from ..core.backend_manager import BackendManager
from ..core.config import OCRConfig
from ..core.error_handler import ErrorHandler
from . import (
    _analysis,
    _conversion,
    _image,
    _processor,
    _quality,
    _scanner,
    _workflow,
)

logger = logging.getLogger(__name__)


def register_sota_tools(app, backend_manager_or_runtime, config: OCRConfig):
    """Register all SOTA-compliant portmanteau tools with the FastMCP app.

    backend_manager_or_runtime: BackendManager instance, or dict with keys
        backend_manager and config (mutated by server lifespan).
    """

    def _resolve():
        if isinstance(backend_manager_or_runtime, dict):
            return (
                backend_manager_or_runtime.get("backend_manager"),
                backend_manager_or_runtime.get("config") or config,
            )
        return backend_manager_or_runtime, config

    @app.tool()
    async def document_processing(
        operation: str,
        source_path: str | None = None,
        backend: str = "auto",
        ocr_mode: str = "auto",
        output_format: str = "text",
        language: str | None = None,
        region: list[int] | None = None,
        enhance_image: bool = True,
        comic_mode: bool = False,
        manga_layout: bool = False,
        scaffold_separate: bool = False,
        panel_analysis: bool = False,
        batch_process: bool = False,
        save_intermediate: bool = False,
        source_paths: list[str] | None = None,
        max_concurrent: int = 4,
        ocr_result: dict[str, Any] | None = None,
        ground_truth: str | None = None,
        assessment_type: str = "comprehensive",
        validation_type: str = "character",
        backends: list[str] | None = None,
        quality_checks: list[str] | None = None,
        analysis_type: str = "comprehensive",
        detect_tables: bool = True,
        detect_forms: bool = True,
        detect_headers: bool = True,
        table_region: list[int] | None = None,
        ocr_backend: str = "auto",
        extract_dates: bool = True,
        extract_names: bool = True,
        extract_numbers: bool = True,
    ) -> dict[str, Any]:
        """
        PORTMANTEAU PATTERN RATIONALE:
        Consolidates 13 document OCR, analysis, and quality operations into a single
        interface. Prevents tool explosion while maintaining full functionality. Follows
        FastMCP 2.14+ best practices.

        OPERATIONS:
        - process_document: Main OCR for single images/PDFs. Requires: source_path.
        - process_batch: Parallel multi-document processing. Requires: source_path (dir).
        - analyze_layout: Structural detection (tables, forms, reading order). Requires: source_path.
        - extract_tables: Table region extraction and OCR. Requires: source_path.
        - detect_forms: Form field detection. Requires: source_path.
        - analyze_reading_order: Document reading order. Requires: source_path.
        - classify_type: Document type classification. Requires: source_path.
        - extract_metadata: Dates, names, numbers extraction. Requires: source_path.
        - assess_quality: OCR output scoring. Requires: ocr_result.
        - validate_accuracy: CER/WER measurement. Requires: ocr_result, ground_truth.
        - compare_backends: Multi-backend comparison. Requires: source_path.
        - analyze_image_quality: Image preprocessing assessment. Requires: source_path.

        Args:
        - operation (str, required): Operation to perform. Must be one of OPERATIONS above.
        - source_path (str | None): Path to document or directory. Required for most operations.
        - backend (str): OCR backend. Default: auto. Valid: auto, deepseek-ocr, florence-2,
          pp-ocrv5, tesseract, easyocr. Used by: process_document, process_batch.
        - ocr_mode (str): OCR mode. Default: auto. Used by: process_document, process_batch.
        - output_format (str): Output format. Default: text. Used by: process_document.
        - language (str | None): Language hint. Used by: process_document.
        - region (list[int] | None): [x, y, w, h] region of interest. Used by: process_document.
        - enhance_image (bool): Apply preprocessing. Default: True. Used by: process_document.
        - ocr_result (dict[str, Any] | None): Prior OCR output. Required for: assess_quality,
          validate_accuracy, classify_type, extract_metadata, analyze_reading_order.
        - ground_truth (str | None): Expected text for validation. Required for: validate_accuracy,
          compare_backends.
        - backends (list[str] | None): Backends to compare. Used by: compare_backends.
        - assessment_type (str): Quality assessment type. Default: comprehensive. Used by: assess_quality.
        - validation_type (str): CER or WER. Default: character. Used by: validate_accuracy.
        - analysis_type (str): Layout analysis depth. Default: comprehensive. Used by: analyze_layout.
        - detect_tables (bool): Include table detection. Default: True. Used by: analyze_layout.
        - detect_forms (bool): Include form detection. Default: True. Used by: analyze_layout.
        - detect_headers (bool): Include header detection. Default: True. Used by: analyze_layout.
        - table_region (list[int] | None): [x, y, w, h] for extract_tables.
        - ocr_backend (str): Backend for table OCR. Default: auto. Used by: extract_tables.
        - extract_dates (bool): Extract dates in metadata. Default: True. Used by: extract_metadata.
        - extract_names (bool): Extract names in metadata. Default: True. Used by: extract_metadata.
        - extract_numbers (bool): Extract numbers in metadata. Default: True. Used by: extract_metadata.
        - quality_checks (list[str] | None): Checks for analyze_image_quality.
        - source_paths (list[str] | None): Paths for batch. Alternative to source_path dir.
        - max_concurrent (int): Parallel limit for process_batch. Default: 4.
        - batch_process (bool): Use batch mode. Used by: process_document.
        - save_intermediate (bool): Save intermediate outputs. Used by: process_batch.
        - comic_mode (bool): Comic layout. Used by: process_document.
        - manga_layout (bool): Manga layout. Used by: process_document.
        - scaffold_separate (bool): Separate panels. Used by: process_document.
        - panel_analysis (bool): Analyze panels. Used by: process_document.

        Returns:
        FastMCP 2.14.1+ dialogic response: success, operation, result or error,
        recommendations, next_steps, recovery_options (on error), related_operations.
        Enables conversational back-and-forth between client and assistant.
        """
        backend_manager, config = _resolve()
        if not backend_manager:
            return ErrorHandler.create_error(
                "INTERNAL_ERROR", "OCR-MCP server not initialized. Please restart."
            ).to_dict()
        try:
            if operation == "process_document":
                return await _processor.process_document(
                    source_path=source_path,
                    backend=backend,
                    mode=ocr_mode,
                    enhance=enhance_image,
                    region=region,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "process_batch":
                return await _processor.process_batch(
                    source_dir=source_path,
                    backend=backend,
                    mode=ocr_mode,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "analyze_layout":
                return await _analysis.analyze_document_layout(
                    source_path,
                    analysis_type,
                    detect_tables,
                    detect_forms,
                    detect_headers,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "extract_tables":
                return await _analysis.extract_table_data(
                    source_path,
                    table_region=table_region,
                    ocr_backend=ocr_backend,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "detect_forms":
                return await _analysis.detect_form_fields(
                    source_path,
                    field_types=None,  # Could be expanded in params if needed
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "analyze_reading_order":
                return await _analysis.analyze_document_reading_order(
                    source_path,
                    ocr_result=ocr_result,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "classify_type":
                return await _analysis.classify_document_type(
                    source_path,
                    ocr_result=ocr_result,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "extract_metadata":
                return await _analysis.extract_document_metadata(
                    source_path,
                    ocr_result=ocr_result,
                    extract_dates=extract_dates,
                    extract_names=extract_names,
                    extract_numbers=extract_numbers,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "assess_quality":
                return await _quality.assess_ocr_quality(
                    ocr_result,
                    ground_truth,
                    assessment_type,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "validate_accuracy":
                return await _quality.validate_ocr_accuracy(
                    ocr_text=ocr_result.get("text") if ocr_result else "",
                    expected_text=ground_truth if ground_truth else "",
                    validation_type=validation_type,
                )
            elif operation == "compare_backends":
                return await _quality.compare_ocr_backends(
                    image_path=source_path,
                    backends=backends,
                    ground_truth=ground_truth,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "analyze_image_quality":
                return await _quality.analyze_image_quality(
                    image_path=source_path,
                    quality_checks=quality_checks,
                )

            return ErrorHandler.create_error(
                "PARAMETERS_INVALID",
                message_override=f"Unsupported operation: {operation}",
            ).to_dict()
        except Exception as e:
            return ErrorHandler.handle_exception(e, context=f"document_processing_{operation}")

    @app.tool()
    async def image_management(
        operation: str,
        source_path: str | None = None,
        target_path: str | None = None,
        format: str = "png",
        grayscale: bool = True,
        denoise: bool = True,
        deskew: bool = True,
        threshold: bool = False,
        autocrop: bool = False,
        dpi: int | None = None,
    ) -> dict[str, Any]:
        """
        PORTMANTEAU PATTERN RATIONALE:
        Consolidates 4 image preprocessing and conversion operations into a single
        interface. Prevents tool explosion while maintaining full functionality. Follows
        FastMCP 2.14+ best practices.

        OPERATIONS:
        - preprocess: Deskew, denoise, grayscale, threshold, autocrop for OCR readiness. Requires: source_path.
        - convert: Convert image format (PNG, JPG, TIFF, WebP) with optional DPI. Requires: source_path. Optional: target_path.
        - pdf_to_images: Extract pages from PDF as images at specified DPI. Requires: source_path. Optional: target_path.
        - embed_text: Create searchable PDF by embedding OCR text layer. Requires: source_path. Optional: target_path.

        Args:
        - operation (str, required): Operation to perform. Must be one of OPERATIONS above.
        - source_path (str | None): Path to source image or PDF. Required for all operations.
        - target_path (str | None): Output path. Used by: convert, pdf_to_images, embed_text.
        - format (str): Output format for convert. Default: png. Valid: png, jpg, tiff, webp.
          Used by: convert, pdf_to_images.
        - grayscale (bool): Apply grayscale. Default: True. Used by: preprocess.
        - denoise (bool): Apply denoising. Default: True. Used by: preprocess.
        - deskew (bool): Apply deskew. Default: True. Used by: preprocess.
        - threshold (bool): Apply thresholding. Default: False. Used by: preprocess.
        - autocrop (bool): Apply autocrop. Default: False. Used by: preprocess.
        - dpi (int | None): Resolution for conversion and PDF extraction. Default: 300.
          Used by: convert, pdf_to_images.

        Returns:
        FastMCP 2.14.1+ dialogic response: success, operation, result or error,
        recommendations, next_steps, recovery_options (on error), related_operations.
        Enables conversational back-and-forth between client and assistant.
        """
        backend_manager, config = _resolve()
        if not backend_manager:
            return ErrorHandler.create_error(
                "INTERNAL_ERROR", "OCR-MCP server not initialized. Please restart."
            ).to_dict()
        try:
            if operation == "preprocess":
                return await _image.preprocess_image(
                    source_path,
                    grayscale,
                    denoise,
                    deskew,
                    threshold,
                    autocrop,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "convert":
                return await _conversion.convert_image(
                    source_path,
                    target_path,
                    format,
                    dpi,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "pdf_to_images":
                return await _conversion.convert_pdf_to_images(
                    source_path,
                    target_path or ".",
                    dpi or 300,
                    format or "PNG",
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "embed_text":
                return await _conversion.embed_ocr_text(
                    source_path,
                    target_path or "searchable.pdf",
                    backend_manager=backend_manager,
                    config=config,
                )
            return ErrorHandler.create_error(
                "PARAMETERS_INVALID",
                message_override=f"Unsupported operation: {operation}",
            ).to_dict()
        except Exception as e:
            return ErrorHandler.handle_exception(e, context=f"image_management_{operation}")

    @app.tool()
    async def scanner_operations(
        operation: str,
        device_id: str | None = None,
        scan_source: str = "flatbed",
        resolution: int = 300,
        color_mode: str = "color",
        paper_size: str = "A4",
        output_prefix: str = "scan_",
    ) -> dict[str, Any]:
        """
        PORTMANTEAU PATTERN RATIONALE:
        Consolidates 7 scanner hardware operations into a single interface. Prevents
        tool explosion while maintaining full functionality. Follows FastMCP 2.14+
        best practices. Windows WIA only.

        OPERATIONS:
        - list_scanners: Discover and enumerate available WIA scanners. No device_id.
        - scanner_properties: Get capabilities and settings. Requires: device_id.
        - configure_scan: Set scan parameters. Requires: device_id.
        - scan_document: Single document scan from flatbed or ADF. Requires: device_id.
        - scan_batch: Batch scan multiple documents with ADF. Requires: device_id.
        - preview_scan: Low-resolution preview for positioning. Requires: device_id.
        - diagnostics: Troubleshooting and backend status. Optional: device_id.

        Args:
        - operation (str, required): Operation to perform. Must be one of OPERATIONS above.
        - device_id (str | None): WIA device ID from list_scanners. Optional: when omitted
          and scan_source is flatbed, uses first flatbed scanner in list. Required only for
          diagnostics when targeting a specific device.
        - scan_source (str): Source for scanning. Default: flatbed. Valid: flatbed, adf.
          Used by: configure_scan, scan_document, scan_batch.
        - resolution (int): DPI for scanning. Default: 300. Used by: configure_scan,
          scan_document, scan_batch.
        - color_mode (str): Color mode. Default: color. Valid: color, grayscale, lineart.
          Used by: configure_scan, scan_document, scan_batch.
        - paper_size (str): Paper size. Default: A4. Valid: A4, Letter, Legal, etc.
          Used by: configure_scan, scan_document, scan_batch.
        - output_prefix (str): Prefix for output files. Default: scan_. Used by:
          scan_document, scan_batch.

        Returns:
        FastMCP 2.14.1+ dialogic response: success, operation, result or error,
        recommendations, next_steps, recovery_options (on error), related_operations.
        Enables conversational back-and-forth between client and assistant.
        """
        backend_manager, config = _resolve()
        if not backend_manager:
            return ErrorHandler.create_error(
                "INTERNAL_ERROR", "OCR-MCP server not initialized. Please restart."
            ).to_dict()
        try:
            return await _scanner.handle_scanner_op(
                operation,
                device_id,
                scan_source,
                resolution,
                color_mode,
                paper_size,
                output_prefix,
                backend_manager=backend_manager,
                config=config,
            )
        except Exception as e:
            return ErrorHandler.handle_exception(e, context=f"scanner_operations_{operation}")

    @app.tool()
    async def workflow_management(
        operation: str,
        workflow_name: str | None = None,
        source_dir: str | None = None,
        output_dir: str | None = None,
        pipeline_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        PORTMANTEAU PATTERN RATIONALE:
        Consolidates 8 batch processing, pipeline, and system management operations
        into a single interface. Prevents tool explosion while maintaining full
        functionality. Follows FastMCP 2.14+ best practices.

        OPERATIONS:
        - process_batch_intelligent: Auto workflow per document. Requires: source_dir.
        - create_processing_pipeline: Define custom pipeline. Requires: workflow_name, pipeline_config (steps).
        - execute_pipeline: Run pipeline on documents. Requires: pipeline_config, source_dir (input_documents).
        - monitor_batch_progress: Batch progress and metrics.
        - optimize_processing: Recommended settings for document set. Requires: source_dir.
        - ocr_health_check: Backend health and diagnostics.
        - list_backends: Available OCR backends and status.
        - manage_models: Model memory management.

        Args:
        - operation (str, required): Operation to perform. Must be one of OPERATIONS above.
        - workflow_name (str | None): Pipeline name. Required for: create_processing_pipeline.
        - source_dir (str | None): Input directory or document paths. Required for:
          process_batch_intelligent, optimize_processing. Used by: execute_pipeline.
        - output_dir (str | None): Output directory for batch results. Used by:
          process_batch_intelligent.
        - pipeline_config (dict[str, Any] | None): Pipeline definition with steps, or
          execution config. Required for: create_processing_pipeline (steps),
          execute_pipeline (full config).

        Returns:
        FastMCP 2.14.1+ dialogic response: success, operation, result or error,
        recommendations, next_steps, recovery_options (on error), related_operations.
        Enables conversational back-and-forth between client and assistant.
        """
        backend_manager, config = _resolve()
        if not backend_manager:
            return ErrorHandler.create_error(
                "INTERNAL_ERROR", "OCR-MCP server not initialized. Please restart."
            ).to_dict()
        try:
            return await _workflow.handle_workflow_op(
                operation,
                workflow_name,
                source_dir,
                output_dir,
                pipeline_config,
                backend_manager=backend_manager,
                config=config,
            )
        except Exception as e:
            return ErrorHandler.handle_exception(e, context=f"workflow_management_{operation}")

    @app.tool()
    async def help(level: str = "basic", topic: str | None = None) -> str:
        """
        PORTMANTEAU PATTERN RATIONALE:
        Single help tool for contextual documentation. Prevents separate help tools
        per domain. Follows FastMCP 2.14+ best practices.

        LEVELS:
        - basic: Quick start, essential tools, common workflows.
        - intermediate: Detailed options, batch and pipeline patterns.
        - advanced: Backend config, architecture, troubleshooting.

        Args:
        - level (str): Help depth. Default: basic. Must be one of LEVELS above.
        - topic (str | None): Optional filter for focused help. Valid: scanner, ocr, workflow, etc.

        Returns:
        Markdown string with contextual help for the requested level and topic.
        """
        return _workflow.get_help_content(level, topic)

    @app.tool()
    async def status(level: str = "basic") -> dict[str, Any]:
        """
        PORTMANTEAU PATTERN RATIONALE:
        Single status tool for system diagnostics. Prevents separate status tools per
        component. Follows FastMCP 2.14+ best practices.

        LEVELS:
        - basic: Backend availability, overall health, quick status.
        - detailed: Per-backend status, model load state, resource usage.

        Args:
        - level (str): Detail depth. Default: basic. Must be one of LEVELS above.

        Returns:
        FastMCP 2.14.1+ dialogic response: success, operation, result or error,
        recommendations, next_steps, recovery_options (on error), related_operations.
        Enables conversational back-and-forth between client and assistant.
        """
        backend_manager, _ = _resolve()
        if not backend_manager:
            return ErrorHandler.create_error(
                "INTERNAL_ERROR", "OCR-MCP server not initialized. Please restart."
            ).to_dict()
        return _workflow.get_system_status(level, backend_manager)


register_ocr_tools = register_sota_tools
register_document_processing_tools = register_sota_tools
