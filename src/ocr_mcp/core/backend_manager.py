"""
OCR Backend Manager: Manages multiple OCR backends with unified interface
"""

import logging
from typing import Dict, Any, Optional, List

from .config import OCRConfig
from .backend_optimizer import BackendOptimizer
from .model_manager import model_manager

# Import scanner manager (optional)
try:
    from ..backends.scanner.scanner_manager import scanner_manager
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


class MockOCRBackend:
    """Mock backend for failed OCR backends - provides graceful degradation"""

    def __init__(self, backend_name: str, error_message: str):
        self.backend_name = backend_name
        self.error_message = error_message

    def is_available(self) -> bool:
        """Mock backends are never available"""
        return False

    async def load_model(self) -> bool:
        """Mock backends can't load models"""
        return False

    async def process_document(self, image_path: str, ocr_mode: str = "text", region: Optional[List[int]] = None) -> Dict[str, Any]:
        """Mock backends raise informative errors"""
        raise RuntimeError(f"{self.backend_name} backend is not available: {self.error_message}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Return mock capabilities"""
        return {
            "name": self.backend_name,
            "available": False,
            "error": self.error_message,
            "modes": ["text"],
            "languages": ["en"],
            "gpu_support": False,
            "strengths": [],
            "limitations": ["not_available"],
            "model_size": "unknown"
        }

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

        # Initialize backend optimizer for intelligent selection
        self.optimizer = BackendOptimizer(config)

        # Update model manager with config
        global model_manager
        model_manager.config = config

        # Initialize available backends
        self._initialize_backends()

    def _initialize_backends(self):
        """Initialize all available OCR backends."""

        # DeepSeek-OCR backend
        try:
            from ..backends.deepseek_backend import DeepSeekOCRBackend
            self.backends["deepseek-ocr"] = DeepSeekOCRBackend(self.config.__dict__)
            logger.info("DeepSeek-OCR backend initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize DeepSeek-OCR backend: {e}")
            self.backends["deepseek-ocr"] = MockOCRBackend("deepseek-ocr", str(e))

        # Florence-2 backend
        try:
            from ..backends.florence_backend import FlorenceBackend
            self.backends["florence-2"] = FlorenceBackend(self.config.__dict__)
            logger.info("Florence-2 backend initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Florence-2 backend: {e}")
            self.backends["florence-2"] = MockOCRBackend("florence-2", str(e))

        # DOTS.OCR backend
        try:
            from ..backends.dots_backend import DOTSBackend
            self.backends["dots-ocr"] = DOTSBackend(self.config.__dict__)
            logger.info("DOTS.OCR backend initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize DOTS.OCR backend: {e}")
            self.backends["dots-ocr"] = MockOCRBackend("dots-ocr", str(e))

        # PP-OCRv5 backend
        try:
            from ..backends.ppocr_backend import PPOCRBackend
            self.backends["pp-ocrv5"] = PPOCRBackend(self.config.__dict__)
            logger.info("PP-OCRv5 backend initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize PP-OCRv5 backend: {e}")
            self.backends["pp-ocrv5"] = MockOCRBackend("pp-ocrv5", str(e))

        # Qwen-Image-Layered backend
        try:
            from ..backends.qwen_backend import QwenLayeredBackend
            self.backends["qwen-layered"] = QwenLayeredBackend(self.config.__dict__)
            logger.info("Qwen-Image-Layered backend initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Qwen-Image-Layered backend: {e}")
            self.backends["qwen-layered"] = MockOCRBackend("qwen-layered", str(e))

        # Mistral OCR 3 backend (Cloud API)
        try:
            from ..backends.mistral_ocr_backend import MistralOCRBackend
            self.backends["mistral-ocr"] = MistralOCRBackend(self.config)
            logger.info("Mistral OCR 3 backend initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Mistral OCR 3 backend: {e}")
            self.backends["mistral-ocr"] = MockOCRBackend("mistral-ocr", str(e))

        # Legacy backends for compatibility
        try:
            from ..backends.got_ocr_backend import GOTOCRBackend
            self.backends["got-ocr"] = GOTOCRBackend(self.config)
            logger.info("GOT-OCR2.0 legacy backend initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize GOT-OCR legacy backend: {e}")
            self.backends["got-ocr"] = MockOCRBackend("got-ocr", str(e))

        try:
            from ..backends.tesseract_backend import TesseractBackend
            self.backends["tesseract"] = TesseractBackend(self.config)
            logger.info("Tesseract legacy backend initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Tesseract legacy backend: {e}")
            self.backends["tesseract"] = MockOCRBackend("tesseract", str(e))

        try:
            from ..backends.easyocr_backend import EasyOCRBackend
            self.backends["easyocr"] = EasyOCRBackend(self.config)
            logger.info("EasyOCR legacy backend initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize EasyOCR legacy backend: {e}")
            self.backends["easyocr"] = MockOCRBackend("easyocr", str(e))

    def get_available_backends(self) -> List[str]:
        """Get list of available backend names."""
        return [name for name, backend in self.backends.items() if backend.is_available()]

    def get_backend(self, name: str) -> Optional[OCRBackend]:
        """Get a specific backend by name."""
        return self.backends.get(name)

    def select_backend(self, requested_backend: str = "auto", image_path: Optional[str] = None) -> Optional[OCRBackend]:
        """Select an appropriate backend based on request."""
        if requested_backend == "auto":
            # Intelligent auto-selection based on document analysis
            if image_path:
                try:
                    from pathlib import Path
                    optimal_backend_name = self.optimizer.select_optimal_backend(Path(image_path))
                    if optimal_backend_name != "auto":
                        backend = self.get_backend(optimal_backend_name)
                        if backend and backend.is_available():
                            logger.info(f"Intelligent selection: {optimal_backend_name} for {Path(image_path).name}")
                            return backend
                except Exception as e:
                    logger.warning(f"Intelligent backend selection failed: {e}, falling back to preference order")

            # Fallback to preference order if intelligent selection fails
            preference_order = [
                "mistral-ocr",   # Mistral OCR 3: 74% win rate over OCR2, state-of-the-art
                "deepseek-ocr",  # 4.7M downloads, vision-language model
                "florence-2",    # Microsoft's unified vision-language model
                "dots-ocr",      # Document structure specialist
                "pp-ocrv5",      # Industrial PaddlePaddle OCR
                "qwen-layered",  # Image decomposition for complex content
                "got-ocr",       # Legacy GOT-OCR2.0
                "tesseract",     # Legacy Tesseract
                "easyocr"        # Legacy EasyOCR
            ]
            for backend_name in preference_order:
                backend = self.get_backend(backend_name)
                if backend and backend.is_available():
                    return backend

            # No backends available
            return None

        # Specific backend requested - handle common aliases
        backend_name_map = {
            "deepseek": "deepseek-ocr",
            "florence": "florence-2",
            "dots": "dots-ocr",
            "pp-ocr": "pp-ocrv5",
            "qwen": "qwen-layered",
            "got": "got-ocr",
            "tesseract": "tesseract",
            "easyocr": "easyocr"
        }

        # Normalize backend name
        normalized_backend = backend_name_map.get(requested_backend, requested_backend)

        backend = self.get_backend(normalized_backend)
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
        backend = self.select_backend(backend_name, image_path)
        if not backend:
            return {
                "success": False,
                "error": f"No suitable OCR backend available for '{backend_name}'",
                "available_backends": self.get_available_backends()
            }

        try:
            # Call the appropriate processing method
            if hasattr(backend, 'process_document'):
                # New backend interface
                result = await backend.process_document(image_path, ocr_mode=mode, **kwargs)
            elif hasattr(backend, 'process_image'):
                # Legacy backend interface
                result = await backend.process_image(image_path, mode, **kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Backend {backend.name} does not implement processing interface",
                    "backend_used": backend.name
                }

            result["backend_used"] = backend.name
            return result
        except Exception as e:
            logger.error(f"Error processing with {backend.name}: {e}")
            return {
                "success": False,
                "error": f"OCR processing failed with {backend.name}: {str(e)}",
                "backend_used": backend.name
            }

    def get_model_stats(self) -> Dict[str, Any]:
        """Get model memory and performance statistics"""
        return model_manager.get_memory_stats()

    def optimize_models(self, target_free_mb: int = 1024) -> Dict[str, Any]:
        """Optimize model memory usage"""
        freed_memory = model_manager.optimize_memory(target_free_mb)
        return {
            "memory_freed_mb": freed_memory,
            "optimization_complete": True
        }

    def preload_models(self) -> Dict[str, Any]:
        """Preload commonly used models"""
        preloaded_count = model_manager.preload_common_models()
        return {
            "models_preloaded": preloaded_count,
            "preloading_complete": True
        }

    def cleanup_idle_models(self, max_idle_seconds: int = 300) -> Dict[str, Any]:
        """Clean up idle models"""
        cleaned_count = model_manager.cleanup_idle_models(max_idle_seconds)
        return {
            "models_cleaned": cleaned_count,
            "cleanup_complete": True
        }
