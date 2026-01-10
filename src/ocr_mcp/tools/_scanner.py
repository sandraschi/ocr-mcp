"""
Scanner Operations Tools for OCR-MCP Server - PORTMANTEAU DESIGN

Consolidates all scanner hardware control operations into a single tool.
"""

import logging
from typing import Dict, Any, Optional


from ..core.error_handler import ErrorHandler, create_success_response

logger = logging.getLogger(__name__)


async def handle_scanner_op(
    operation: str,
    device_id: Optional[str] = None,
    scan_source: str = "flatbed",
    resolution: int = 300,
    color_mode: str = "Color",
    paper_size: str = "A4",
    output_prefix: str = "scan_",
    backend_manager: Any = None,
    config: Any = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    PORTMANTEAU TOOL: Scanner Hardware Operations

    Consolidates all scanner discovery, configuration, and control operations into a single tool.

    OPERATIONS:
    - "list_scanners": Discover and enumerate available scanners
    - "scanner_properties": Get detailed scanner capabilities and settings
    - "configure_scan": Set scan parameters (DPI, color mode, paper size)
    - "scan_document": Perform single document scan
    - "scan_batch": Batch scan multiple documents with ADF support
    - "preview_scan": Low-resolution preview scan for positioning

    Args:
        operation: The specific operation to perform
        device_id: Scanner device ID
        scan_source: Source for scanning ("flatbed" or "adf")
        resolution: DPI (resolution)
        color_mode: Color mode
        paper_size: Paper size
        output_prefix: Prefix for output files
        backend_manager: BackendManager instance
        config: OCRConfig instance
        **kwargs: Additional parameters (save_path, save_directory, brightness, contrast, count, etc.)

    Returns:
        Operation-specific results
    """
    # Map parameters if necessary
    dpi = resolution
    save_path = kwargs.get("save_path")
    save_directory = kwargs.get("save_directory")
    brightness = kwargs.get("brightness", 0)
    contrast = kwargs.get("contrast", 0)
    use_adf = kwargs.get("use_adf", False) or (scan_source == "adf")
    duplex = kwargs.get("duplex", False)
    count = kwargs.get("count", 1)

    try:
        logger.info(f"Scanner operation: {operation}")

        # Validate operation parameter
        valid_operations = [
            "list_scanners",
            "scanner_properties",
            "configure_scan",
            "scan_document",
            "scan_batch",
            "preview_scan",
        ]

        if operation not in valid_operations:
            return ErrorHandler.create_error(
                "PARAMETERS_INVALID",
                message_override=f"Invalid operation: {operation}",
                details={"valid_operations": valid_operations},
            ).to_dict()

        # Check if scanner backend is available
        if (
            not backend_manager.scanner_manager
            or not backend_manager.scanner_manager.is_available()
        ):
            return ErrorHandler.create_error(
                "SCANNER_NOT_FOUND",
                message_override="Scanner backend not available. Ensure scanner hardware is connected and WIA is enabled.",
                details={"backend_status": "unavailable"},
            ).to_dict()

        # Route to appropriate handler based on operation
        if operation == "list_scanners":
            return await _handle_list_scanners(backend_manager)

        elif operation == "scanner_properties":
            if not device_id:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override="device_id required for scanner_properties operation",
                ).to_dict()
            return await _handle_scanner_properties(device_id, backend_manager)

        elif operation == "configure_scan":
            if not device_id:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override="device_id required for configure_scan operation",
                ).to_dict()
            return await _handle_configure_scan(
                device_id,
                dpi,
                color_mode,
                paper_size,
                brightness,
                contrast,
                use_adf,
                duplex,
                backend_manager,
            )

        elif operation == "scan_document":
            if not device_id:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override="device_id required for scan_document operation",
                ).to_dict()
            return await _handle_scan_document(
                device_id,
                dpi,
                color_mode,
                paper_size,
                brightness,
                contrast,
                use_adf,
                duplex,
                save_path,
                backend_manager,
            )

        elif operation == "scan_batch":
            if not device_id:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override="device_id required for scan_batch operation",
                ).to_dict()
            return await _handle_scan_batch(
                device_id,
                count,
                dpi,
                color_mode,
                paper_size,
                brightness,
                contrast,
                use_adf,
                duplex,
                save_directory,
                backend_manager,
            )

        elif operation == "preview_scan":
            if not device_id:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override="device_id required for preview_scan operation",
                ).to_dict()
            return await _handle_preview_scan(device_id, save_path, backend_manager)

    except Exception as e:
        logger.error(f"Scanner operation failed: {operation}, error: {e}")
        return ErrorHandler.handle_exception(
            e, context=f"scanner_operations_{operation}"
        )


# Operation handler functions
async def _handle_list_scanners(backend_manager):
    """Handle scanner discovery."""
    try:
        # Discover scanners
        scanners = backend_manager.scanner_manager.discover_scanners(force_refresh=True)

        # Get backend status
        backend_status = backend_manager.scanner_manager.get_backend_status()

        # Format scanner information
        scanner_list = []
        for scanner in scanners:
            scanner_list.append(
                {
                    "id": getattr(scanner, "device_id", "unknown"),
                    "name": getattr(scanner, "name", "Unknown Scanner"),
                    "manufacturer": getattr(scanner, "manufacturer", "Unknown"),
                    "type": getattr(scanner, "device_type", "Unknown"),
                    "supports_adf": getattr(scanner, "supports_adf", False),
                    "supports_duplex": getattr(scanner, "supports_duplex", False),
                }
            )

        return create_success_response(
            {
                "scanners": scanner_list,
                "backend_status": backend_status,
                "count": len(scanner_list),
            }
        )

    except Exception as e:
        logger.error(f"Failed to list scanners: {e}")
        return ErrorHandler.handle_exception(e, context="list_scanners")


async def _handle_scanner_properties(device_id, backend_manager):
    """Handle scanner properties query."""
    try:
        properties = backend_manager.scanner_manager.get_scanner_properties(device_id)
        if properties is None:
            return ErrorHandler.create_error(
                "SCANNER_NOT_FOUND",
                message_override=f"Scanner {device_id} not found or not accessible",
            ).to_dict()

        return create_success_response(
            {
                "device_id": device_id,
                "properties": properties.__dict__
                if hasattr(properties, "__dict__")
                else properties,
            }
        )

    except Exception as e:
        logger.error(f"Failed to get scanner properties for {device_id}: {e}")
        return ErrorHandler.handle_exception(e, context="scanner_properties")


async def _handle_configure_scan(
    device_id,
    dpi,
    color_mode,
    paper_size,
    brightness,
    contrast,
    use_adf,
    duplex,
    backend_manager,
):
    """Handle scan configuration."""
    try:
        settings = {
            "dpi": dpi,
            "color_mode": color_mode,
            "paper_size": paper_size,
            "brightness": brightness,
            "contrast": contrast,
            "use_adf": use_adf,
            "duplex": duplex,
        }

        success = backend_manager.scanner_manager.configure_scan(device_id, settings)

        return create_success_response(
            {"device_id": device_id, "configured": success, "settings": settings}
        )

    except Exception as e:
        logger.error(f"Failed to configure scan for {device_id}: {e}")
        return ErrorHandler.handle_exception(e, context="configure_scan")


async def _handle_scan_document(
    device_id,
    dpi,
    color_mode,
    paper_size,
    brightness,
    contrast,
    use_adf,
    duplex,
    save_path,
    backend_manager,
):
    """Handle single document scanning."""
    try:
        # Configure scan first
        settings = {
            "dpi": dpi,
            "color_mode": color_mode,
            "paper_size": paper_size,
            "brightness": brightness,
            "contrast": contrast,
            "use_adf": use_adf,
            "duplex": duplex,
        }

        # Perform scan
        result = backend_manager.scanner_manager.scan_document(
            device_id, settings, save_path
        )

        if result is None:
            return ErrorHandler.create_error(
                "SCAN_FAILED", message_override=f"Scan failed for device {device_id}"
            ).to_dict()

        return create_success_response(
            {"device_id": device_id, "scan_result": str(result), "settings": settings}
        )

    except Exception as e:
        logger.error(f"Failed to scan document with {device_id}: {e}")
        return ErrorHandler.handle_exception(e, context="scan_document")


async def _handle_scan_batch(
    device_id,
    count,
    dpi,
    color_mode,
    paper_size,
    brightness,
    contrast,
    use_adf,
    duplex,
    save_directory,
    backend_manager,
):
    """Handle batch document scanning."""
    try:
        settings = {
            "dpi": dpi,
            "color_mode": color_mode,
            "paper_size": paper_size,
            "brightness": brightness,
            "contrast": contrast,
            "use_adf": use_adf,
            "duplex": duplex,
        }

        results = backend_manager.scanner_manager.scan_batch(
            device_id, count, settings, save_directory
        )

        return create_success_response(
            {
                "device_id": device_id,
                "batch_results": [str(r) for r in results] if results else [],
                "count_requested": count,
                "count_completed": len(results) if results else 0,
                "settings": settings,
            }
        )

    except Exception as e:
        logger.error(f"Failed to scan batch with {device_id}: {e}")
        return ErrorHandler.handle_exception(e, context="scan_batch")


async def _handle_preview_scan(device_id, save_path, backend_manager):
    """Handle preview scanning."""
    try:
        result = backend_manager.scanner_manager.preview_scan(device_id, save_path)

        if result is None:
            return ErrorHandler.create_error(
                "PREVIEW_SCAN_FAILED",
                message_override=f"Preview scan failed for device {device_id}",
            ).to_dict()

        return create_success_response(
            {"device_id": device_id, "preview_result": str(result)}
        )

    except Exception as e:
        logger.error(f"Failed to preview scan with {device_id}: {e}")
        return ErrorHandler.handle_exception(e, context="preview_scan")
