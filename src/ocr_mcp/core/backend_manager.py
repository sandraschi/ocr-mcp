"""
OCR Backend Manager: Manages multiple OCR backends with unified interface
"""

import inspect
import logging
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from .backend_optimizer import BackendOptimizer
from .config import OCRConfig
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

    async def process_document(
        self,
        image_path: str,
        ocr_mode: str = "text",
        region: list[int] | None = None,
    ) -> dict[str, Any]:
        """Mock backends raise informative errors"""
        raise RuntimeError(f"{self.backend_name} backend is not available: {self.error_message}")

    def get_capabilities(self) -> dict[str, Any]:
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
            "model_size": "unknown",
        }


logger = logging.getLogger(__name__)

# Optimizer / docs may still say "florence-2"; registry uses concrete package names only.
_BACKEND_NAME_ALIASES: dict[str, str] = {
    "deepseek": "deepseek-ocr",
    "deepseek2": "deepseek-ocr2",
    "deepseek-ocr-2": "deepseek-ocr2",
    "paddleocr": "paddleocr-vl",
    "paddle": "paddleocr-vl",
    "paddleocr-vl-1.5": "paddleocr-vl",
    "olmocr": "olmocr-2",
    "olm": "olmocr-2",
    "florence": "paddleocr-vl",
    "florence-2": "paddleocr-vl",
    "dots": "dots-ocr",
    "pp-ocr": "pp-ocrv5",
    "qwen": "qwen-layered",
    "got": "got-ocr",
    "tesseract": "tesseract",
    "easyocr": "easyocr",
    "mineru": "mineru-2.5",
}


def canonical_backend_name(name: str) -> str:
    """Map legacy / marketing names to registry keys."""
    return _BACKEND_NAME_ALIASES.get(name, name)


class OCRBackend:
    """Base class for OCR backends."""

    def __init__(self, name: str, config: OCRConfig):
        self.name = name
        self.config = config
        self._available = False

    def is_available(self) -> bool:
        """Check if this backend is available."""
        return self._available

    async def process_image(self, image_path: str, mode: str = "text", **kwargs) -> dict[str, Any]:
        """Process an image with this backend."""
        raise NotImplementedError("Subclasses must implement process_image")

    def get_capabilities(self) -> dict[str, Any]:
        """Get backend capabilities."""
        return {
            "name": self.name,
            "available": self.is_available(),
            "modes": ["text"],  # Default capabilities
            "languages": ["en"],
            "gpu_support": False,
        }


