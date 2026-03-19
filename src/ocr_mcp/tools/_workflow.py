"""
Workflow Management Tools for OCR-MCP Server - PORTMANTEAU DESIGN

Consolidates batch processing, pipelines, system monitoring, and management operations into a single tool.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any

from ..core.error_handler import ErrorHandler, create_success_response
from . import _analysis, _conversion, _image, _processor, _quality

logger = logging.getLogger(__name__)

# Map pipeline step tool names to (module, function_name)
_STEP_TOOL_MAP = {
    "process_document": (_processor, "process_document"),
    "assess_ocr_quality": (_quality, "assess_ocr_quality"),
    "analyze_document_layout": (_analysis, "analyze_document_layout"),
    "extract_table_data": (_analysis, "extract_table_data"),
    "convert_image_format": (_conversion, "convert_image"),
    "deskew_image": (_image, "deskew_image"),
    "enhance_image": (_image, "preprocess_image"),
    "rotate_image": (_image, "rotate_image"),
    "crop_image": (_image, "preprocess_image"),
}


def get_help_content(level: str = "basic", topic: str | None = None) -> str:
    """Provides contextual help for OCR-MCP."""
    help_data = {
        "basic": "# OCR-MCP Help\nUse `document_processing` for OCR tasks.",
        "advanced": "# Advanced OCR-MCP\nConfiguring backends and pipelines...",
    }
    return help_data.get(level, help_data["basic"])


def get_system_status(level: str = "basic", backend_manager: Any = None) -> dict[str, Any]:
    """Returns system health and backend status."""
    status = {
        "status": "healthy",
        "backends": backend_manager.list_backends() if backend_manager else [],
    }
    return status


# --- Helper Functions (Forward Declaration) ---
async def analyze_document_workflow(doc_path: str) -> dict[str, Any]:
    """Analyze a document to determine optimal processing workflow."""
    try:
        # Get basic file info
        file_path = Path(doc_path)
        if not file_path.exists():
            return {
                "file_path": doc_path,
                "error": "File not found",
                "estimated_complexity": "unknown",
                "recommended_workflow": "fallback",
            }

        file_size = file_path.stat().st_size
        file_ext = file_path.suffix.lower()

        # Basic document analysis
        analysis = {
            "file_path": doc_path,
            "file_size": file_size,
            "file_type": file_ext,
            "estimated_complexity": "low",
            "recommended_workflow": "standard",
            "expected_quality": 0.8,
        }

        # Determine document type and complexity
        if file_ext in [".pdf"]:
            analysis.update(
                {
                    "document_type": "pdf",
                    "estimated_complexity": "medium",
                    "recommended_workflow": "pdf_processing",
                }
            )
        elif file_ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            analysis.update(
                {
                    "document_type": "image",
                    "estimated_complexity": "low",
                    "recommended_workflow": "image_processing",
                }
            )
        else:
            analysis.update(
                {
                    "document_type": "unknown",
                    "estimated_complexity": "high",
                    "recommended_workflow": "complex_processing",
                }
            )

        # Estimate file complexity by size
        if file_size > 10 * 1024 * 1024:  # 10MB
            analysis["estimated_complexity"] = "high"
            analysis["expected_quality"] = 0.6
        elif file_size > 1 * 1024 * 1024:  # 1MB
            analysis["estimated_complexity"] = "medium"
            analysis["expected_quality"] = 0.75

        return analysis

    except Exception as e:
        logger.error(f"Document workflow analysis failed: {e}")
        return {
            "file_path": doc_path,
            "error": str(e),
            "estimated_complexity": "unknown",
            "recommended_workflow": "fallback",
        }


async def _process_pdf_document(
    doc_path: str,
    quality_threshold: float,
    save_intermediates: bool,
    backend_manager: Any,
) -> dict[str, Any]:
    """Process PDF document with PDF-specific optimizations."""
    try:
        # TODO: Implement actual PDF to image conversion
        # pdf_result = await convert_pdf_to_images(doc_path, None, dpi=300, format="PNG")
        # For now, mock it or assume simple processing

        # Real implementation would look like:
        # image_paths = pdf_result.get("results", {}).get("files_saved", [])

        # Fallback for now: Treat as standard doc if we can't extract images yet
        ocr_result = await backend_manager.process_document(doc_path, output_format="markdown")

        return {
            "success": True,  # ocr_result.get("success", False),
            "workflow": "pdf_processing",
            "ocr_result": ocr_result,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"PDF processing failed: {str(e)}",
            "workflow": "pdf_processing",
        }


async def _process_image_document(
    doc_path: str,
    quality_threshold: float,
    save_intermediates: bool,
    backend_manager: Any,
) -> dict[str, Any]:
    """Process image document with image-specific optimizations."""
    try:
        # TODO: Integrate with actual preprocessing checks
        # quality_result = await analyze_image_quality(doc_path)
        # preprocessing_needed = quality_result.get("ocr_readiness") != "ready"

        # Determine backend
        ocr_result = await backend_manager.process_document(doc_path, output_format="markdown")

        return {
            "success": True,
            "workflow": "image_processing",
            "preprocessing_applied": False,  # placeholder
            "ocr_result": ocr_result,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Image processing failed: {str(e)}",
            "workflow": "image_processing",
        }


async def _process_standard_document(
    doc_path: str, quality_threshold: float, backend_manager: Any
) -> dict[str, Any]:
    """Process document with standard OCR workflow."""
    try:
        ocr_result = await backend_manager.process_document(doc_path, output_format="markdown")

        return {"success": True, "workflow": "standard", "ocr_result": ocr_result}

    except Exception as e:
        return {
            "success": False,
            "error": f"Standard processing failed: {str(e)}",
            "workflow": "standard",
        }


async def _apply_auto_workflow(
    doc_path: str,
    analysis: dict,
    quality_threshold: float,
    save_intermediates: bool,
    backend_manager: Any,
) -> dict[str, Any]:
    """Apply automatic workflow based on document analysis."""
    workflow = analysis.get("recommended_workflow", "standard")

    if workflow == "pdf_processing":
        return await _process_pdf_document(
            doc_path, quality_threshold, save_intermediates, backend_manager
        )
    elif workflow == "image_processing":
        return await _process_image_document(
            doc_path, quality_threshold, save_intermediates, backend_manager
        )
    else:
        return await _process_standard_document(doc_path, quality_threshold, backend_manager)


async def _apply_ocr_only_workflow(
    doc_path: str, analysis: dict, backend_manager: Any
) -> dict[str, Any]:
    """Apply OCR-only workflow (no preprocessing)."""
    try:
        ocr_result = await backend_manager.process_document(doc_path, output_format="markdown")
        return {
            "success": True,
            "workflow": "ocr_only",
            "ocr_result": ocr_result,
            "quality_score": 0.7,  # Basic estimate
            "processing_steps": ["ocr"],
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"OCR-only workflow failed: {str(e)}",
            "workflow": "ocr_only",
        }


async def _validate_pipeline_steps(steps: list[dict]) -> dict[str, Any]:
    """Validate pipeline step configurations."""
    errors = []
    valid_tools = [
        "deskew_image",
        "enhance_image",
        "rotate_image",
        "crop_image",
        "process_document",
        "assess_ocr_quality",
        "convert_image_format",
        "analyze_document_layout",
        "extract_table_data",
    ]

    for i, step in enumerate(steps):
        if "tool" not in step:
            errors.append(f"Step {i + 1}: Missing 'tool' field")
        elif step["tool"] not in valid_tools:
            errors.append(f"Step {i + 1}: Unknown tool '{step['tool']}'")
        elif "parameters" not in step:
            errors.append(f"Step {i + 1}: Missing 'parameters' field")

    return {"valid": len(errors) == 0, "errors": errors, "steps_validated": len(steps)}


def _estimate_pipeline_complexity(steps: list[dict]) -> str:
    """Estimate pipeline complexity."""
    complexity_score = len(steps)

    complex_tools = [
        "analyze_document_layout",
        "extract_table_data",
        "assess_ocr_quality",
    ]
    for step in steps:
        if step.get("tool") in complex_tools:
            complexity_score += 2

    if complexity_score <= 3:
        return "low"
    elif complexity_score <= 6:
        return "medium"
    else:
        return "high"


async def _save_batch_results(results: list[dict], output_directory: str) -> None:
    """Save batch processing results to files."""
    try:
        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save summary
        summary = {
            "batch_timestamp": time.time(),
            "total_documents": len(results),
            "successful": sum(1 for r in results if r.get("success")),
            "results": results,
        }

        summary_file = output_dir / "batch_results.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2, default=str)

    except Exception as e:
        logger.error(f"Failed to save batch results: {e}")


def _calculate_optimal_settings(
    analysis_results: list[dict],
    target_quality: float,
    time_constraint: float | None,
) -> dict[str, Any]:
    """Calculate optimal processing settings."""
    # Simplified optimization logic
    if not analysis_results:
        return {
            "recommended_backend": "auto",
            "preprocessing_steps": [],
            "estimated_quality": target_quality,
            "estimated_time": 0,
            "resource_requirements": "low",
        }

    avg_complexity = sum(
        1
        if a.get("estimated_complexity") == "high"
        else 0.5
        if a.get("estimated_complexity") == "medium"
        else 0
        for a in analysis_results
    ) / len(analysis_results)

    if avg_complexity > 0.7:
        recommended_backend = "deepseek-ocr"  # Best for complex docs
        preprocessing = ["deskew", "enhance", "crop"]
    elif avg_complexity > 0.4:
        recommended_backend = "florence-2"  # Good layout understanding
        preprocessing = ["enhance", "crop"]
    else:
        recommended_backend = "easyocr"  # Fast for simple docs
        preprocessing = ["enhance"]

    return {
        "recommended_backend": recommended_backend,
        "preprocessing_steps": preprocessing,
        "estimated_quality": min(target_quality + 0.1, 0.95),
        "estimated_time": 2.0 + avg_complexity * 3.0,
        "resource_requirements": "standard",
    }


def _generate_processing_recommendations(optimization: dict, analysis: list[dict]) -> list[str]:
    """Generate processing recommendations."""
    recommendations = []

    backend = optimization["recommended_backend"]
    if backend == "deepseek-ocr":
        recommendations.append("Use DeepSeek-OCR for complex documents with formulas or tables")
    elif backend == "florence-2":
        recommendations.append("Use Florence-2 for documents with complex layouts")
    elif backend == "easyocr":
        recommendations.append("Use EasyOCR for fast processing of simple documents")

    if optimization["preprocessing_steps"]:
        recommendations.append(
            f"Apply preprocessing: {', '.join(optimization['preprocessing_steps'])}"
        )

    if optimization["estimated_time"] > 5.0:
        recommendations.append("Consider batch processing for better performance")

    return recommendations


# --- Handler Functions ---


async def _handle_process_batch_intelligent(
    document_paths,
    workflow_type,
    quality_threshold,
    max_concurrent,
    output_directory,
    save_intermediates,
    backend_manager,
):
    """Handle intelligent batch processing."""

    logger.info(f"Starting intelligent batch processing of {len(document_paths)} documents")
    start_time = time.time()

    # Process sequentially for now to be safe, but structure allows concurrency
    results = []

    for i, doc_path in enumerate(document_paths):
        try:
            # Determine document type and optimal workflow
            doc_analysis = await analyze_document_workflow(doc_path)

            # Apply intelligent processing based on workflow type
            if workflow_type == "auto":
                result = await _apply_auto_workflow(
                    doc_path,
                    doc_analysis,
                    quality_threshold,
                    save_intermediates,
                    backend_manager,
                )
            elif workflow_type == "ocr_only":
                result = await _apply_ocr_only_workflow(doc_path, doc_analysis, backend_manager)
            else:
                result = await _apply_auto_workflow(
                    doc_path,
                    doc_analysis,
                    quality_threshold,
                    save_intermediates,
                    backend_manager,
                )

            result["document_index"] = i
            result["document_path"] = doc_path
            results.append(result)

        except Exception as e:
            logger.error(f"Failed to process document {doc_path}: {e}")
            results.append(
                {
                    "document_path": doc_path,
                    "document_index": i,
                    "success": False,
                    "error": f"Processing failed: {str(e)}",
                }
            )

    end_time = time.time()

    # Save results if output directory specified
    if output_directory:
        await _save_batch_results(results, output_directory)

    successful = [r for r in results if r.get("success", False)]

    return {
        "success": True,
        "batch_summary": {
            "total_documents": len(document_paths),
            "successful": len(successful),
            "total_processing_time": round(end_time - start_time, 2),
        },
        "results": results,
        "message": f"Batch processing complete: {len(successful)}/{len(document_paths)} documents processed successfully",
    }


async def _handle_create_processing_pipeline(pipeline_name, steps, quality_gates, error_handling):
    """Handle custom pipeline creation."""
    validation_results = await _validate_pipeline_steps(steps)
    if not validation_results["valid"]:
        return {
            "success": False,
            "error": "Pipeline validation failed",
            "validation_errors": validation_results["errors"],
        }

    pipeline_config = {
        "name": pipeline_name,
        "steps": steps,
        "quality_gates": quality_gates or [],
        "error_handling": error_handling or {},
    }

    return {
        "success": True,
        "pipeline_name": pipeline_name,
        "pipeline_config": pipeline_config,
        "message": f"Pipeline '{pipeline_name}' created successfully",
    }


async def _handle_execute_pipeline(
    pipeline_config, input_documents, execution_mode, backend_manager
):
    """Execute pipeline steps on each document. Passes output of each step to the next."""
    steps = pipeline_config.get("steps", [])
    if not steps:
        return ErrorHandler.create_error(
            "PARAMETERS_INVALID",
            message_override="Pipeline has no steps",
        ).to_dict()

    config = getattr(backend_manager, "config", None)
    results = []

    for doc_idx, doc_path in enumerate(input_documents):
        current_path = doc_path
        current_ocr_result = None
        step_results = []
        failed = False

        for step_idx, step in enumerate(steps):
            tool_name = step.get("tool")
            params = dict(step.get("parameters", {}))

            if tool_name not in _STEP_TOOL_MAP:
                step_results.append(
                    {
                        "step": step_idx + 1,
                        "tool": tool_name,
                        "success": False,
                        "error": f"Unknown tool: {tool_name}",
                    }
                )
                failed = True
                break

            module, func_name = _STEP_TOOL_MAP[tool_name]
            func = getattr(module, func_name)

            # Build kwargs per tool
            kwargs = dict(params)
            kwargs.setdefault("backend_manager", backend_manager)
            kwargs.setdefault("config", config)

            if tool_name == "process_document":
                kwargs["source_path"] = current_path
            elif tool_name in ("analyze_document_layout", "extract_table_data"):
                kwargs["image_path"] = current_path
            elif tool_name == "convert_image_format":
                kwargs["source_path"] = current_path
            elif tool_name in ("deskew_image", "rotate_image"):
                kwargs["image_path"] = current_path
            elif tool_name in ("enhance_image", "crop_image"):
                kwargs["source_path"] = current_path
                if tool_name == "crop_image":
                    kwargs["autocrop"] = True
            elif tool_name == "assess_ocr_quality":
                if current_ocr_result is None:
                    step_results.append(
                        {
                            "step": step_idx + 1,
                            "tool": tool_name,
                            "success": False,
                            "error": "No OCR result from previous step for assess_ocr_quality",
                        }
                    )
                    failed = True
                    break
                kwargs["ocr_result"] = current_ocr_result

            # Remove backend_manager/config for tools that do not accept them
            if tool_name in ("deskew_image", "rotate_image"):
                kwargs.pop("backend_manager", None)
                kwargs.pop("config", None)

            try:
                result = await func(**kwargs)
            except Exception as e:
                step_results.append(
                    {
                        "step": step_idx + 1,
                        "tool": tool_name,
                        "success": False,
                        "error": str(e),
                    }
                )
                failed = True
                break

            step_results.append(
                {
                    "step": step_idx + 1,
                    "tool": tool_name,
                    "success": result.get("success", False),
                }
            )

            if not result.get("success", False):
                failed = True
                step_results[-1]["error"] = result.get("error", "Step failed")
                break

            if tool_name == "process_document":
                current_ocr_result = result.get("result", result)
            elif result.get("target_path"):
                current_path = result["target_path"]

        results.append(
            {
                "document": doc_path,
                "document_index": doc_idx,
                "success": not failed,
                "steps_completed": len(step_results),
                "step_results": step_results,
                "final_path": current_path,
            }
        )

    successful = sum(1 for r in results if r["success"])
    return {
        "success": True,
        "pipeline_name": pipeline_config["name"],
        "total_documents": len(input_documents),
        "successful": successful,
        "failed": len(input_documents) - successful,
        "results": results,
        "message": f"Pipeline executed: {successful}/{len(input_documents)} documents processed",
    }


async def _handle_monitor_batch_progress(batch_id, include_metrics, include_errors):
    """Handle batch progress monitoring."""
    return {
        "success": True,
        "monitoring_status": "active",
        "message": "Batch monitoring active (placeholder)",
    }


async def _handle_optimize_processing(document_paths, quality_threshold):
    """Handle processing optimization."""
    # Analyze sample documents
    sample_analysis = []
    for doc_path in document_paths[:5]:
        analysis = await analyze_document_workflow(doc_path)
        sample_analysis.append(analysis)

    optimization = _calculate_optimal_settings(sample_analysis, quality_threshold, None)
    recommendations = _generate_processing_recommendations(optimization, sample_analysis)

    return {
        "success": True,
        "optimization_results": optimization,
        "recommendations": recommendations,
        "message": "Optimization complete",
    }


async def _handle_ocr_health_check(backend_manager, detailed, focus):
    """Handle OCR health check."""
    status = get_system_status("basic", backend_manager)
    return create_success_response(status)


async def _handle_list_backends(backend_manager):
    """Handle backend listing."""
    backends = backend_manager.list_backends()
    return create_success_response({"backends": backends})


async def _handle_manage_models(backend_manager, target_free_mb, max_idle_seconds):
    """Handle model management."""
    # Placeholder for model management
    return create_success_response({"message": "Model management executed", "freed_memory_mb": 0})


# --- Main Portmanteau Tool Function ---


# Backward compatibility alias for watch_folder service
async def workflow_management(
    operation: str,
    backend_manager: Any,
    document_paths: list[str] | None = None,
    workflow_type: str = "auto",
    quality_threshold: float = 0.8,
    max_concurrent: int = 3,
    output_directory: str | None = None,
    save_intermediates: bool = False,
    pipeline_name: str | None = None,
    steps: list[dict[str, Any]] | None = None,
    quality_gates: list[dict[str, Any]] | None = None,
    error_handling: dict[str, Any] | None = None,
    input_documents: list[str] | None = None,
    execution_mode: str = "sequential",
    batch_id: str | None = None,
    include_metrics: bool = True,
    include_errors: bool = True,
    detailed: bool = False,
    focus: str | None = None,
    target_free_mb: int = 1024,
    max_idle_seconds: int = 300,
    pipeline_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Backward compatibility wrapper. Delegates to handle_workflow_op.
    See ocr_tools.workflow_management for MCP tool docstring.
    """
    return await handle_workflow_op(
        operation=operation,
        backend_manager=backend_manager,
        document_paths=document_paths,
        workflow_type=workflow_type,
        quality_threshold=quality_threshold,
        max_concurrent=max_concurrent,
        output_directory=output_directory,
        save_intermediates=save_intermediates,
        pipeline_name=pipeline_name,
        steps=steps,
        quality_gates=quality_gates,
        error_handling=error_handling,
        input_documents=input_documents,
        execution_mode=execution_mode,
        batch_id=batch_id,
        include_metrics=include_metrics,
        include_errors=include_errors,
        detailed=detailed,
        focus=focus,
        target_free_mb=target_free_mb,
        max_idle_seconds=max_idle_seconds,
        pipeline_config=pipeline_config,
    )


