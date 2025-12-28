"""
Scanner Operations Tools for OCR-MCP Server - PORTMANTEAU DESIGN

Consolidates all scanner hardware control operations into a single tool.
"""

import logging
from typing import Dict, Any, Optional

from ..core.backend_manager import BackendManager
from ..core.config import OCRConfig
from ..core.error_handler import ErrorHandler, create_success_response

logger = logging.getLogger(__name__)


def register_scanner_operations_tools(app, backend_manager: BackendManager, config: OCRConfig):
    """Register scanner operations portmanteau tool with the FastMCP app."""

    @app.tool()
    async def scanner_operations(
        operation: str,
        device_id: Optional[str] = None,
        # Scan configuration parameters
        dpi: int = 300,
        color_mode: str = "Color",
        paper_size: str = "A4",
        brightness: int = 0,
        contrast: int = 0,
        use_adf: bool = False,
        duplex: bool = False,
        # Batch scanning parameters
        count: int = 1,
        save_path: Optional[str] = None,
        save_directory: Optional[str] = None
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
            operation: The specific operation to perform (see list above)
            device_id: Scanner device ID (required for most operations except "list_scanners")
            dpi: Resolution in dots per inch (75, 150, 200, 300, 600, etc.)
            color_mode: Color mode ("Color", "Grayscale", "BlackWhite")
            paper_size: Paper size ("A4", "Letter", "Legal", "Custom")
            brightness: Brightness adjustment (-1000 to 1000)
            contrast: Contrast adjustment (-1000 to 1000)
            use_adf: Use Automatic Document Feeder if available
            duplex: Enable duplex scanning if supported
            count: Number of documents to scan in batch operations
            save_path: Path to save single scan result
            save_directory: Directory to save batch scan results

        Returns:
            Operation-specific results with scanner information, scan data, or status
        """
        try:
            logger.info(f"Scanner operation: {operation}")

            # Validate operation parameter
            valid_operations = [
                "list_scanners", "scanner_properties", "configure_scan",
                "scan_document", "scan_batch", "preview_scan"
            ]

            if operation not in valid_operations:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override=f"Invalid operation: {operation}",
                    details={"valid_operations": valid_operations}
                ).to_dict()

            # Check if scanner backend is available
            if not backend_manager.scanner_manager or not backend_manager.scanner_manager.is_available():
                return ErrorHandler.create_error(
                    "SCANNER_NOT_FOUND",
                    message_override="Scanner backend not available. Ensure scanner hardware is connected and WIA is enabled.",
                    details={"backend_status": "unavailable"}
                ).to_dict()

            # Route to appropriate handler based on operation
            if operation == "list_scanners":
                return await _handle_list_scanners(backend_manager)

            elif operation == "scanner_properties":
                if not device_id:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="device_id required for scanner_properties operation"
                    ).to_dict()
                return await _handle_scanner_properties(device_id, backend_manager)

            elif operation == "configure_scan":
                if not device_id:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="device_id required for configure_scan operation"
                    ).to_dict()
                return await _handle_configure_scan(
                    device_id, dpi, color_mode, paper_size, brightness, contrast, use_adf, duplex, backend_manager
                )

            elif operation == "scan_document":
                if not device_id:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="device_id required for scan_document operation"
                    ).to_dict()
                return await _handle_scan_document(
                    device_id, dpi, color_mode, paper_size, brightness, contrast, use_adf, duplex, save_path, backend_manager
                )

            elif operation == "scan_batch":
                if not device_id:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="device_id required for scan_batch operation"
                    ).to_dict()
                return await _handle_scan_batch(
                    device_id, count, dpi, color_mode, paper_size, brightness, contrast, use_adf, duplex, save_directory, backend_manager
                )

            elif operation == "preview_scan":
                if not device_id:
                    return ErrorHandler.create_error(
                        "PARAMETERS_INVALID",
                        message_override="device_id required for preview_scan operation"
                    ).to_dict()
                return await _handle_preview_scan(device_id, save_path, backend_manager)

        except Exception as e:
            logger.error(f"Scanner operation failed: {operation}, error: {e}")
            return ErrorHandler.handle_exception(e, context=f"scanner_operations_{operation}")


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
            scanner_list.append({
                "id": scanner.get("id", "unknown"),
                "name": scanner.get("name", "Unknown Scanner"),
                "manufacturer": scanner.get("manufacturer", "Unknown"),
                "type": scanner.get("type", "Unknown"),
                "status": scanner.get("status", "unknown"),
                "capabilities": scanner.get("capabilities", {})
            })

        return create_success_response({
            "scanners": scanner_list,
            "backend_status": backend_status,
            "count": len(scanner_list)
        })

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
                message_override=f"Scanner {device_id} not found or not accessible"
            ).to_dict()

        return create_success_response({
            "device_id": device_id,
            "properties": properties
        })

    except Exception as e:
        logger.error(f"Failed to get scanner properties for {device_id}: {e}")
        return ErrorHandler.handle_exception(e, context="scanner_properties")


async def _handle_configure_scan(device_id, dpi, color_mode, paper_size, brightness, contrast, use_adf, duplex, backend_manager):
    """Handle scan configuration."""
    try:
        settings = {
            "dpi": dpi,
            "color_mode": color_mode,
            "paper_size": paper_size,
            "brightness": brightness,
            "contrast": contrast,
            "use_adf": use_adf,
            "duplex": duplex
        }

        success = backend_manager.scanner_manager.configure_scan(device_id, settings)

        return create_success_response({
            "device_id": device_id,
            "configured": success,
            "settings": settings
        })

    except Exception as e:
        logger.error(f"Failed to configure scan for {device_id}: {e}")
        return ErrorHandler.handle_exception(e, context="configure_scan")


async def _handle_scan_document(device_id, dpi, color_mode, paper_size, brightness, contrast, use_adf, duplex, save_path, backend_manager):
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
            "duplex": duplex
        }

        # Perform scan
        result = backend_manager.scanner_manager.scan_document(device_id, settings, save_path)

        if result is None:
            return ErrorHandler.create_error(
                "SCAN_FAILED",
                message_override=f"Scan failed for device {device_id}"
            ).to_dict()

        return create_success_response({
            "device_id": device_id,
            "scan_result": result,
            "settings": settings
        })

    except Exception as e:
        logger.error(f"Failed to scan document with {device_id}: {e}")
        return ErrorHandler.handle_exception(e, context="scan_document")


async def _handle_scan_batch(device_id, count, dpi, color_mode, paper_size, brightness, contrast, use_adf, duplex, save_directory, backend_manager):
    """Handle batch document scanning."""
    try:
        settings = {
            "dpi": dpi,
            "color_mode": color_mode,
            "paper_size": paper_size,
            "brightness": brightness,
            "contrast": contrast,
            "use_adf": use_adf,
            "duplex": duplex
        }

        results = backend_manager.scanner_manager.scan_batch(device_id, count, settings, save_directory)

        return create_success_response({
            "device_id": device_id,
            "batch_results": results,
            "count_requested": count,
            "count_completed": len(results) if results else 0,
            "settings": settings
        })

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
                message_override=f"Preview scan failed for device {device_id}"
            ).to_dict()

        return create_success_response({
            "device_id": device_id,
            "preview_result": result
        })

    except Exception as e:
        logger.error(f"Failed to preview scan with {device_id}: {e}")
        return ErrorHandler.handle_exception(e, context="preview_scan")


def register_scanner_tools(app, backend_manager: BackendManager, config: OCRConfig):
    """Legacy function - now delegates to portmanteau tool."""
    register_scanner_operations_tools(app, backend_manager, config)


# Original individual tool functions removed - now handled by portmanteau tool
    """Register all scanner tools with the FastMCP app."""

    @app.tool()
    async def list_scanners() -> Dict[str, Any]:
        """
        Discover and list all available scanners.

        Returns detailed information about connected scanners including
        their capabilities, supported resolutions, and connection status.

        Returns:
            Dictionary containing scanner information and backend status
        """
        logger.info("Discovering available scanners")

        # Check if scanner backend is available
        if not backend_manager.scanner_manager or not backend_manager.scanner_manager.is_available():
            return ErrorHandler.create_error(
                "SCANNER_NOT_FOUND",
                message_override="Scanner backend not available. Ensure scanner hardware is connected and WIA is enabled.",
                details={"backend_status": "unavailable"}
            ).to_dict()

        try:
            # Discover scanners
            scanners = backend_manager.scanner_manager.discover_scanners(force_refresh=True)

            # Get backend status
            backend_status = backend_manager.scanner_manager.get_backend_status()

            # Format scanner information
            scanner_list = []
            for scanner in scanners:
                scanner_info = {
                    "device_id": scanner.device_id,
                    "name": scanner.name,
                    "manufacturer": scanner.manufacturer,
                    "description": scanner.description,
                    "device_type": scanner.device_type,
                    "supports_adf": scanner.supports_adf,
                    "supports_duplex": scanner.supports_duplex,
                    "max_dpi": scanner.max_dpi
                }
                scanner_list.append(scanner_info)

            return {
                "success": True,
                "scanners": scanner_list,
                "total_scanners": len(scanners),
                "backend_status": backend_status,
                "available_backends": list(backend_status.keys())
            }

        except Exception as e:
            logger.error(f"Scanner discovery failed: {e}")
            return {
                "success": False,
                "error": f"Scanner discovery failed: {str(e)}",
                "scanners": [],
                "total_scanners": 0
            }

    @app.tool()
    async def scanner_properties(device_id: str) -> Dict[str, Any]:
        """
        Get detailed properties and capabilities of a specific scanner.

        Args:
            device_id: Scanner device ID (e.g., "wia:Epson Perfection V39")

        Returns:
            Comprehensive scanner properties including supported resolutions,
            color modes, paper sizes, and hardware capabilities
        """
        logger.info(f"Getting properties for scanner: {device_id}")

        try:
            properties = backend_manager.scanner_manager.get_scanner_properties(device_id)

            if not properties:
                return {
                    "success": False,
                    "error": f"Scanner not found or properties unavailable: {device_id}",
                    "device_id": device_id
                }

            return {
                "success": True,
                "device_id": device_id,
                "properties": {
                    "supported_resolutions": properties.supported_resolutions,
                    "supported_color_modes": properties.supported_color_modes,
                    "supported_paper_sizes": properties.supported_paper_sizes,
                    "max_paper_width": properties.max_paper_width,
                    "max_paper_height": properties.max_paper_height,
                    "supports_adf": properties.supports_adf,
                    "supports_duplex": properties.supports_duplex,
                    "supports_preview": properties.supports_preview,
                    "manufacturer": properties.manufacturer,
                    "model": properties.model,
                    "firmware_version": properties.firmware_version
                }
            }

        except Exception as e:
            logger.error(f"Failed to get scanner properties for {device_id}: {e}")
            return {
                "success": False,
                "error": f"Failed to get scanner properties: {str(e)}",
                "device_id": device_id
            }

    @app.tool()
    async def configure_scan(
        device_id: str,
        dpi: int = 300,
        color_mode: str = "Color",
        paper_size: str = "A4",
        brightness: int = 0,
        contrast: int = 0,
        use_adf: bool = False,
        duplex: bool = False
    ) -> Dict[str, Any]:
        """
        Configure scan parameters for a scanner.

        Args:
            device_id: Scanner device ID
            dpi: Resolution in dots per inch (75, 150, 200, 300, 600, etc.)
            color_mode: Color mode ("Color", "Grayscale", "BlackWhite")
            paper_size: Paper size ("A4", "Letter", "Legal", "Custom")
            brightness: Brightness adjustment (-1000 to 1000)
            contrast: Contrast adjustment (-1000 to 1000)
            use_adf: Use Automatic Document Feeder if available
            duplex: Enable duplex scanning if supported

        Returns:
            Configuration status and applied settings
        """
        logger.info(f"Configuring scanner {device_id} with {dpi} DPI, {color_mode} mode")

        settings = {
            "dpi": dpi,
            "color_mode": color_mode,
            "paper_size": paper_size,
            "brightness": brightness,
            "contrast": contrast,
            "use_adf": use_adf,
            "duplex": duplex
        }

        try:
            success = backend_manager.scanner_manager.configure_scan(device_id, settings)

            if success:
                return {
                    "success": True,
                    "device_id": device_id,
                    "settings_applied": settings,
                    "message": f"Scanner {device_id} configured successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to configure scanner {device_id}",
                    "device_id": device_id,
                    "settings_requested": settings
                }

        except Exception as e:
            logger.error(f"Scanner configuration failed for {device_id}: {e}")
            return {
                "success": False,
                "error": f"Scanner configuration failed: {str(e)}",
                "device_id": device_id,
                "settings_requested": settings
            }

    @app.tool()
    async def scan_document(
        device_id: str,
        dpi: int = 300,
        color_mode: str = "Color",
        paper_size: str = "A4",
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform a single document scan.

        Args:
            device_id: Scanner device ID
            dpi: Resolution in dots per inch
            color_mode: Color mode ("Color", "Grayscale", "BlackWhite")
            paper_size: Paper size ("A4", "Letter", "Legal")
            save_path: Optional path to save the scanned image

        Returns:
            Scan results with image data and metadata
        """
        logger.info(f"Scanning document on {device_id}")

        settings = {
            "dpi": dpi,
            "color_mode": color_mode,
            "paper_size": paper_size
        }

        try:
            image = backend_manager.scanner_manager.scan_document(device_id, settings)

            if image is None:
                return {
                    "success": False,
                    "error": f"Scan failed on {device_id}",
                    "device_id": device_id,
                    "settings": settings
                }

            # Save image if path provided
            if save_path:
                try:
                    image.save(save_path)
                    logger.info(f"Scanned image saved to {save_path}")
                except Exception as e:
                    logger.warning(f"Failed to save image to {save_path}: {e}")

            # Get image metadata
            image_info = {
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "format": "PNG",  # PIL default
                "size_bytes": len(image.tobytes()) if hasattr(image, 'tobytes') else 0
            }

            return {
                "success": True,
                "device_id": device_id,
                "settings": settings,
                "image_info": image_info,
                "saved_to": save_path if save_path else None,
                "message": f"Document scanned successfully on {device_id}"
            }

        except Exception as e:
            logger.error(f"Document scan failed on {device_id}: {e}")
            return {
                "success": False,
                "error": f"Document scan failed: {str(e)}",
                "device_id": device_id,
                "settings": settings
            }

    @app.tool()
    async def scan_batch(
        device_id: str,
        count: int = 5,
        dpi: int = 300,
        color_mode: str = "Color",
        paper_size: str = "A4",
        save_directory: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform batch scanning of multiple documents.

        Args:
            device_id: Scanner device ID (must support ADF)
            count: Maximum number of documents to scan
            dpi: Resolution in dots per inch
            color_mode: Color mode ("Color", "Grayscale", "BlackWhite")
            paper_size: Paper size ("A4", "Letter", "Legal")
            save_directory: Directory to save scanned images

        Returns:
            Batch scan results with information about each scanned document
        """
        logger.info(f"Starting batch scan on {device_id} for up to {count} documents")

        settings = {
            "dpi": dpi,
            "color_mode": color_mode,
            "paper_size": paper_size,
            "use_adf": True  # Enable ADF for batch scanning
        }

        try:
            images = await backend_manager.scanner_manager.scan_batch(device_id, settings, count)

            if not images:
                return {
                    "success": False,
                    "error": f"Batch scan failed on {device_id}",
                    "device_id": device_id,
                    "settings": settings,
                    "documents_scanned": 0
                }

            # Save images if directory provided
            saved_files = []
            if save_directory:
                from pathlib import Path

                save_dir = Path(save_directory)
                save_dir.mkdir(parents=True, exist_ok=True)

                for i, image in enumerate(images):
                    filename = f"scan_{i+1:03d}.png"
                    filepath = save_dir / filename
                    try:
                        image.save(filepath)
                        saved_files.append(str(filepath))
                    except Exception as e:
                        logger.warning(f"Failed to save image {filename}: {e}")

            # Get batch statistics
            batch_info = []
            for i, image in enumerate(images):
                info = {
                    "document_number": i + 1,
                    "width": image.width,
                    "height": image.height,
                    "mode": image.mode,
                    "saved_to": saved_files[i] if i < len(saved_files) else None
                }
                batch_info.append(info)

            return {
                "success": True,
                "device_id": device_id,
                "settings": settings,
                "documents_scanned": len(images),
                "documents_requested": count,
                "batch_info": batch_info,
                "total_saved": len(saved_files),
                "save_directory": save_directory if save_directory else None,
                "message": f"Batch scan completed: {len(images)} documents scanned"
            }

        except Exception as e:
            logger.error(f"Batch scan failed on {device_id}: {e}")
            return {
                "success": False,
                "error": f"Batch scan failed: {str(e)}",
                "device_id": device_id,
                "settings": settings,
                "documents_scanned": 0
            }

    @app.tool()
    async def get_raw_scan(
        device_id: str,
        dpi: int = 300,
        color_mode: str = "Color",
        paper_size: str = "A4",
        brightness: int = 0,
        contrast: int = 0,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform raw scan acquisition without OCR processing.

        This tool acquires raw scanned image data directly from the scanner
        without any OCR processing. Use this when you need the scanned image
        for storage, display, or further processing.

        Args:
            device_id: Scanner device ID
            dpi: Resolution in dots per inch (75, 150, 200, 300, 600, etc.)
            color_mode: Color mode ("Color", "Grayscale", "BlackWhite")
            paper_size: Paper size ("A4", "Letter", "Legal", "Custom")
            brightness: Brightness adjustment (-1000 to 1000)
            contrast: Contrast adjustment (-1000 to 1000)
            save_path: Optional path to save the raw scanned image

        Returns:
            Raw scan results with image data and metadata (no OCR processing)
        """
        logger.info(f"Acquiring raw scan from {device_id} at {dpi} DPI")

        settings = {
            "dpi": dpi,
            "color_mode": color_mode,
            "paper_size": paper_size,
            "brightness": brightness,
            "contrast": contrast
        }

        try:
            # Configure scanner with the specified settings
            config_success = backend_manager.scanner_manager.configure_scan(device_id, settings)
            if not config_success:
                return {
                    "success": False,
                    "error": f"Failed to configure scanner {device_id} for raw scan",
                    "device_id": device_id,
                    "settings": settings
                }

            # Perform raw scan acquisition
            image = backend_manager.scanner_manager.scan_document(device_id, settings)

            if image is None:
                return {
                    "success": False,
                    "error": f"Raw scan acquisition failed on {device_id}",
                    "device_id": device_id,
                    "settings": settings
                }

            # Save image if path provided
            if save_path:
                try:
                    image.save(save_path)
                    logger.info(f"Raw scan saved to {save_path}")
                except Exception as e:
                    logger.warning(f"Failed to save raw scan to {save_path}: {e}")

            # Get comprehensive image metadata
            image_info = {
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "format": image.format or "PNG",
                "size_pixels": image.width * image.height,
                "color_depth": "24-bit" if image.mode == "RGB" else ("8-bit grayscale" if image.mode == "L" else "1-bit"),
                "file_size_bytes": len(image.tobytes()) if hasattr(image, 'tobytes') else 0
            }

            return {
                "success": True,
                "device_id": device_id,
                "scan_type": "raw_acquisition",
                "settings_applied": settings,
                "image_info": image_info,
                "saved_to": save_path if save_path else None,
                "message": f"Raw scan acquired successfully from {device_id}",
                "note": "This is raw image data only - no OCR processing performed"
            }

        except Exception as e:
            logger.error(f"Raw scan acquisition failed on {device_id}: {e}")
            return {
                "success": False,
                "error": f"Raw scan acquisition failed: {str(e)}",
                "device_id": device_id,
                "settings": settings
            }

    @app.tool()
    async def get_scanner_settings(device_id: str) -> Dict[str, Any]:
        """
        Query current scanner settings and capabilities.

        This tool retrieves the current configuration and supported capabilities
        of a scanner device, including supported resolutions, color modes,
        paper sizes, and current settings.

        Args:
            device_id: Scanner device ID

        Returns:
            Current scanner settings and supported capabilities
        """
        logger.info(f"Querying scanner settings for {device_id}")

        try:
            # Get scanner properties/capabilities
            properties = backend_manager.scanner_manager.get_scanner_properties(device_id)

            if not properties:
                return {
                    "success": False,
                    "error": f"Scanner not found or settings unavailable: {device_id}",
                    "device_id": device_id
                }

            # Get current scanner state if available
            current_settings = {}
            try:
                device = backend_manager.scanner_manager._devices.get(device_id)
                if device:
                    # Try to read current settings from device
                    current_settings = {
                        "current_dpi": getattr(device, 'current_dpi', 'unknown'),
                        "current_color_mode": getattr(device, 'current_color_mode', 'unknown'),
                        "current_paper_size": getattr(device, 'current_paper_size', 'unknown'),
                        "last_scan_time": getattr(device, 'last_scan_time', None)
                    }
            except Exception as e:
                logger.debug(f"Could not read current settings: {e}")

            return {
                "success": True,
                "device_id": device_id,
                "capabilities": {
                    "supported_resolutions": properties.supported_resolutions,
                    "supported_color_modes": properties.supported_color_modes,
                    "supported_paper_sizes": properties.supported_paper_sizes,
                    "max_paper_width_pixels": properties.max_paper_width,
                    "max_paper_height_pixels": properties.max_paper_height,
                    "supports_adf": properties.supports_adf,
                    "supports_duplex": properties.supports_duplex,
                    "supports_preview": properties.supports_preview,
                    "manufacturer": properties.manufacturer,
                    "model": properties.model,
                    "firmware_version": properties.firmware_version
                },
                "current_settings": current_settings,
                "message": f"Scanner settings retrieved for {device_id}"
            }

        except Exception as e:
            logger.error(f"Failed to query scanner settings for {device_id}: {e}")
            return {
                "success": False,
                "error": f"Failed to query scanner settings: {str(e)}",
                "device_id": device_id
            }

    @app.tool()
    async def set_scanner_settings(
        device_id: str,
        dpi: Optional[int] = None,
        color_mode: Optional[str] = None,
        paper_size: Optional[str] = None,
        brightness: Optional[int] = None,
        contrast: Optional[int] = None,
        use_adf: Optional[bool] = None,
        duplex: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Set scanner configuration parameters.

        This tool allows you to configure various scanner settings before
        performing scans. Only the parameters you specify will be changed.

        Args:
            device_id: Scanner device ID
            dpi: Resolution in dots per inch (75, 150, 200, 300, 600, etc.)
            color_mode: Color mode ("Color", "Grayscale", "BlackWhite")
            paper_size: Paper size ("A4", "Letter", "Legal", "Custom")
            brightness: Brightness adjustment (-1000 to 1000)
            contrast: Contrast adjustment (-1000 to 1000)
            use_adf: Use Automatic Document Feeder if available
            duplex: Enable duplex scanning if supported

        Returns:
            Settings update status and applied configuration
        """
        logger.info(f"Setting scanner configuration for {device_id}")

        # Build settings dict with only provided parameters
        settings = {}
        if dpi is not None:
            settings["dpi"] = dpi
        if color_mode is not None:
            settings["color_mode"] = color_mode
        if paper_size is not None:
            settings["paper_size"] = paper_size
        if brightness is not None:
            settings["brightness"] = brightness
        if contrast is not None:
            settings["contrast"] = contrast
        if use_adf is not None:
            settings["use_adf"] = use_adf
        if duplex is not None:
            settings["duplex"] = duplex

        if not settings:
            return {
                "success": False,
                "error": "No settings provided to update",
                "device_id": device_id
            }

        try:
            success = backend_manager.scanner_manager.configure_scan(device_id, settings)

            if success:
                return {
                    "success": True,
                    "device_id": device_id,
                    "settings_applied": settings,
                    "message": f"Scanner settings updated successfully for {device_id}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to apply scanner settings for {device_id}",
                    "device_id": device_id,
                    "settings_requested": settings
                }

        except Exception as e:
            logger.error(f"Scanner settings update failed for {device_id}: {e}")
            return {
                "success": False,
                "error": f"Scanner settings update failed: {str(e)}",
                "device_id": device_id,
                "settings_requested": settings
            }

    @app.tool()
    async def preview_scan(
        device_id: str,
        dpi: int = 150,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform a preview scan for positioning and cropping.

        Preview scans use lower resolution and are intended for
        setting up the scan area before performing the final scan.

        Args:
            device_id: Scanner device ID
            dpi: Preview resolution (typically 75-200 DPI)
            save_path: Optional path to save preview image

        Returns:
            Preview scan results
        """
        logger.info(f"Performing preview scan on {device_id} at {dpi} DPI")

        # Use low resolution for preview
        settings = {
            "dpi": min(dpi, 200),  # Cap preview at 200 DPI
            "color_mode": "Grayscale",  # Grayscale for faster preview
            "paper_size": "A4"
        }

        try:
            image = backend_manager.scanner_manager.scan_document(device_id, settings)

            if image is None:
                return {
                    "success": False,
                    "error": f"Preview scan failed on {device_id}",
                    "device_id": device_id
                }

            # Save preview if path provided
            if save_path:
                try:
                    image.save(save_path)
                    logger.info(f"Preview image saved to {save_path}")
                except Exception as e:
                    logger.warning(f"Failed to save preview to {save_path}: {e}")

            return {
                "success": True,
                "device_id": device_id,
                "preview_dpi": settings["dpi"],
                "image_info": {
                    "width": image.width,
                    "height": image.height,
                    "mode": image.mode
                },
                "saved_to": save_path if save_path else None,
                "message": f"Preview scan completed on {device_id}"
            }

        except Exception as e:
            logger.error(f"Preview scan failed on {device_id}: {e}")
            return {
                "success": False,
                "error": f"Preview scan failed: {str(e)}",
                "device_id": device_id
            }






