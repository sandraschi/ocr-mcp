"""
OCR Backend Manager: Manages multiple OCR backends with unified interface
"""

import logging
from typing import Dict, Any, Optional, List

from .config import OCRConfig

# Import scanner manager (optional)
try:
    from ..backends.scanner import scanner_manager
    SCANNER_AVAILABLE = scanner_manager.is_available()
except (ImportError, AttributeError):
    SCANNER_AVAILABLE = False
    scanner_manager = None

# Import document processor (optional)
try:
    from ..backends.document_processor import document_processor
    DOCUMENT_PROCESSOR_AVAILABLE = document_processor.is_available()
except (ImportError, AttributeError):
    DOCUMENT_PROCESSOR_AVAILABLE = False
    document_processor = None

logger = logging.getLogger(__name__)


class OCRBackend:
    """Base class for OCR backends."""

    def __init__(self, name: str, config: OCRConfig):
        self.name = name
        self.config = config
        self._available = False

    def is_available(self) -> bool:
        """Check if this backend is available."""
        return self._available

    async def process_image(
        self,
        image_path: str,
        mode: str = "text",
        **kwargs
    ) -> Dict[str, Any]:
        """Process an image with this backend."""
        raise NotImplementedError("Subclasses must implement process_image")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get backend capabilities."""
        return {
            "name": self.name,
            "available": self.is_available(),
            "modes": ["text"],  # Default capabilities
            "languages": ["en"],
            "gpu_support": False
        }


class BackendManager:
    """Manages multiple OCR backends with unified interface."""

    def __init__(self, config: OCRConfig):
        self.config = config
        self.backends: Dict[str, OCRBackend] = {}
        self.scanner_manager = scanner_manager
        self.document_processor = document_processor

        # Initialize available backends
        self._initialize_backends()

    def _initialize_backends(self):
        """Initialize all available OCR backends."""
        from ..backends.got_ocr_backend import GOTOCRBackend
        from ..backends.tesseract_backend import TesseractBackend
        from ..backends.easyocr_backend import EasyOCRBackend

        # GOT-OCR2.0 backend
        try:
            self.backends["got-ocr"] = GOTOCRBackend(self.config)
            logger.info("GOT-OCR2.0 backend initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize GOT-OCR backend: {e}")

        # Tesseract backend
        try:
            self.backends["tesseract"] = TesseractBackend(self.config)
            logger.info("Tesseract backend initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Tesseract backend: {e}")

        # EasyOCR backend
        try:
            self.backends["easyocr"] = EasyOCRBackend(self.config)
            logger.info("EasyOCR backend initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize EasyOCR backend: {e}")

    def get_available_backends(self) -> List[str]:
        """Get list of available backend names."""
        return [name for name, backend in self.backends.items() if backend.is_available()]

    def get_backend(self, name: str) -> Optional[OCRBackend]:
        """Get a specific backend by name."""
        return self.backends.get(name)

    def select_backend(self, requested_backend: str = "auto") -> Optional[OCRBackend]:
        """Select an appropriate backend based on request."""
        if requested_backend == "auto":
            # Auto-select: prefer GOT-OCR, then Tesseract, then EasyOCR
            preference_order = ["got-ocr", "tesseract", "easyocr"]
            for backend_name in preference_order:
                backend = self.get_backend(backend_name)
                if backend and backend.is_available():
                    return backend

            # No backends available
            return None

        # Specific backend requested
        backend = self.get_backend(requested_backend)
        if backend and backend.is_available():
            return backend

        # Fallback to auto-selection if requested backend not available
        logger.warning(f"Requested backend '{requested_backend}' not available, falling back to auto-selection")
        return self.select_backend("auto")

    async def process_with_backend(
        self,
        backend_name: str,
        image_path: str,
        mode: str = "text",
        **kwargs
    ) -> Dict[str, Any]:
        """Process an image with a specific backend."""
        backend = self.select_backend(backend_name)
        if not backend:
            return {
                "success": False,
                "error": f"No suitable OCR backend available for '{backend_name}'",
                "available_backends": self.get_available_backends()
            }

        try:
            result = await backend.process_image(image_path, mode, **kwargs)
            result["backend_used"] = backend.name
            return result
        except Exception as e:
            logger.error(f"Error processing with {backend.name}: {e}")
            return {
                "success": False,
                "error": f"OCR processing failed with {backend.name}: {str(e)}",
                "backend_used": backend.name
            }
