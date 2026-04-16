# MIT License
#
# Copyright (c) 2025 OCR-MCP Project
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
#
#
#
#

"""
OCR Tools for OCR-MCP Server: SOTA v13.1 Technical Refit.

Consolidates document processing, image manipulation, and hardware control into
precise, schema-aware operational tools.
"""

import logging
from typing import Any, Literal, Optional

from ..core.config import OCRConfig
from ..core.error_handler import ErrorHandler
from . import (
    _analysis,
    _conversion,
    _corpus,
    _image,
    _processor,
    _quality,
    _scanner,
    _workflow,
)
from .models import (
    OCRBackend,
    OCRMode,
    OutputFormat,
    ToolResponse,
)

logger = logging.getLogger(__name__)


def register_sota_tools(app, backend_manager_or_runtime, config: OCRConfig):
    """Register refactored SOTA tools with the FastMCP app."""

    def _resolve():
        if isinstance(backend_manager_or_runtime, dict):
            return (
                backend_manager_or_runtime.get("backend_manager"),
                backend_manager_or_runtime.get("config") or config,
            )
        return backend_manager_or_runtime, config

    @app.tool()
    async def process_document(
        operation: Literal[
            "process_document",
            "process_batch",
            "analyze_layout",
            "extract_tables",
            "detect_forms",
            "analyze_reading_order",
            "classify_type",
            "extract_metadata",
            "assess_quality",
            "validate_accuracy",
            "compare_backends",
            "analyze_image_quality",
        ],
        source_path: Optional[str] = None,
        backend: OCRBackend = "auto",
        ocr_mode: OCRMode = "auto",
        output_format: OutputFormat = "text",
        language: Optional[str] = None,
        region: Optional[list[int]] = None,
        enhance_image: bool = True,
        ocr_result: Optional[dict[str, Any]] = None,
        ground_truth: Optional[str] = None,
        assessment_type: Literal["comprehensive", "basic", "layout"] = "comprehensive",
        validation_type: Literal["character", "word"] = "character",
        backends: Optional[list[OCRBackend]] = None,
        quality_checks: Optional[list[str]] = None,
        analysis_type: Literal["comprehensive", "layout_only", "tables_only"] = "comprehensive",
        detect_tables: bool = True,
        detect_forms: bool = True,
        detect_headers: bool = True,
        table_region: Optional[list[int]] = None,
        extract_dates: bool = True,
        extract_names: bool = True,
        extract_numbers: bool = True,
        source_paths: Optional[list[str]] = None,
        max_concurrent: int = 4,
    ) -> ToolResponse:
        """
        Execute document processing operations including OCR, layout analysis, and quality assessment.

        OPERATIONS:
        - process_document: Run OCR on a single file. (Requires: source_path)
        - process_batch: Parallel processing for a directory or list of paths. (Requires: source_path or source_paths)
        - analyze_layout: Detect structural elements (tables, forms, zones). (Requires: source_path)
        - extract_tables: Deep table parsing and OCR. (Requires: source_path)
        - detect_forms: Form field and checkbox detection. (Requires: source_path)
        - analyze_reading_order: Determine logical text flow. (Requires: source_path or ocr_result)
        - classify_type: Categorize document (invoice, ID, contract). (Requires: source_path)
        - extract_metadata: NLP-based entity extraction (dates, names). (Requires: ocr_result)
        - assess_quality: Score OCR results and provide error heatmaps. (Requires: ocr_result)
        - validate_accuracy: Calculate CER/WER against ground truth. (Requires: ocr_result, ground_truth)
        - compare_backends: Benchmarking multi-model performance. (Requires: source_path)
        - analyze_image_quality: Pre-OCR assessment (blur, noise, DPI). (Requires: source_path)

        COMMON ERRORS:
        - BACKEND_NOT_AVAILABLE: Ensure the requested OCR engine is downloaded (use status() to check).
        - FILE_NOT_FOUND: Verify the source_path exists and is a valid document.
        - QUALITY_TOO_LOW: Image resolution <200 DPI or high noise. Use manage_image(operation='preprocess') first.
        """
        backend_manager, config = _resolve()
        if not backend_manager:
            return ToolResponse(
                success=False,
                operation=operation,
                summary="OCR-MCP server not initialized.",
                next_steps=["Please restart the server."],
            )

        try:
            res_data = {}
            if operation == "process_document":
                res_data = await _processor.process_document(
                    source_path=source_path,
                    backend=backend,
                    mode=ocr_mode,
                    enhance=enhance_image,
                    region=region,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "process_batch":
                res_data = await _processor.process_batch(
                    source_dir=source_path,
                    backend=backend,
                    mode=ocr_mode,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "analyze_layout":
                res_data = await _analysis.analyze_document_layout(
                    source_path,
                    analysis_type,
                    detect_tables,
                    detect_forms,
                    detect_headers,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "extract_tables":
                res_data = await _analysis.extract_table_data(
                    source_path,
                    table_region=table_region,
                    ocr_backend=backend,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "detect_forms":
                res_data = await _analysis.detect_form_fields(
                    source_path,
                    field_types=None,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "analyze_reading_order":
                res_data = await _analysis.analyze_document_reading_order(
                    source_path,
                    ocr_result=ocr_result,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "classify_type":
                res_data = await _analysis.classify_document_type(
                    source_path,
                    ocr_result=ocr_result,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "extract_metadata":
                res_data = await _analysis.extract_document_metadata(
                    source_path,
                    ocr_result=ocr_result,
                    extract_dates=extract_dates,
                    extract_names=extract_names,
                    extract_numbers=extract_numbers,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "assess_quality":
                res_data = await _quality.assess_ocr_quality(
                    ocr_result,
                    ground_truth,
                    assessment_type,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "validate_accuracy":
                res_data = await _quality.validate_ocr_accuracy(
                    ocr_text=ocr_result.get("text") if ocr_result else "",
                    expected_text=ground_truth if ground_truth else "",
                    validation_type=validation_type,
                )
            elif operation == "compare_backends":
                res_data = await _quality.compare_ocr_backends(
                    image_path=source_path,
                    backends=backends,
                    ground_truth=ground_truth,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "analyze_image_quality":
                res_data = await _quality.analyze_image_quality(
                    image_path=source_path,
                    quality_checks=quality_checks,
                )
            else:
                return ToolResponse(
                    success=False,
                    operation=operation,
                    summary=f"Unsupported operation: {operation}",
                )

            return ToolResponse(
                success=res_data.get("success", True),
                operation=operation,
                result=res_data.get("result", res_data),
                summary=res_data.get("summary") or res_data.get("message") or "Operation completed",
                next_steps=res_data.get("next_steps", []),
                suggestions=res_data.get("suggestions", []),
            )

        except Exception as e:
            err = ErrorHandler.handle_exception(e, context=f"process_document_{operation}")
            return ToolResponse(
                success=False,
                operation=operation,
                summary=str(e),
                next_steps=err.get("recovery_options", []),
            )

    @app.tool()
    async def manage_image(
        operation: Literal["preprocess", "convert", "pdf_to_images", "embed_text"],
        source_path: Optional[str] = None,
        target_path: Optional[str] = None,
        format: Literal["png", "jpg", "tiff", "webp"] = "png",
        grayscale: bool = True,
        denoise: bool = True,
        deskew: bool = True,
        threshold: bool = False,
        autocrop: bool = False,
        dpi: Optional[int] = 300,
    ) -> ToolResponse:
        """
        Manage image preprocessing and format conversion.

        OPERATIONS:
        - preprocess: Enhance image specifically for OCR (deskew, denoise).
        - convert: Change image format (e.g., TIFF to PNG).
        - pdf_to_images: Explode PDF pages into separate images.
        - embed_text: Create a searchable PDF/A by embedding an invisible text layer.

        RECOVERY:
        - If 'deskew' fails, ensure the image contains significant horizontal text lines.
        - Large PDFs (>100MB) may timeout during 'pdf_to_images'.
        """
        backend_manager, config = _resolve()
        if not backend_manager:
            return ToolResponse(
                success=False,
                operation=operation,
                summary="OCR-MCP server not initialized.",
            )

        try:
            res_data = {}
            if operation == "preprocess":
                res_data = await _image.preprocess_image(
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
                res_data = await _conversion.convert_image(
                    source_path,
                    target_path,
                    format,
                    dpi,
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "pdf_to_images":
                res_data = await _conversion.convert_pdf_to_images(
                    source_path,
                    target_path or ".",
                    dpi or 300,
                    format or "PNG",
                    backend_manager=backend_manager,
                    config=config,
                )
            elif operation == "embed_text":
                res_data = await _conversion.embed_ocr_text(
                    source_path,
                    target_path or "searchable.pdf",
                    backend_manager=backend_manager,
                    config=config,
                )
            else:
                return ToolResponse(success=False, operation=operation, summary=f"Unknown op: {operation}")

            return ToolResponse(
                success=res_data.get("success", True),
                operation=operation,
                result=res_data.get("result", res_data),
                summary=res_data.get("summary") or res_data.get("message") or "Image managed.",
                next_steps=res_data.get("next_steps", []),
            )
        except Exception as e:
            return ToolResponse(success=False, operation=operation, summary=str(e))

    @app.tool()
    async def operate_scanner(
        operation: Literal[
            "list_scanners",
            "scanner_properties",
            "configure_scan",
            "scan_document",
            "scan_batch",
            "preview_scan",
            "diagnostics",
        ],
        device_id: Optional[str] = None,
        scan_source: Literal["flatbed", "adf"] = "flatbed",
        resolution: int = 300,
        color_mode: Literal["color", "grayscale", "lineart"] = "color",
        paper_size: str = "A4",
        output_prefix: str = "scan_",
    ) -> ToolResponse:
        """
        Hardware control for connected Windows WIA scanners.

        OPERATIONS:
        - list_scanners: Enumerate connected devices and get device_ids.
        - scan_document: Acquire single page from flatbed.
        - scan_batch: Acquire multiple pages using ADF.
        - diagnostics: Test scanner connectivity and capabilities.

        RECOVERY:
        - SCANNER_NOT_FOUND: Ensure hardware is ON and Windows WIA service is running.
        - SCANNER_BUSY: Wait for current job to finish or restart physical device.
        """
        backend_manager, config = _resolve()
        if not backend_manager:
            return ToolResponse(success=False, operation=operation, summary="Server not init.")

        try:
            res_data = await _scanner.handle_scanner_op(
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
            return ToolResponse(
                success=res_data.get("success", True),
                operation=operation,
                result=res_data.get("result", res_data),
                summary=res_data.get("message") or "Scanner operation completed.",
            )
        except Exception as e:
            return ToolResponse(success=False, operation=operation, summary=str(e))

    @app.tool()
    async def manage_workflow(
        operation: Literal[
            "process_batch_intelligent",
            "create_processing_pipeline",
            "execute_pipeline",
            "monitor_batch_progress",
            "optimize_processing",
            "ocr_health_check",
            "list_backends",
            "manage_models",
        ],
        workflow_name: Optional[str] = None,
        source_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
        pipeline_config: Optional[dict[str, Any]] = None,
    ) -> ToolResponse:
        """
        Orchestrate batch processing, custom pipelines, and system management.

        OPERATIONS:
        - process_batch_intelligent: Automatically choose best routing for multiple files.
        - create_processing_pipeline: Define sequential tools (e.g. crop -> deskew -> OCR).
        - execute_pipeline: Run a defined pipeline on a series of documents.
        - list_backends: Show hardware acceleration and download status for all OCR engines.
        """
        backend_manager, _ = _resolve()
        if not backend_manager:
            return ToolResponse(success=False, operation=operation, summary="Server not init.")

        try:
            res_data = await _workflow.handle_mcp_workflow(
                operation,
                workflow_name,
                source_dir,
                output_dir,
                pipeline_config,
                backend_manager,
            )
            return ToolResponse(
                success=res_data.get("success", True),
                operation=operation,
                result=res_data.get("result", res_data),
                summary=res_data.get("message") or "Workflow operation completed.",
            )
        except Exception as e:
            return ToolResponse(success=False, operation=operation, summary=str(e))

    @app.tool()
    async def manage_corpus(
        operation: Literal["register", "update_metadata", "get", "search", "list_recent", "attach_ocr_result"],
        source_path: Optional[str] = None,
        corpus_id: Optional[str] = None,
        title: Optional[str] = None,
        tags: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        query: Optional[str] = None,
        limit: int = 20,
        ocr_text: Optional[str] = None,
        ocr_text_path: Optional[str] = None,
        backend: Optional[OCRBackend] = None,
        metadata_patch: Optional[dict[str, Any]] = None,
    ) -> ToolResponse:
        """
        Local SQLite document index management. Persist OCR results and metadata.

        OPERATIONS:
        - register: Add a new file to the local index.
        - search: Full-text search across indexed documents and OCR excerpts.
        - attach_ocr_result: Link extracted text to an existing index entry.
        """
        _, cfg = _resolve()
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags and tags.strip() else None
        try:
            res_data = await _corpus.handle_corpus_op(
                operation=operation,
                config=cfg,
                source_path=source_path,
                corpus_id=corpus_id,
                title=title,
                tags=tag_list,
                metadata=metadata,
                query=query,
                limit=limit,
                ocr_text=ocr_text,
                ocr_text_path=ocr_text_path,
                backend=backend,
                metadata_patch=metadata_patch,
            )
            return ToolResponse(
                success=res_data.get("success", True),
                operation=operation,
                result=res_data.get("result", res_data),
            )
        except Exception as e:
            return ToolResponse(success=False, operation=operation, summary=str(e))

    @app.tool()
    async def get_help(
        level: Literal["basic", "intermediate", "advanced"] = "basic", topic: Optional[str] = None
    ) -> str:
        """Contextual documentation for OCR operations and tool configurations."""
        return _workflow.get_help_content(level, topic)

    @app.tool()
    async def get_status(level: Literal["basic", "detailed"] = "basic") -> ToolResponse:
        """Real-time system health, backend availability, and resource utilization."""
        backend_manager, _ = _resolve()
        if not backend_manager:
            return ToolResponse(success=False, operation="get_status", summary="Server not init.")
        res_data = _workflow.get_system_status(level, backend_manager)
        return ToolResponse(
            success=True,
            operation="get_status",
            result=res_data,
            summary="System status retrieved.",
        )


# Aliases for backward compatibility
register_ocr_tools = register_sota_tools
register_document_processing_tools = register_sota_tools
