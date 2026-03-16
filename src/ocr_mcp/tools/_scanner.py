"""
Scanner Operations Tools for OCR-MCP Server - PORTMANTEAU DESIGN

Consolidates all scanner hardware control operations into a single tool.
"""

import logging
from typing import Any

from ..core.error_handler import ErrorHandler, create_success_response

logger = logging.getLogger(__name__)


async def handle_scanner_op(
    operation: str,
    device_id: str | None = None,
    scan_source: str = "flatbed",
    resolution: int = 300,
    color_mode: str = "Color",
    paper_size: str = "A4",
    output_prefix: str = "scan_",
    backend_manager: Any = None,
    config: Any = None,
    **kwargs,
) -> dict[str, Any]:
    """
    Backend handler for scanner operations. See ocr_tools.scanner_operations for MCP tool docstring.

    OPERATIONS:
    - list_scanners: Discover and enumerate available scanners. No device_id.
    - scanner_properties: Get capabilities and settings. Requires: device_id.
    - configure_scan: Set scan parameters. Requires: device_id.
    - scan_document: Perform single document scan. Requires: device_id.
    - scan_batch: Batch scan with ADF. Requires: device_id.
    - preview_scan: Low-resolution preview. Requires: device_id.
    - diagnostics: Troubleshooting. Optional: device_id.

    Args:
    - operation (str, required): Operation to perform. Must be one of OPERATIONS above.
    - device_id (str | None): WIA device ID. Required for most operations.
    - scan_source (str): flatbed or adf. Default: flatbed.
    - resolution (int): DPI. Default: 300.
    - color_mode (str): Color mode. Default: Color.
    - paper_size (str): Paper size. Default: A4.
    - output_prefix (str): Prefix for output files. Default: scan_.
    - backend_manager: Injected BackendManager.
    - config: Injected OCRConfig.
    - **kwargs: save_path, save_directory, brightness, contrast, count, use_adf, duplex.

    Returns:
    FastMCP 3.1 dialogic response: success, operation, result or error,
    recommendations, next_steps, recovery_options (on error), related_operations.
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
            "diagnostics",
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

        # Resolve device_id when missing: use first flatbed scanner
        resolved_device_id = device_id
        if not resolved_device_id:
            resolved_device_id = await _resolve_default_device_id(backend_manager, scan_source)

        # Route to appropriate handler based on operation
        if operation == "list_scanners":
            return await _handle_list_scanners(backend_manager)

        elif operation == "scanner_properties":
            if not resolved_device_id:
                return ErrorHandler.create_error(
                    "SCANNER_NOT_FOUND",
                    message_override="No scanner found. Specify device_id or ensure a flatbed scanner is connected.",
                ).to_dict()
            return await _handle_scanner_properties(resolved_device_id, backend_manager)

        elif operation == "configure_scan":
            if not resolved_device_id:
                return ErrorHandler.create_error(
                    "SCANNER_NOT_FOUND",
                    message_override="No scanner found. Specify device_id or ensure a flatbed scanner is connected.",
                ).to_dict()
            return await _handle_configure_scan(
                resolved_device_id,
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
            if not resolved_device_id:
                return ErrorHandler.create_error(
                    "SCANNER_NOT_FOUND",
                    message_override="No scanner found. Specify device_id or ensure a flatbed scanner is connected.",
                ).to_dict()
            return await _handle_scan_document(
                resolved_device_id,
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
            if not resolved_device_id:
                return ErrorHandler.create_error(
                    "SCANNER_NOT_FOUND",
                    message_override="No scanner found. Specify device_id or ensure a flatbed scanner is connected.",
                ).to_dict()
            return await _handle_scan_batch(
                resolved_device_id,
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
            if not resolved_device_id:
                return ErrorHandler.create_error(
                    "SCANNER_NOT_FOUND",
                    message_override="No scanner found. Specify device_id or ensure a flatbed scanner is connected.",
                ).to_dict()
            return await _handle_preview_scan(resolved_device_id, save_path, backend_manager)

        elif operation == "diagnostics":
            return await _handle_diagnostics(resolved_device_id, backend_manager)

    except Exception as e:
        logger.error(f"Scanner operation failed: {operation}, error: {e}")
        return ErrorHandler.handle_exception(e, context=f"scanner_operations_{operation}")


async def _resolve_default_device_id(backend_manager, scan_source: str = "flatbed") -> str | None:
    """
    Resolve device_id when not provided: use first flatbed if scan_source is flatbed,
    otherwise first available scanner.
    """
    try:
        scanners = backend_manager.scanner_manager.discover_scanners(force_refresh=True)
        if not scanners:
            return None

        if scan_source.lower() == "flatbed":
            for scanner in scanners:
                dev_type = str(getattr(scanner, "device_type", "")).lower()
                if "flatbed" in dev_type:
                    return getattr(scanner, "device_id", None) or str(scanner)

        return getattr(scanners[0], "device_id", None) or str(scanners[0])
    except Exception as e:
        logger.warning(f"Could not resolve default device_id: {e}")
        return None


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

        # Perform scan (ScannerManager.scan_document takes device_id, settings only)
        result = backend_manager.scanner_manager.scan_document(device_id, settings)

        if result is None:
            return ErrorHandler.create_error(
                "SCAN_FAILED", message_override=f"Scan failed for device {device_id}"
            ).to_dict()

        saved_path = None
        if save_path and hasattr(result, "save"):
            from pathlib import Path

            path = Path(save_path)
            if not path.suffix:
                path = path.with_suffix(".png")
            result.save(str(path))
            saved_path = str(path)

        return create_success_response(
            {
                "device_id": device_id,
                "scan_result": str(result),
                "saved_path": saved_path,
                "settings": settings,
            }
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

        return create_success_response({"device_id": device_id, "preview_result": str(result)})

    except Exception as e:
        logger.error(f"Failed to preview scan with {device_id}: {e}")
        return ErrorHandler.handle_exception(e, context="preview_scan")


async def _handle_diagnostics(device_id, backend_manager):
    """Handle scanner diagnostics."""
    try:
        diagnostics = {}

        # Get backend status
        if hasattr(backend_manager.scanner_manager, "get_backend_status"):
            diagnostics["backend_status"] = backend_manager.scanner_manager.get_backend_status()
        else:
            diagnostics["backend_status"] = "Backend status not available"

        # Get device-specific diagnostics if device_id provided
        if device_id:
            if hasattr(backend_manager.scanner_manager, "get_scanner_diagnostics"):
                device_diagnostics = backend_manager.scanner_manager.get_scanner_diagnostics(
                    device_id
                )
                if device_diagnostics:
                    diagnostics["device_diagnostics"] = device_diagnostics
                else:
                    diagnostics["device_diagnostics"] = f"No diagnostics available for {device_id}"
            else:
                diagnostics["device_diagnostics"] = "Device diagnostics not supported"
        else:
            diagnostics["device_diagnostics"] = (
                "No device_id specified - run diagnostics on specific scanner for detailed info"
            )

        # Add general system information
        import platform

        diagnostics["system_info"] = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "architecture": platform.architecture(),
        }

        # Add troubleshooting hints
        diagnostics["troubleshooting"] = {
            "common_issues": [
                "Scanner not powered on or connected",
                "WIA service not running (Windows)",
                "COM initialization issues",
                "Device busy - wait and retry",
                "Driver conflicts or outdated drivers",
                "USB power management issues",
                "Antivirus blocking scanner access",
            ],
            "canon_lide_specific": [
                "Power cycle the scanner",
                "Check USB cable connection",
                "Update Canon drivers from official website",
                "Disable USB selective suspend in Power Options",
                "Try different USB port",
                "Close other scanning applications",
            ],
        }

        return create_success_response(diagnostics)

    except Exception as e:
        logger.error(f"Failed to get diagnostics: {e}")
        return ErrorHandler.handle_exception(e, context="diagnostics")