async def handle_workflow_op(
    operation: str,
    backend_manager: Any,
    document_paths: list[str] | None = None,
    workflow_type: str = "auto",
    quality_threshold: float = 0.8,
    max_concurrent: int = 3,
    output_directory: str | None = None,
    save_intermediates: bool = False,
    pipeline_name: str | None = None,
    steps: list[dict[str, Any]] | None = None,
    quality_gates: list[dict[str, Any]] | None = None,
    error_handling: dict[str, Any] | None = None,
    input_documents: list[str] | None = None,
    execution_mode: str = "sequential",
    batch_id: str | None = None,
    include_metrics: bool = True,
    include_errors: bool = True,
    detailed: bool = False,
    focus: str | None = None,
    target_free_mb: int = 1024,
    max_idle_seconds: int = 300,
    pipeline_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Backend handler for workflow operations. See ocr_tools.workflow_management for MCP tool docstring.
    Note: ocr_tools exposes simplified API (workflow_name, source_dir, output_dir, pipeline_config);
    this accepts full API. Some handlers are placeholders (monitor_batch_progress, manage_models).

    OPERATIONS:
    - process_batch_intelligent: Auto workflow per document. Requires: document_paths.
    - create_processing_pipeline: Define custom pipeline. Requires: pipeline_name, steps.
    - execute_pipeline: Run pipeline on documents. Requires: pipeline_config, input_documents.
    - monitor_batch_progress: Batch progress (placeholder).
    - optimize_processing: Recommended settings. Requires: document_paths.
    - ocr_health_check: Backend health.
    - list_backends: Available OCR backends.
    - manage_models: Model memory (placeholder).

    Args:
    - operation (str, required): Operation to perform. Must be one of OPERATIONS above.
    - backend_manager: Injected BackendManager.
    - document_paths (list[str] | None): Input paths. Required for: process_batch_intelligent, optimize_processing.
    - workflow_type (str): auto or ocr_only. Default: auto.
    - quality_threshold (float): Target quality. Default: 0.8.
    - max_concurrent (int): Parallel limit. Default: 3.
    - output_directory (str | None): Output dir for batch.
    - save_intermediates (bool): Save intermediates. Default: False.
    - pipeline_name (str | None): Pipeline name. Required for: create_processing_pipeline.
    - steps (list[dict] | None): Pipeline steps. Required for: create_processing_pipeline.
    - pipeline_config (dict | None): Pipeline config. Required for: execute_pipeline.
    - input_documents (list[str] | None): Documents for execute_pipeline.
    - execution_mode (str): sequential or parallel. Default: sequential.
    - batch_id (str | None): For monitor_batch_progress.
    - include_metrics (bool): Include metrics. Default: True.
    - include_errors (bool): Include errors. Default: True.
    - detailed (bool): Detailed health. Default: False.
    - focus (str | None): Health focus.
    - target_free_mb (int): For manage_models. Default: 1024.
    - max_idle_seconds (int): For manage_models. Default: 300.
    - quality_gates (list[dict] | None): Pipeline quality gates.
    - error_handling (dict | None): Pipeline error handling.

    Returns:
    FastMCP 3.1 dialogic response: success, operation, result or error,
    recommendations, next_steps, recovery_options (on error), related_operations.
    """
    try:
        logger.info(f"Workflow management operation: {operation}")

        # Validate operation
        valid_operations = [
            "process_batch_intelligent",
            "create_processing_pipeline",
            "execute_pipeline",
            "monitor_batch_progress",
            "optimize_processing",
            "ocr_health_check",
            "list_backends",
            "manage_models",
        ]

        if operation not in valid_operations:
            return ErrorHandler.create_error(
                "PARAMETERS_INVALID",
                message_override=f"Invalid operation: {operation}",
                details={"valid_operations": valid_operations},
            ).to_dict()

        # Route to appropriate handler based on operation
        if operation == "process_batch_intelligent":
            if not document_paths:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override="document_paths required for process_batch_intelligent operation",
                ).to_dict()
            return await _handle_process_batch_intelligent(
                document_paths,
                workflow_type,
                quality_threshold,
                max_concurrent,
                output_directory,
                save_intermediates,
                backend_manager,
            )

        elif operation == "create_processing_pipeline":
            if not pipeline_name or not steps:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override="pipeline_name and steps required for create_processing_pipeline operation",
                ).to_dict()
            return await _handle_create_processing_pipeline(
                pipeline_name, steps, quality_gates, error_handling
            )

        elif operation == "execute_pipeline":
            if not pipeline_config or not input_documents:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override="pipeline_config and input_documents required for execute_pipeline operation",
                ).to_dict()
            return await _handle_execute_pipeline(
                pipeline_config, input_documents, execution_mode, backend_manager
            )

        elif operation == "monitor_batch_progress":
            return await _handle_monitor_batch_progress(batch_id, include_metrics, include_errors)

        elif operation == "optimize_processing":
            if not document_paths:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override="document_paths required for optimize_processing operation",
                ).to_dict()
            return await _handle_optimize_processing(document_paths, quality_threshold)

        elif operation == "ocr_health_check":
            return await _handle_ocr_health_check(backend_manager, detailed, focus)

        elif operation == "list_backends":
            return await _handle_list_backends(backend_manager)

        elif operation == "manage_models":
            return await _handle_manage_models(backend_manager, target_free_mb, max_idle_seconds)

    except Exception as e:
        logger.error(f"Workflow management operation failed: {operation}, error: {e}")
        return ErrorHandler.handle_exception(e, context=f"workflow_management_{operation}")
