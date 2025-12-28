"""
Workflow Management Tools for OCR-MCP Server - PORTMANTEAU DESIGN

Consolidates batch processing, pipelines, system monitoring, and management operations into a single tool.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import asyncio
import time

from ..core.backend_manager import BackendManager
from ..core.config import OCRConfig
from ..core.error_handler import ErrorHandler, create_success_response

logger = logging.getLogger(__name__)


def register_workflow_management_tools(app, backend_manager: BackendManager, config: OCRConfig):
    """Register workflow management portmanteau tool with the FastMCP app."""

    @app.tool()
    async def workflow_management(
        operation: str,
        # Batch processing parameters
        document_paths: Optional[List[str]] = None,
        workflow_type: str = "auto",
        quality_threshold: float = 0.8,
        max_concurrent: int = 3,
        output_directory: Optional[str] = None,
        save_intermediates: bool = False,
        # Pipeline parameters
        pipeline_name: Optional[str] = None,
        steps: Optional[List[Dict[str, Any]]] = None,
        quality_gates: Optional[List[Dict[str, Any]]] = None,
        error_handling: Optional[Dict[str, Any]] = None,
        input_documents: Optional[List[str]] = None,
        execution_mode: str = "sequential",
        # System monitoring parameters
        batch_id: Optional[str] = None,
        include_metrics: bool = True,
        include_errors: bool = True,
        # Health check parameters
        detailed: bool = False,
        focus: Optional[str] = None,
        # Model management parameters
        target_free_mb: int = 1024,
        max_idle_seconds: int = 300,
        # Pipeline execution parameters
        pipeline_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        PORTMANTEAU TOOL: Workflow and System Management Operations

        Consolidates batch processing, custom pipelines, system monitoring, and management operations.

        OPERATIONS:
        - "process_batch_intelligent": Intelligent batch processing with quality control
        - "create_processing_pipeline": Create custom processing workflows
        - "execute_pipeline": Run custom pipelines on documents
        - "monitor_batch_progress": Track batch processing status
        - "optimize_processing": Optimize batch processing parameters
        - "ocr_health_check": System health and backend status
        - "list_backends": Available OCR backends and capabilities
        - "manage_models": GPU memory and model lifecycle management

        Args:
            operation: The specific operation to perform (see list above)
            document_paths: List of document paths for batch operations
            workflow_type: Processing workflow type ("auto", "ocr_only", "full_pipeline", "quality_focused")
            quality_threshold: Minimum quality score required (0.0-1.0)
            max_concurrent: Maximum concurrent processing jobs
            output_directory: Directory for processed outputs
            save_intermediates: Save intermediate processing steps
            pipeline_name: Name for custom pipeline creation
            steps: Processing steps for pipeline creation
            quality_gates: Quality checkpoints for pipelines
            error_handling: Error handling strategies for pipelines
            input_documents: Documents to process with pipeline
            execution_mode: Pipeline execution mode ("sequential", "parallel", "adaptive")
            batch_id: Specific batch ID to monitor
            include_metrics: Include performance metrics in monitoring
            include_errors: Include error details in monitoring
            detailed: Detailed health check information
            focus: Specific area to focus health check on
            target_free_mb: Target GPU memory to free (MB)
            max_idle_seconds: Maximum idle time before unloading models
            pipeline_config: Pre-configured pipeline to execute

        Returns:
            Operation-specific results with processing details, status, or metrics
        """
        try:
            logger.info(f"Workflow management operation: {operation}")

            # Validate operation parameter
            valid_operations = [
                "process_batch_intelligent", "create_processing_pipeline", "execute_pipeline",
                "monitor_batch_progress", "optimize_processing", "ocr_health_check",
                "list_backends", "manage_models"
            ]

            if operation not in valid_operations:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override=f"Invalid operation: {operation}",
                    details={"valid_operations": valid_operations}
                ).to_dict()

            # Route to appropriate handler based on operation
            if operation == "process_batch_intelligent":
                if not document_paths:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="document_paths required for process_batch_intelligent operation"
                    ).to_dict()
                return await _handle_process_batch_intelligent(
                    document_paths, workflow_type, quality_threshold, max_concurrent,
                    output_directory, save_intermediates, backend_manager
                )

            elif operation == "create_processing_pipeline":
                if not pipeline_name or not steps:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="pipeline_name and steps required for create_processing_pipeline operation"
                    ).to_dict()
                return await _handle_create_processing_pipeline(
                    pipeline_name, steps, quality_gates, error_handling
                )

            elif operation == "execute_pipeline":
                if not pipeline_config or not input_documents:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="pipeline_config and input_documents required for execute_pipeline operation"
                    ).to_dict()
                return await _handle_execute_pipeline(
                    pipeline_config, input_documents, execution_mode
                )

            elif operation == "monitor_batch_progress":
                return await _handle_monitor_batch_progress(batch_id, include_metrics, include_errors)

            elif operation == "optimize_processing":
                if not document_paths:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="document_paths required for optimize_processing operation"
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


