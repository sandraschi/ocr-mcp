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
    _quality,
    _image,
    _conversion,
    _scanner,
    _workflow,
    _processor,
)

logger = logging.getLogger(__name__)


def register_sota_tools(app, backend_manager: BackendManager, config: OCRConfig):
    """Register all SOTA-compliant portmanteau tools with the FastMCP app."""

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
        # Batch processing parameters
        source_paths: list[str] | None = None,
        max_concurrent: int = 4,
        # Quality assessment/Analysis parameters
        ocr_result: dict[str, Any] | None = None,
        ground_truth: str | None = None,
        assessment_type: str = "comprehensive",
        validation_type: str = "character",
        backends: list[str] | None = None,
        quality_checks: list[str] | None = None,
        # Layout analysis parameters
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
        PORTMANTEAU TOOL: Comprehensive Document Processing Operations.

        OPERATIONS:
        - "process_document": Main OCR tool for single images/PDFs.
        - "process_batch": Parallel multi-document processing.
        - "analyze_layout": Structural detection (tables, forms).
        - "assess_quality": OCR output scoring.
        - "validate_accuracy": CER/WER measurement.
        """
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
            return ErrorHandler.handle_exception(
                e, context=f"document_processing_{operation}"
            )

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
        PORTMANTEAU TOOL: Image Preprocessing and Conversion Operations.
        """
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
            return ErrorHandler.handle_exception(
                e, context=f"image_management_{operation}"
            )

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
        PORTMANTEAU TOOL: Scanner Hardware Control Operations.
        """
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
            return ErrorHandler.handle_exception(
                e, context=f"scanner_operations_{operation}"
            )

    @app.tool()
    async def workflow_management(
        operation: str,
        workflow_name: str | None = None,
        source_dir: str | None = None,
        output_dir: str | None = None,
        pipeline_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        PORTMANTEAU TOOL: Batch Processing and Workflow Orchestration.
        """
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
            return ErrorHandler.handle_exception(
                e, context=f"workflow_management_{operation}"
            )

    @app.tool()
    async def help(level: str = "basic", topic: str | None = None) -> str:
        """
        PORTMANTEAU TOOL: Comprehensive help and documentation for OCR-MCP.

        LEVELS:
        - basic: Quick start and essential tools
        - intermediate: Detailed workflows and options
        - advanced: Backend configuration and architecture
        """
        return _workflow.get_help_content(level, topic)

    @app.tool()
    async def status(level: str = "basic") -> dict[str, Any]:
        """
        PORTMANTEAU TOOL: System diagnostics and backend health monitoring.
        """
        return _workflow.get_system_status(level, backend_manager)
