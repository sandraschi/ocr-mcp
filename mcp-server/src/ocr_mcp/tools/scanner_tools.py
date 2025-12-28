"""
Scanner Tools for OCR-MCP Server

Provides MCP tools for scanner discovery, configuration, and control.
"""

import logging
from typing import Dict, Any, Optional

from ..core.backend_manager import BackendManager
from ..core.config import OCRConfig

logger = logging.getLogger(__name__)


def register_scanner_tools(app, backend_manager: BackendManager, config: OCRConfig):
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