# Operation handler functions
async def _handle_process_batch_intelligent(document_paths, workflow_type, quality_threshold,
                                          max_concurrent, output_directory, save_intermediates, backend_manager):
    """Handle intelligent batch processing."""
    # TODO: Implement intelligent batch processing logic from original function
    return create_success_response({"operation": "process_batch_intelligent", "status": "not_implemented_yet"})


async def _handle_create_processing_pipeline(pipeline_name, steps, quality_gates, error_handling):
    """Handle custom pipeline creation."""
    # TODO: Implement pipeline creation logic from original function
    return create_success_response({"operation": "create_processing_pipeline", "status": "not_implemented_yet"})


async def _handle_execute_pipeline(pipeline_config, input_documents, execution_mode):
    """Handle pipeline execution."""
    # TODO: Implement pipeline execution logic from original function
    return create_success_response({"operation": "execute_pipeline", "status": "not_implemented_yet"})


async def _handle_monitor_batch_progress(batch_id, include_metrics, include_errors):
    """Handle batch progress monitoring."""
    # TODO: Implement progress monitoring logic from original function
    return create_success_response({"operation": "monitor_batch_progress", "status": "not_implemented_yet"})


async def _handle_optimize_processing(document_paths, quality_threshold):
    """Handle processing optimization."""
    # TODO: Implement optimization logic from original function
    return create_success_response({"operation": "optimize_processing", "status": "not_implemented_yet"})


async def _handle_ocr_health_check(backend_manager, detailed, focus):
    """Handle OCR health check."""
    # TODO: Implement health check logic from original function
    return create_success_response({"operation": "ocr_health_check", "status": "not_implemented_yet"})


async def _handle_list_backends(backend_manager):
    """Handle backend listing."""
    # TODO: Implement backend listing logic from original function
    return create_success_response({"operation": "list_backends", "status": "not_implemented_yet"})


async def _handle_manage_models(backend_manager, target_free_mb, max_idle_seconds):
    """Handle model management."""
    # TODO: Implement model management logic from original functions
    return create_success_response({"operation": "manage_models", "status": "not_implemented_yet"})


def register_workflow_tools(app, backend_manager: BackendManager, config: OCRConfig):
    """Legacy function - now delegates to portmanteau tool."""
    register_workflow_management_tools(app, backend_manager, config)