class BackendManager:
    """Manages multiple OCR backends with unified interface and lazy loading."""

    def __init__(self, config: OCRConfig):
        self.config = config
        self.backends: dict[str, OCRBackend | None] = {}  # Allow None for lazy loading
        self.scanner_manager = scanner_manager
        self.document_processor = document_processor

        # Initialize backend optimizer for intelligent selection
        self.optimizer = BackendOptimizer(config)

        # Update model manager with config
        global model_manager
        model_manager.config = config

        # Initialize backend registry (lazy loading - no actual imports yet!)
        self._initialize_backend_registry()

    def _initialize_backend_registry(self):
        """Initialize backend registry for lazy loading - no actual imports yet!"""
        # Registry of available backends with their import paths and model sizes
        self.backend_registry = {
            "deepseek-ocr": {
                "module": "..backends.deepseek_backend",
                "class": "DeepSeekOCRBackend",
                "model_size": "~500MB+",
                "description": "DeepSeek-OCR cloud API",
            },
            "paddleocr-vl": {
                "module": "..backends.paddleocr_vl_backend",
                "class": "PaddleOCRVLBackend",
                "model_size": "~1.8GB (0.9B params)",
                "description": "Baidu PaddleOCR-VL-1.5 — Jan 2026 SOTA, 94.5% OmniDocBench",
            },
            "deepseek-ocr2": {
                "module": "..backends.deepseek_ocr2_backend",
                "class": "DeepSeekOCR2Backend",
                "model_size": "~6GB (3B params)",
                "description": "DeepSeek-OCR-2 — Jan 2026, Visual Causal Flow",
            },
            "olmocr-2": {
                "module": "..backends.olmocr_backend",
                "class": "OlmOCR2Backend",
                "model_size": "~14GB (7B params)",
                "description": "Allen AI olmOCR-2 — Oct 2025, best for academic PDFs",
            },
            "dots-ocr": {
                "module": "..backends.dots_backend",
                "class": "DOTSBackend",
                "model_size": "~200MB",
                "description": "DOTS.OCR specialized OCR model",
            },
            "pp-ocrv5": {
                "module": "..backends.ppocr_backend",
                "class": "PPOCRBackend",
                "model_size": "~100MB",
                "description": "PaddlePaddle PP-OCRv5",
            },
            "qwen-layered": {
                "module": "..backends.qwen_backend",
                "class": "QwenLayeredBackend",
                "model_size": "~2GB+",
                "description": "Qwen-VL image layered processing",
            },
            "mistral-ocr": {
                "module": "..backends.mistral_ocr_backend",
                "class": "MistralOCRBackend",
                "model_size": "~500MB",
                "description": "Mistral OCR 3 cloud API",
            },
            "mineru-2.5": {
                "module": "..backends.mineru_backend",
                "class": "MinerU25Backend",
                "model_size": "~2.5GB (1.2B params)",
                "description": "MinerU2.5-Pro — Apr 2026, opendatalab coarse-to-fine doc parsing VLM",
            },
            "got-ocr": {
                "module": "..backends.got_ocr_backend",
                "class": "GOTOCRBackend",
                "model_size": "~300MB",
                "description": "GOT-OCR2.0 legacy backend",
            },
            "tesseract": {
                "module": "..backends.tesseract_backend",
                "class": "TesseractBackend",
                "model_size": "~50MB",
                "description": "Tesseract OCR engine",
            },
            "easyocr": {
                "module": "..backends.easyocr_backend",
                "class": "EasyOCRBackend",
                "model_size": "~200MB",
                "description": "EasyOCR with CRAFT detector",
            },
        }

        # Initialize registry in backends dict (None means not loaded yet)
        for backend_name in self.backend_registry:
            self.backends[backend_name] = None  # Lazy loading placeholder

    def _load_backend(self, backend_name: str) -> OCRBackend:
        """Lazy load a backend only when first accessed."""
        if backend_name not in self.backend_registry:
            raise ValueError(f"Unknown backend: {backend_name}")

        # Return already loaded backend
        if self.backends[backend_name] is not None:
            return self.backends[backend_name]

        # Lazy load the backend - this is where the heavy lifting happens!
        try:
            registry_info = self.backend_registry[backend_name]
            module_path = registry_info["module"]
            class_name = registry_info["class"]
            model_size = registry_info["model_size"]

            logger.info(f"Lazy loading {backend_name} backend ({model_size})...")

            # Dynamic import - only load when needed!
            import importlib

            module = importlib.import_module(module_path, __package__)
            backend_class = getattr(module, class_name)

            # Create instance
            backend_instance = backend_class(self.config)
            self.backends[backend_name] = backend_instance

            logger.info(f"[OK] {backend_name} backend loaded successfully")
            return backend_instance

        except Exception as e:
            logger.warning(f"Failed to lazy-load {backend_name} backend: {e}")
            mock_backend = MockOCRBackend(backend_name, str(e))
            self.backends[backend_name] = mock_backend
            return mock_backend

    def get_available_backends(self) -> list[str]:
        """Get list of available backend names (lazy loading compatible)."""
        available = []
        for name in self.backends.keys():
            backend = self.get_backend(name)  # This triggers lazy loading if needed
            if backend and backend.is_available():
                available.append(name)
        return available

    def get_backend(self, name: str) -> OCRBackend | None:
        """Get a specific backend by name (lazy loading)."""
        if name not in self.backends:
            return None

        # Lazy load if not already loaded
        if self.backends[name] is None:
            self.backends[name] = self._load_backend(name)

        return self.backends[name]

    def invalidate_backend(self, name: str) -> None:
        """Drop cached backend so the next ``get_backend`` reloads (e.g. after API key change)."""
        if name in self.backends:
            self.backends[name] = None

    def select_backend(self, requested_backend: str = "auto", image_path: str | None = None) -> OCRBackend | None:
        """Select an appropriate backend based on request."""
        if requested_backend == "auto":
            # Intelligent auto-selection based on document analysis
            if image_path:
                try:
                    from pathlib import Path

                    optimal_backend_name = self.optimizer.select_optimal_backend(Path(image_path))
                    if optimal_backend_name != "auto":
                        resolved = canonical_backend_name(optimal_backend_name)
                        backend = self.get_backend(resolved)
                        if backend and backend.is_available():
                            logger.info(
                                "Intelligent selection: %s → %s for %s",
                                optimal_backend_name,
                                resolved,
                                Path(image_path).name,
                            )
                            return backend
                        if resolved != optimal_backend_name:
                            logger.warning(
                                "Optimizer suggested %s (resolved %s) but it is unavailable; using fallback order",
                                optimal_backend_name,
                                resolved,
                            )
                except Exception as e:
                    logger.warning(f"Intelligent backend selection failed: {e}, falling back to preference order")

            # Fallback: light reliable engines first so flatbed scans succeed without huge downloads.
            preference_order = [
                "tesseract",
                "pp-ocrv5",
                "got-ocr",
                "dots-ocr",
                "easyocr",
                "paddleocr-vl",
            "mistral-ocr",
            "deepseek-ocr2",
            "mineru-2.5",
            "olmocr-2",
                "deepseek-ocr",
                "qwen-layered",
            ]
            for backend_name in preference_order:
                backend = self.get_backend(backend_name)
                if backend and backend.is_available():
                    return backend

            # No backends available
            return None

        # Specific backend requested - handle common aliases
        normalized_backend = canonical_backend_name(requested_backend)

        backend = self.get_backend(normalized_backend)
        if backend and backend.is_available():
            return backend

        # Fallback to auto-selection if requested backend not available
        logger.warning(f"Requested backend '{requested_backend}' not available, falling back to auto-selection")
        return self.select_backend("auto")

    async def process_with_backend(
        self, backend_name: str, image_path: str, mode: str = "text", **kwargs
    ) -> dict[str, Any]:
        """Process an image with a specific backend."""
        backend = self.select_backend(backend_name, image_path)
        if not backend:
            return {
                "success": False,
                "error": f"No suitable OCR backend available for '{backend_name}'",
                "available_backends": self.get_available_backends(),
            }

        try:
            # Load model if needed (for newer backends)
            if hasattr(backend, "load_model"):
                if (
                    (hasattr(backend, "model") and backend.model is None)
                    or (hasattr(backend, "ocr") and backend.ocr is None)
                    or (hasattr(backend, "pipeline") and backend.pipeline is None)
                ):
                    logger.info(f"Automatically loading model/engine for {backend.name}")
                    loaded = await backend.load_model()
                    if loaded is False:
                        return {
                            "success": False,
                            "error": (
                                f"Model engine failed to load for '{backend.name}'. "
                                "Check server logs (HF download, disk space, CUDA OOM). "
                                "Try backend tesseract or pp-ocrv5 for offline scans."
                            ),
                            "backend_used": backend.name,
                        }

            # Call the appropriate processing method
            if hasattr(backend, "process_document"):
                # New backend interface
                import inspect

                sig = inspect.signature(backend.process_document)
                if "ocr_mode" in sig.parameters:
                    result = await backend.process_document(image_path, ocr_mode=mode, **kwargs)
                else:
                    result = await backend.process_document(image_path, mode=mode, **kwargs)
            elif hasattr(backend, "process_image"):
                # Legacy backend interface
                result = await backend.process_image(image_path, mode, **kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Backend {backend.name} does not implement processing interface",
                    "backend_used": backend.name,
                }

            result["backend_used"] = backend.name
            return result
        except Exception as e:
            logger.error(f"Error processing with {backend.name}: {e}")
            return {
                "success": False,
                "error": f"OCR processing failed with {backend.name}: {e!s}",
                "backend_used": backend.name,
            }

    def list_backends(self) -> dict[str, Any]:
        """List all registered backends with availability and capabilities.

        Returns a dict with backends (dict keyed by backend name), available_count,
        total_count, and a sorted list of names.
        """
        backends_info: dict[str, dict[str, Any]] = {}
        available_count = 0
        for name, meta in self.backend_registry.items():
            backend = self.get_backend(name)
            available = bool(backend and backend.is_available())
            if available:
                available_count += 1
            capabilities: dict[str, Any] = {}
            if backend and hasattr(backend, "get_capabilities"):
                try:
                    capabilities = backend.get_capabilities()
                except Exception:
                    pass
            backends_info[name] = {
                "name": name,
                "available": available,
                "description": meta.get("description", f"{name} OCR backend"),
                "model_size": meta.get("model_size", "unknown"),
                "capabilities": capabilities,
            }
        return {
            "backends": backends_info,
            "available_count": available_count,
            "total_count": len(self.backend_registry),
        }

    def get_model_stats(self) -> dict[str, Any]:
        """Get model memory and performance statistics"""
        return model_manager.get_memory_stats()

    def optimize_models(self, target_free_mb: int = 1024) -> dict[str, Any]:
        """Optimize model memory usage"""
        freed_memory = model_manager.optimize_memory(target_free_mb)
        return {"memory_freed_mb": freed_memory, "optimization_complete": True}

    def preload_models(self) -> dict[str, Any]:
        """Preload commonly used models"""
        preloaded_count = model_manager.preload_common_models()
        return {"models_preloaded": preloaded_count, "preloading_complete": True}

    def cleanup_idle_models(self, max_idle_seconds: int = 300) -> dict[str, Any]:
        """Clean up idle models"""
        cleaned_count = model_manager.cleanup_idle_models(max_idle_seconds)
        return {"models_cleaned": cleaned_count, "cleanup_complete": True}

    async def probe_backend(self, backend_name: str) -> dict[str, Any]:
        """Run availability + optional load_model + tiny sample OCR on *this* backend only (no auto-fallback)."""
        raw = (backend_name or "").strip()
        if not raw:
            return {"success": False, "error": "Empty backend name", "backend": ""}

        n = raw.lower()
        key = _BACKEND_NAME_ALIASES.get(n, n)
        if key not in self.backend_registry:
            return {"success": False, "error": f"Unknown backend '{raw}'", "backend": key}

        backend = self.get_backend(key)
        if isinstance(backend, MockOCRBackend):
            return {
                "success": False,
                "error": backend.error_message,
                "backend": key,
                "phase": "import_or_init",
            }
        if not backend.is_available():
            return {
                "success": False,
                "error": "Backend reported not available (missing deps, GPU, API keys, etc.).",
                "backend": key,
                "phase": "availability",
            }

        if hasattr(backend, "load_model"):
            try:
                loaded = await backend.load_model()
                if loaded is False:
                    return {
                        "success": False,
                        "error": "load_model returned False (see server logs).",
                        "backend": key,
                        "phase": "load_model",
                    }
            except Exception as e:
                logger.warning("probe_backend load_model %s: %s", key, e)
                return {
                    "success": False,
                    "error": f"load_model failed: {e}",
                    "backend": key,
                    "phase": "load_model",
                }

        tmp_path: Path | None = None
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.close()
            tmp_path = Path(tmp.name)
            img = Image.new("RGB", (280, 80), color="white")
            draw = ImageDraw.Draw(img)
            draw.rectangle((10, 10, 270, 70), outline="black", width=2)
            draw.text((24, 28), "OCR probe OK", fill="black")
            img.save(tmp_path, format="PNG")

            if hasattr(backend, "process_document"):
                sig = inspect.signature(backend.process_document)
                if "ocr_mode" in sig.parameters:
                    result = await backend.process_document(str(tmp_path), ocr_mode="text")
                else:
                    result = await backend.process_document(str(tmp_path), mode="text")
            elif hasattr(backend, "process_image"):
                result = await backend.process_image(str(tmp_path), "text")
            else:
                return {
                    "success": False,
                    "error": "Backend has no process_document / process_image",
                    "backend": key,
                    "phase": "run",
                }

            if not isinstance(result, dict):
                return {
                    "success": False,
                    "error": f"Unexpected result type: {type(result).__name__}",
                    "backend": key,
                    "phase": "run",
                }

            err = result.get("error")
            explicit_fail = result.get("success") is False
            explicit_ok = result.get("success") is True
            text = (result.get("text") or "").strip()
            ok = explicit_ok or (not explicit_fail and not err and bool(text))
            if explicit_fail and text:
                ok = True

            preview = text[:240] if text else ""
            return {
                "success": ok,
                "backend": key,
                "phase": "ocr_sample",
                "sample_text_preview": preview or None,
                "error": None if ok else (err or result.get("message") or "OCR returned no usable text"),
            }
        except Exception as e:
            logger.exception("probe_backend OCR sample failed backend=%s", key)
            return {
                "success": False,
                "error": str(e),
                "backend": key,
                "phase": "ocr_sample",
            }
        finally:
            if tmp_path is not None:
                try:
                    tmp_path.unlink(missing_ok=True)
                except OSError:
                    pass
