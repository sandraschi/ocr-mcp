"""
Scanner Manager: Unified interface for multiple scanner backends

Orchestrates WIA, TWAIN, and other scanner control systems with a unified API.
"""

import logging
from typing import Dict, Any, Optional, List

from .wia_scanner import WIABackend, ScannerInfo, ScanSettings, ScannerProperties
from .bridge_scanner import BridgeScannerBackend

logger = logging.getLogger(__name__)


class ScannerManager:
    """
    Unified scanner management across multiple backends.

    Provides a consistent interface for scanner discovery, configuration,
    and control regardless of the underlying scanner API used.
    """

    def __init__(self):
        self.backends = {
            "wia": WIABackend(),
            "bridge": BridgeScannerBackend(),
            # Future: "twain": TWAINBackend(),
            # Future: "sane": SANEBackend(),
        }
        self._discovered_scanners = {}
        self._last_discovery = None

    def is_available(self) -> bool:
        """Check if any scanner backend is available."""
        return any(backend.is_available() for backend in self.backends.values())

    def discover_scanners(self, force_refresh: bool = False) -> List[ScannerInfo]:
        """
        Discover all connected scanners across all backends.

        Args:
            force_refresh: Force rediscovery even if cached

        Returns:
            List of all discovered scanners
        """
        if not force_refresh and self._last_discovery and self._discovered_scanners:
            # Return cached results if recent enough
            return list(self._discovered_scanners.values())

        all_scanners = []
        self._discovered_scanners = {}

        for backend_name, backend in self.backends.items():
            if backend.is_available():
                try:
                    scanners = backend.discover_scanners()
                    for scanner in scanners:
                        # Prefix device_id with backend name to avoid conflicts
                        unique_id = f"{backend_name}:{scanner.device_id}"
                        scanner.device_id = unique_id
                        self._discovered_scanners[unique_id] = scanner
                        all_scanners.append(scanner)

                    logger.info(
                        f"{backend_name.upper()} backend found {len(scanners)} scanners"
                    )
                except Exception as e:
                    logger.error(f"Error discovering scanners with {backend_name}: {e}")

        self._last_discovery = all_scanners
        logger.info(f"Total scanners discovered: {len(all_scanners)}")
        return all_scanners

    def get_scanner_info(self, device_id: str) -> Optional[ScannerInfo]:
        """
        Get information about a specific scanner.

        Args:
            device_id: Scanner device ID (with backend prefix)

        Returns:
            ScannerInfo object or None if not found
        """
        # Ensure we have discovered scanners
        if not self._discovered_scanners:
            self.discover_scanners()

        return self._discovered_scanners.get(device_id)

    def get_scanner_properties(self, device_id: str) -> Optional[ScannerProperties]:
        """
        Get detailed properties for a scanner.

        Args:
            device_id: Scanner device ID (with backend prefix)

        Returns:
            ScannerProperties object or None if not found
        """
        backend_name, actual_device_id = self._parse_device_id(device_id)
        backend = self.backends.get(backend_name)

        if not backend or not backend.is_available():
            return None

        try:
            # Remove backend prefix for backend-specific call
            return backend.get_scanner_properties(actual_device_id)
        except Exception as e:
            logger.error(f"Failed to get properties for scanner {device_id}: {e}")
            return None

    def configure_scan(self, device_id: str, settings: Dict[str, Any]) -> bool:
        """
        Configure scan settings for a scanner.

        Args:
            device_id: Scanner device ID (with backend prefix)
            settings: Dictionary of scan settings

        Returns:
            True if configuration successful
        """
        backend_name, actual_device_id = self._parse_device_id(device_id)
        backend = self.backends.get(backend_name)

        if not backend or not backend.is_available():
            return False

        try:
            # Convert dict to ScanSettings object
            scan_settings = ScanSettings(**settings)
            return backend.configure_scan(actual_device_id, scan_settings)
        except Exception as e:
            logger.error(f"Failed to configure scanner {device_id}: {e}")
            return False

    def scan_document(self, device_id: str, settings: Dict[str, Any]) -> Optional[Any]:
        """
        Perform a document scan.

        Args:
            device_id: Scanner device ID (with backend prefix)
            settings: Dictionary of scan settings

        Returns:
            PIL Image object if successful, None otherwise
        """
        backend_name, actual_device_id = self._parse_device_id(device_id)
        backend = self.backends.get(backend_name)

        if not backend or not backend.is_available():
            return None

        try:
            # Convert dict to ScanSettings object
            scan_settings = ScanSettings(**settings)
            return backend.scan_document(actual_device_id, scan_settings)
        except Exception as e:
            logger.error(f"Failed to scan document on {device_id}: {e}")
            return None

    async def scan_batch(
        self,
        device_id: str,
        settings: Dict[str, Any],
        count: int = 10,
        auto_process: bool = True,
    ) -> List[Any]:
        """
        Perform batch scanning of multiple documents.

        Args:
            device_id: Scanner device ID (with backend prefix)
            settings: Dictionary of scan settings
            count: Maximum number of documents to scan
            auto_process: Whether to automatically process each scan

        Returns:
            List of PIL Image objects
        """
        backend_name, actual_device_id = self._parse_device_id(device_id)
        backend = self.backends.get(backend_name)

        if not backend or not backend.is_available():
            return []

        images = []
        try:
            for i in range(count):
                logger.info(f"Scanning document {i + 1}/{count}")

                # Configure scanner for batch mode
                batch_settings = settings.copy()
                batch_settings["use_adf"] = True  # Enable ADF for batch scanning

                image = self.scan_document(device_id, batch_settings)
                if image:
                    images.append(image)
                    logger.info(f"Document {i + 1} scanned successfully")
                else:
                    logger.warning(f"Failed to scan document {i + 1}")
                    break  # Stop on first failure

        except Exception as e:
            logger.error(f"Batch scanning failed on {device_id}: {e}")

        logger.info(f"Batch scanning completed: {len(images)} documents scanned")
        return images

    def _parse_device_id(self, device_id: str) -> tuple[str, str]:
        """
        Parse device ID to extract backend name and actual device ID.

        Args:
            device_id: Full device ID with backend prefix (e.g., "wia:device123")

        Returns:
            Tuple of (backend_name, actual_device_id)
        """
        if ":" in device_id:
            backend_name, actual_device_id = device_id.split(":", 1)
            return backend_name, actual_device_id
        else:
            # Assume WIA if no prefix (backward compatibility)
            return "wia", device_id

    def get_available_backends(self) -> List[str]:
        """Get list of available scanner backends."""
        return [
            name for name, backend in self.backends.items() if backend.is_available()
        ]

    def get_backend_status(self) -> Dict[str, bool]:
        """Get status of all scanner backends."""
        return {name: backend.is_available() for name, backend in self.backends.items()}


# Global scanner manager instance
scanner_manager = ScannerManager()