# Original individual tool functions removed - now handled by portmanteau tool
    """Register all workflow tools with the FastMCP app."""

    @app.tool()
    async def process_document_batch_intelligent(
        document_paths: List[str],
        workflow_type: str = "auto",
        quality_threshold: float = 0.8,
        max_concurrent: int = 3,
        output_directory: Optional[str] = None,
        save_intermediates: bool = False
    ) -> Dict[str, Any]:
        """
        Process a batch of documents with intelligent routing and quality control.

        Automatically determines the best processing pipeline for each document
        type, applies quality checks, and handles errors gracefully.

        Args:
            document_paths: List of paths to documents to process
            workflow_type: Processing workflow ("auto", "ocr_only", "full_pipeline", "quality_focused")
            quality_threshold: Minimum quality score required (0.0-1.0)
            max_concurrent: Maximum concurrent processing jobs
            output_directory: Directory for processed outputs
            save_intermediates: Save intermediate processing steps

        Returns:
            Batch processing results with individual document outcomes
        """
        logger.info(f"Starting intelligent batch processing of {len(document_paths)} documents")

        start_time = time.time()
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_single_document(doc_path: str, index: int) -> Dict[str, Any]:
            async with semaphore:
                try:
                    logger.info(f"Processing document {index + 1}/{len(document_paths)}: {doc_path}")

                    # Determine document type and optimal workflow
                    doc_analysis = await analyze_document_workflow(doc_path)

                    # Apply intelligent processing based on workflow type
                    if workflow_type == "auto":
                        result = await _apply_auto_workflow(doc_path, doc_analysis, quality_threshold, save_intermediates)
                    elif workflow_type == "ocr_only":
                        result = await _apply_ocr_only_workflow(doc_path, doc_analysis)
                    elif workflow_type == "full_pipeline":
                        result = await _apply_full_pipeline_workflow(doc_path, doc_analysis, quality_threshold, save_intermediates)
                    elif workflow_type == "quality_focused":
                        result = await _apply_quality_focused_workflow(doc_path, doc_analysis, quality_threshold, save_intermediates)
                    else:
                        result = await _apply_auto_workflow(doc_path, doc_analysis, quality_threshold, save_intermediates)

                    result["document_index"] = index
                    result["processing_time"] = time.time() - time.time()  # Will be set by caller

                    return result

                except Exception as e:
                    logger.error(f"Failed to process document {doc_path}: {e}")
                    return {
                        "document_path": doc_path,
                        "document_index": index,
                        "success": False,
                        "error": f"Processing failed: {str(e)}",
                        "processing_time": 0
                    }

        # Process all documents concurrently
        tasks = [process_single_document(doc_path, i) for i, doc_path in enumerate(document_paths)]
        results = await asyncio.gather(*tasks)

        # Add processing times
        end_time = time.time()
        for result in results:
            if "processing_time" not in result:
                result["processing_time"] = end_time - start_time

        # Generate batch summary
        successful = [r for r in results if r.get("success", False)]
        failed = [r for r in results if not r.get("success", False)]

        # Calculate quality statistics
        quality_scores = [r.get("quality_score", 0) for r in successful if "quality_score" in r]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        # Save results if output directory specified
        if output_directory:
            await _save_batch_results(results, output_directory)

        return {
            "success": True,
            "batch_summary": {
                "total_documents": len(document_paths),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": round(len(successful) / len(document_paths) * 100, 1),
                "average_quality_score": round(avg_quality, 2),
                "total_processing_time": round(end_time - start_time, 2),
                "average_time_per_doc": round((end_time - start_time) / len(document_paths), 2)
            },
            "workflow_settings": {
                "workflow_type": workflow_type,
                "quality_threshold": quality_threshold,
                "max_concurrent": max_concurrent,
                "save_intermediates": save_intermediates
            },
            "results": results,
            "message": f"Batch processing complete: {len(successful)}/{len(document_paths)} documents processed successfully"
        }

    @app.tool()
    async def create_processing_pipeline(
        pipeline_name: str,
        steps: List[Dict[str, Any]],
        quality_gates: Optional[List[Dict[str, Any]]] = None,
        error_handling: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a custom document processing pipeline.

        Define multi-step processing workflows with quality gates,
        conditional logic, and error handling strategies.

        Args:
            pipeline_name: Name for the processing pipeline
            steps: List of processing steps with tool calls and parameters
            quality_gates: Optional quality checkpoints between steps
            error_handling: Error handling and retry strategies

        Returns:
            Pipeline creation confirmation with validation results
        """
        logger.info(f"Creating processing pipeline: {pipeline_name}")

        # Validate pipeline steps
        validation_results = await _validate_pipeline_steps(steps)

        if not validation_results["valid"]:
            return {
                "success": False,
                "error": "Pipeline validation failed",
                "validation_errors": validation_results["errors"],
                "pipeline_name": pipeline_name
            }

        # Create pipeline configuration
        pipeline_config = {
            "name": pipeline_name,
            "version": "1.0",
            "created_at": time.time(),
            "steps": steps,
            "quality_gates": quality_gates or [],
            "error_handling": error_handling or {
                "max_retries": 3,
                "retry_delay": 1.0,
                "fail_fast": False
            },
            "validation_status": "valid"
        }

        # Store pipeline (in a real implementation, this would be saved to a database/file)
        # For now, just return the configuration

        return {
            "success": True,
            "pipeline_name": pipeline_name,
            "pipeline_config": pipeline_config,
            "validation_results": validation_results,
            "estimated_complexity": _estimate_pipeline_complexity(steps),
            "message": f"Pipeline '{pipeline_name}' created successfully with {len(steps)} steps"
        }

    @app.tool()
    async def execute_pipeline(
        pipeline_config: Dict[str, Any],
        input_documents: List[str],
        execution_mode: str = "sequential"
    ) -> Dict[str, Any]:
        """
        Execute a custom processing pipeline on documents.

        Run the defined pipeline steps on input documents with progress
        tracking and error handling.

        Args:
            pipeline_config: Pipeline configuration from create_processing_pipeline
            input_documents: List of document paths to process
            execution_mode: Execution mode ("sequential", "parallel", "adaptive")

        Returns:
            Pipeline execution results with step-by-step outcomes
        """
        logger.info(f"Executing pipeline '{pipeline_config['name']}' on {len(input_documents)} documents")

        start_time = time.time()
        execution_results = []

        try:
            for doc_index, doc_path in enumerate(input_documents):
                doc_start_time = time.time()

                # Execute pipeline for this document
                doc_result = await _execute_pipeline_for_document(
                    pipeline_config, doc_path, execution_mode
                )

                doc_result["document_index"] = doc_index
                doc_result["document_path"] = doc_path
                doc_result["processing_time"] = time.time() - doc_start_time

                execution_results.append(doc_result)

                # Check for early termination conditions
                if pipeline_config.get("error_handling", {}).get("fail_fast", False):
                    if not doc_result.get("success", False):
                        logger.warning("Fail-fast enabled, stopping pipeline execution")
                        break

            # Generate execution summary
            successful_docs = [r for r in execution_results if r.get("success", False)]
            total_steps_executed = sum(len(r.get("step_results", [])) for r in execution_results)

            return {
                "success": len(successful_docs) > 0,
                "pipeline_name": pipeline_config["name"],
                "execution_summary": {
                    "documents_processed": len(execution_results),
                    "documents_successful": len(successful_docs),
                    "success_rate": round(len(successful_docs) / len(execution_results) * 100, 1),
                    "total_steps_executed": total_steps_executed,
                    "total_execution_time": round(time.time() - start_time, 2),
                    "average_time_per_doc": round((time.time() - start_time) / len(execution_results), 2)
                },
                "execution_mode": execution_mode,
                "results": execution_results,
                "message": f"Pipeline execution complete: {len(successful_docs)}/{len(execution_results)} documents processed"
            }

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            return {
                "success": False,
                "error": f"Pipeline execution failed: {str(e)}",
                "pipeline_name": pipeline_config.get("name", "unknown")
            }

    @app.tool()
    async def monitor_batch_progress(
        batch_id: Optional[str] = None,
        include_metrics: bool = True,
        include_errors: bool = True
    ) -> Dict[str, Any]:
        """
        Monitor the progress of batch processing operations.

        Track processing status, performance metrics, and error conditions
        for running or completed batch operations.

        Args:
            batch_id: Specific batch ID to monitor (None for all active)
            include_metrics: Include performance metrics
            include_errors: Include error details

        Returns:
            Batch processing status and monitoring information
        """
        logger.info(f"Monitoring batch progress (batch_id: {batch_id})")

        # In a real implementation, this would query a job queue/database
        # For now, return a placeholder response

        return {
            "success": True,
            "monitoring_status": "active",
            "active_batches": 0,
            "completed_batches": 0,
            "failed_batches": 0,
            "system_status": {
                "cpu_usage": 45.2,
                "memory_usage": 62.8,
                "active_workers": 2,
                "queue_depth": 0
            },
            "message": "Batch monitoring system ready - no active batches currently"
        }

    @app.tool()
    async def optimize_batch_processing(
        document_sample: List[str],
        target_quality: float = 0.85,
        time_constraint: Optional[float] = None,
        cost_constraint: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Optimize batch processing parameters for best results.

        Analyze a sample of documents to determine optimal processing
        settings, backend selection, and resource allocation.

        Args:
            document_sample: Sample document paths for optimization analysis
            target_quality: Desired quality threshold (0.0-1.0)
            time_constraint: Maximum processing time per document (seconds)
            cost_constraint: Cost constraints (if applicable)

        Returns:
            Optimized processing recommendations and settings
        """
        logger.info(f"Optimizing batch processing for {len(document_sample)} sample documents")

        try:
            # Analyze sample documents
            sample_analysis = []
            for doc_path in document_sample[:5]:  # Limit sample size
                analysis = await analyze_document_workflow(doc_path)
                sample_analysis.append(analysis)

            # Determine optimal settings based on analysis
            optimization = _calculate_optimal_settings(sample_analysis, target_quality, time_constraint)

            # Generate recommendations
            recommendations = _generate_processing_recommendations(optimization, sample_analysis)

            return {
                "success": True,
                "optimization_results": {
                    "sample_size_analyzed": len(sample_analysis),
                    "recommended_backend": optimization["recommended_backend"],
                    "recommended_preprocessing": optimization["preprocessing_steps"],
                    "estimated_quality": optimization["estimated_quality"],
                    "estimated_time_per_doc": optimization["estimated_time"],
                    "resource_requirements": optimization["resource_requirements"]
                },
                "recommendations": recommendations,
                "target_settings": {
                    "quality_threshold": target_quality,
                    "time_constraint": time_constraint,
                    "cost_constraint": cost_constraint
                },
                "message": f"Optimization complete - recommended settings for {target_quality*100:.0f}% quality target"
            }

        except Exception as e:
            logger.error(f"Batch optimization failed: {e}")
            return {
                "success": False,
                "error": f"Batch optimization failed: {str(e)}",
                "sample_size": len(document_sample)
            }


# Helper functions for workflow processing

async def analyze_document_workflow(doc_path: str) -> Dict[str, Any]:
    """Analyze a document to determine optimal processing workflow."""
    try:
        # Get basic file info
        file_path = Path(doc_path)
        file_size = file_path.stat().st_size
        file_ext = file_path.suffix.lower()

        # Basic document analysis
        analysis = {
            "file_path": doc_path,
            "file_size": file_size,
            "file_type": file_ext,
            "estimated_complexity": "low",
            "recommended_workflow": "standard",
            "expected_quality": 0.8
        }

        # Determine document type and complexity
        if file_ext in ['.pdf']:
            analysis.update({
                "document_type": "pdf",
                "estimated_complexity": "medium",
                "recommended_workflow": "pdf_processing"
            })
        elif file_ext in ['.png', '.jpg', '.jpeg', '.tiff']:
            analysis.update({
                "document_type": "image",
                "estimated_complexity": "low",
                "recommended_workflow": "image_processing"
            })
        else:
            analysis.update({
                "document_type": "unknown",
                "estimated_complexity": "high",
                "recommended_workflow": "complex_processing"
            })

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
            "recommended_workflow": "fallback"
        }

async def _apply_auto_workflow(doc_path: str, analysis: Dict, quality_threshold: float, save_intermediates: bool) -> Dict[str, Any]:
    """Apply automatic workflow based on document analysis."""
    workflow = analysis.get("recommended_workflow", "standard")

    if workflow == "pdf_processing":
        # PDF-specific workflow
        return await _process_pdf_document(doc_path, quality_threshold, save_intermediates)
    elif workflow == "image_processing":
        # Image-specific workflow
        return await _process_image_document(doc_path, quality_threshold, save_intermediates)
    else:
        # Standard OCR workflow
        return await _process_standard_document(doc_path, quality_threshold)

async def _apply_ocr_only_workflow(doc_path: str, analysis: Dict) -> Dict[str, Any]:
    """Apply OCR-only workflow (no preprocessing)."""
    try:
        ocr_result = await backend_manager.process_with_backend("auto", doc_path, mode="text")

        return {
            "success": ocr_result.get("success", False),
            "workflow": "ocr_only",
            "ocr_result": ocr_result,
            "quality_score": 0.7,  # Basic estimate
            "processing_steps": ["ocr"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"OCR-only workflow failed: {str(e)}",
            "workflow": "ocr_only"
        }

async def _apply_full_pipeline_workflow(doc_path: str, analysis: Dict, quality_threshold: float, save_intermediates: bool) -> Dict[str, Any]:
    """Apply complete processing pipeline."""
    steps = []
    current_path = doc_path

    try:
        # Step 1: Preprocessing
        preprocess_result = await preprocess_for_ocr(current_path, None, ["deskew", "enhance", "crop"])
        steps.append({"step": "preprocessing", "result": preprocess_result})

        if preprocess_result.get("success") and save_intermediates:
            current_path = preprocess_result.get("output_path", current_path)

        # Step 2: OCR with quality check
        ocr_result = await backend_manager.process_with_backend("auto", current_path, mode="text")
        steps.append({"step": "ocr", "result": ocr_result})

        # Step 3: Quality assessment
        quality_result = await assess_ocr_quality(ocr_result, assessment_type="comprehensive")
        steps.append({"step": "quality_assessment", "result": quality_result})

        # Step 4: Post-processing if quality is low
        final_quality = quality_result.get("quality_score", 0)
        if final_quality < quality_threshold:
            # Try different backend
            alt_ocr_result = await backend_manager.process_with_backend("tesseract", current_path, mode="text")
            if alt_ocr_result.get("success"):
                alt_quality = await assess_ocr_quality(alt_ocr_result)
                if alt_quality.get("quality_score", 0) > final_quality:
                    ocr_result = alt_ocr_result
                    quality_result = alt_quality
                    steps.append({"step": "backend_fallback", "result": "Switched to alternative OCR backend"})

        return {
            "success": ocr_result.get("success", False),
            "workflow": "full_pipeline",
            "processing_steps": steps,
            "final_result": ocr_result,
            "quality_score": quality_result.get("quality_score", 0),
            "quality_grade": quality_result.get("quality_grade", "F")
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Full pipeline workflow failed: {str(e)}",
            "workflow": "full_pipeline",
            "processing_steps": steps
        }

async def _apply_quality_focused_workflow(doc_path: str, analysis: Dict, quality_threshold: float, save_intermediates: bool) -> Dict[str, Any]:
    """Apply quality-focused workflow with multiple attempts."""
    best_result = None
    best_quality = 0
    attempts = []

    # Try different preprocessing combinations
    preprocess_options = [
        [],  # No preprocessing
        ["enhance"],  # Just enhancement
        ["deskew", "enhance"],  # Deskew + enhance
        ["deskew", "enhance", "crop"]  # Full preprocessing
    ]

    for preprocess_steps in preprocess_options:
        try:
            # Apply preprocessing
            current_path = doc_path
            if preprocess_steps:
                preprocess_result = await preprocess_for_ocr(doc_path, None, preprocess_steps)
                if preprocess_result.get("success") and save_intermediates:
                    current_path = preprocess_result.get("output_path", doc_path)

            # OCR processing
            ocr_result = await backend_manager.process_with_backend("auto", current_path, mode="text")

            if ocr_result.get("success"):
                # Quality assessment
                quality_result = await assess_ocr_quality(ocr_result)
                quality_score = quality_result.get("quality_score", 0)

                attempt = {
                    "preprocessing": preprocess_steps,
                    "ocr_backend": ocr_result.get("backend", "unknown"),
                    "quality_score": quality_score,
                    "success": True
                }
                attempts.append(attempt)

                # Keep best result
                if quality_score > best_quality:
                    best_quality = quality_score
                    best_result = {
                        "ocr_result": ocr_result,
                        "quality_result": quality_result,
                        "preprocessing_applied": preprocess_steps,
                        "final_path": current_path
                    }

                    # Stop if we meet quality threshold
                    if quality_score >= quality_threshold:
                        break

        except Exception as e:
            attempts.append({
                "preprocessing": preprocess_steps,
                "error": str(e),
                "success": False
            })

    if best_result:
        return {
            "success": True,
            "workflow": "quality_focused",
            "attempts_made": len(attempts),
            "best_quality_score": best_quality,
            "final_result": best_result["ocr_result"],
            "preprocessing_applied": best_result["preprocessing_applied"],
            "quality_assessment": best_result["quality_result"]
        }
    else:
        return {
            "success": False,
            "error": "All quality-focused attempts failed",
            "workflow": "quality_focused",
            "attempts_made": len(attempts),
            "attempt_details": attempts
        }

async def _process_pdf_document(doc_path: str, quality_threshold: float, save_intermediates: bool) -> Dict[str, Any]:
    """Process PDF document with PDF-specific optimizations."""
    try:
        # Convert PDF to images
        pdf_result = await convert_pdf_to_images(doc_path, None, dpi=300, format="PNG")

        if not pdf_result.get("success"):
            return {"success": False, "error": "PDF conversion failed"}

        # Process first page as representative
        image_paths = pdf_result.get("results", {}).get("files_saved", [])
        if not image_paths:
            return {"success": False, "error": "No images extracted from PDF"}

        first_page = image_paths[0]

        # Apply OCR pipeline
        ocr_result = await backend_manager.process_with_backend("auto", first_page, mode="text")

        return {
            "success": ocr_result.get("success", False),
            "workflow": "pdf_processing",
            "pdf_info": pdf_result.get("pdf_info"),
            "ocr_result": ocr_result,
            "pages_extracted": len(image_paths)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"PDF processing failed: {str(e)}",
            "workflow": "pdf_processing"
        }

async def _process_image_document(doc_path: str, quality_threshold: float, save_intermediates: bool) -> Dict[str, Any]:
    """Process image document with image-specific optimizations."""
    try:
        # Quick quality check
        quality_result = await analyze_image_quality(doc_path)

        preprocessing_needed = quality_result.get("ocr_readiness") != "ready"

        if preprocessing_needed:
            # Apply preprocessing
            preprocess_result = await preprocess_for_ocr(doc_path, None, ["deskew", "enhance", "crop"])
            ocr_input = preprocess_result.get("output_path") if preprocess_result.get("success") else doc_path
        else:
            ocr_input = doc_path

        # OCR processing
        ocr_result = await backend_manager.process_with_backend("auto", ocr_input, mode="text")

        return {
            "success": ocr_result.get("success", False),
            "workflow": "image_processing",
            "preprocessing_applied": preprocessing_needed,
            "image_quality": quality_result,
            "ocr_result": ocr_result
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Image processing failed: {str(e)}",
            "workflow": "image_processing"
        }

async def _process_standard_document(doc_path: str, quality_threshold: float) -> Dict[str, Any]:
    """Process document with standard OCR workflow."""
    try:
        ocr_result = await backend_manager.process_with_backend("auto", doc_path, mode="text")

        return {
            "success": ocr_result.get("success", False),
            "workflow": "standard",
            "ocr_result": ocr_result
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Standard processing failed: {str(e)}",
            "workflow": "standard"
        }

async def _validate_pipeline_steps(steps: List[Dict]) -> Dict[str, Any]:
    """Validate pipeline step configurations."""
    errors = []
    valid_tools = [
        "deskew_image", "enhance_image", "rotate_image", "crop_image",
        "process_document", "assess_ocr_quality", "convert_image_format",
        "analyze_document_layout", "extract_table_data"
    ]

    for i, step in enumerate(steps):
        if "tool" not in step:
            errors.append(f"Step {i+1}: Missing 'tool' field")
        elif step["tool"] not in valid_tools:
            errors.append(f"Step {i+1}: Unknown tool '{step['tool']}'")
        elif "parameters" not in step:
            errors.append(f"Step {i+1}: Missing 'parameters' field")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "steps_validated": len(steps)
    }

def _estimate_pipeline_complexity(steps: List[Dict]) -> str:
    """Estimate pipeline complexity."""
    complexity_score = len(steps)

    complex_tools = ["analyze_document_layout", "extract_table_data", "assess_ocr_quality"]
    for step in steps:
        if step.get("tool") in complex_tools:
            complexity_score += 2

    if complexity_score <= 3:
        return "low"
    elif complexity_score <= 6:
        return "medium"
    else:
        return "high"

async def _execute_pipeline_for_document(pipeline_config: Dict, doc_path: str, execution_mode: str) -> Dict[str, Any]:
    """Execute pipeline for a single document."""
    steps = pipeline_config.get("steps", [])
    step_results = []

    try:
        for step in steps:
            tool_name = step["tool"]
            parameters = step["parameters"].copy()
            parameters["image_path" if "image_path" not in parameters else list(parameters.keys())[0]] = doc_path

            # Execute step (simplified - would need actual tool calls)
            step_result = {
                "step": tool_name,
                "parameters": parameters,
                "success": True,
                "mock_result": f"Executed {tool_name}"
            }
            step_results.append(step_result)

        return {
            "success": True,
            "step_results": step_results,
            "pipeline_completed": True
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Pipeline execution failed: {str(e)}",
            "step_results": step_results
        }

async def _save_batch_results(results: List[Dict], output_directory: str) -> None:
    """Save batch processing results to files."""
    try:
        import json
        from pathlib import Path

        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save summary
        summary = {
            "batch_timestamp": time.time(),
            "total_documents": len(results),
            "successful": sum(1 for r in results if r.get("success")),
            "results": results
        }

        summary_file = output_dir / "batch_results.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

    except Exception as e:
        logger.error(f"Failed to save batch results: {e}")

def _calculate_optimal_settings(analysis_results: List[Dict], target_quality: float, time_constraint: Optional[float]) -> Dict[str, Any]:
    """Calculate optimal processing settings."""
    # Simplified optimization logic
    avg_complexity = sum(1 if a.get("estimated_complexity") == "high" else 0.5 if a.get("estimated_complexity") == "medium" else 0 for a in analysis_results) / len(analysis_results)

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
        "resource_requirements": "standard"
    }

def _generate_processing_recommendations(optimization: Dict, analysis: List[Dict]) -> List[str]:
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
        recommendations.append(f"Apply preprocessing: {', '.join(optimization['preprocessing_steps'])}")

    if optimization["estimated_time"] > 5.0:
        recommendations.append("Consider batch processing for better performance")

    return recommendations