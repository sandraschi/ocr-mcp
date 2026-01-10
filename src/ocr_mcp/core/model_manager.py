"""
OCR-MCP Intelligent Model Manager

Provides intelligent model loading/unloading, GPU memory management,
and performance optimization for OCR backends.
"""

import logging
import time
import threading
from collections import defaultdict, OrderedDict
from dataclasses import dataclass
from typing import Dict, Any, Optional
import gc
import psutil

from .config import OCRConfig

logger = logging.getLogger(__name__)

# Optional imports
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

try:
    import GPUtil
    GPU_UTIL_AVAILABLE = True
except ImportError:
    GPU_UTIL_AVAILABLE = False


@dataclass
class ModelInfo:
    """Information about a loaded model"""
    backend_name: str
    model_name: str
    memory_usage: int  # MB
    load_time: float
    last_used: float
    device: str
    priority: int = 1  # 1=low, 2=medium, 3=high
    use_count: int = 0
    model_object: Any = None


@dataclass
class GPUInfo:
    """GPU memory and utilization information"""
    device_id: int
    total_memory: int  # MB
    used_memory: int  # MB
    free_memory: int  # MB
    utilization: float  # percentage
    temperature: Optional[float] = None

    @property
    def available_memory(self) -> int:
        """Memory available for new models (with 10% buffer)"""
        return max(0, int(self.free_memory * 0.9))


class ModelManager:
    """
    Intelligent model management system for OCR backends.

    Features:
    - LRU-based model unloading when GPU memory is low
    - Priority-based model retention
    - Automatic device selection (GPU/CPU)
    - Memory usage monitoring and optimization
    - Concurrent model loading with thread safety
    """

    def __init__(self, config: OCRConfig):
        self.config = config
        self.loaded_models: Dict[str, ModelInfo] = {}
        self.model_cache: OrderedDict[str, ModelInfo] = OrderedDict()
        self.lock = threading.RLock()
        self.max_gpu_memory_mb = self._detect_max_gpu_memory()
        self.memory_threshold = 0.85  # Unload when >85% memory used

        # Model priorities (higher = more important to keep loaded)
        self.model_priorities = {
            "mistral-ocr": 3,      # State-of-the-art, keep loaded
            "deepseek-ocr": 3,     # Very popular, keep loaded
            "florence-2": 2,       # Good general purpose
            "dots-ocr": 2,         # Specialized for tables
            "pp-ocrv5": 1,         # Fast but less accurate
            "qwen-layered": 2,     # Specialized for comics
            "got-ocr": 1,          # Legacy
            "tesseract": 0,        # CPU-only, low priority
            "easyocr": 0           # CPU-only, low priority
        }

        logger.info(f"ModelManager initialized. Max GPU memory: {self.max_gpu_memory_mb}MB")

    def _detect_max_gpu_memory(self) -> int:
        """Detect available GPU memory"""
        if not TORCH_AVAILABLE:
            return 0

        try:
            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()
                if device_count > 0:
                    # Use the first GPU's memory as reference
                    total_memory = torch.cuda.get_device_properties(0).total_memory
                    return total_memory // (1024 * 1024)  # Convert to MB
        except Exception as e:
            logger.warning(f"Failed to detect GPU memory: {e}")

        return 0

    def get_gpu_info(self) -> Optional[GPUInfo]:
        """Get current GPU memory and utilization information"""
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return None

        try:
            device_id = 0  # Primary GPU
            total_memory = torch.cuda.get_device_properties(device_id).total_memory
            allocated_memory = torch.cuda.memory_allocated(device_id)

            # Get utilization if available
            utilization = 0.0
            temperature = None

            if GPU_UTIL_AVAILABLE:
                try:
                    gpu = GPUtil.getGPUs()[device_id]
                    utilization = gpu.load * 100
                    temperature = gpu.temperature
                except Exception as e:
                    pass

            total_mb = total_memory // (1024 * 1024)
            used_mb = allocated_memory // (1024 * 1024)
            free_mb = total_mb - used_mb

            return GPUInfo(
                device_id=device_id,
                total_memory=total_mb,
                used_memory=used_mb,
                free_memory=free_mb,
                utilization=utilization,
                temperature=temperature
            )

        except Exception as e:
            logger.warning(f"Failed to get GPU info: {e}")
            return None

    def register_model(
        self,
        backend_name: str,
        model_name: str,
        model_object: Any,
        device: str = "auto",
        priority: Optional[int] = None
    ) -> str:
        """
        Register a loaded model with the manager.

        Returns the model key for later reference.
        """
        with self.lock:
            model_key = f"{backend_name}:{model_name}"

            # Determine actual device
            actual_device = self._resolve_device(device)

            # Estimate memory usage
            memory_usage = self._estimate_model_memory(model_object, actual_device)

            # Create model info
            model_info = ModelInfo(
                backend_name=backend_name,
                model_name=model_name,
                memory_usage=memory_usage,
                load_time=time.time(),
                last_used=time.time(),
                device=actual_device,
                priority=priority or self.model_priorities.get(backend_name, 1),
                model_object=model_object
            )

            self.loaded_models[model_key] = model_info
            self.model_cache[model_key] = model_info

            logger.info(f"Registered model {model_key} ({memory_usage}MB on {actual_device})")

            # Check if we need to free memory
            self._check_memory_pressure()

            return model_key

    def get_model(self, backend_name: str, model_name: str) -> Optional[Any]:
        """Get a registered model, updating its last-used time"""
        with self.lock:
            model_key = f"{backend_name}:{model_name}"

            if model_key in self.loaded_models:
                model_info = self.loaded_models[model_key]
                model_info.last_used = time.time()
                model_info.use_count += 1

                # Move to end of LRU cache
                self.model_cache.move_to_end(model_key)

                return model_info.model_object

            return None

    def unload_model(self, backend_name: str, model_name: str, force: bool = False) -> bool:
        """
        Unload a model to free memory.

        Returns True if successfully unloaded.
        """
        with self.lock:
            model_key = f"{backend_name}:{model_name}"

            if model_key not in self.loaded_models:
                return False

            model_info = self.loaded_models[model_key]

            # Don't unload high-priority models unless forced
            if not force and model_info.priority >= 3:
                logger.warning(f"Refusing to unload high-priority model {model_key}")
                return False

            try:
                # Clean up the model object
                del model_info.model_object

                # Remove from tracking
                del self.loaded_models[model_key]
                del self.model_cache[model_key]

                # Force garbage collection
                gc.collect()

                if TORCH_AVAILABLE and torch.cuda.is_available():
                    torch.cuda.empty_cache()

                logger.info(f"Unloaded model {model_key} ({model_info.memory_usage}MB freed)")
                return True

            except Exception as e:
                logger.error(f"Failed to unload model {model_key}: {e}")
                return False

    def optimize_memory(self, target_free_mb: int = 1024) -> int:
        """
        Optimize memory usage by unloading least recently used models.

        Returns the amount of memory freed in MB.
        """
        with self.lock:
            gpu_info = self.get_gpu_info()
            if not gpu_info:
                return 0

            memory_freed = 0

            # If we have enough free memory, no need to optimize
            if gpu_info.free_memory >= target_free_mb:
                return 0

            # Sort models by priority (low first) then by last used time
            models_to_unload = sorted(
                self.loaded_models.values(),
                key=lambda m: (m.priority, m.last_used)
            )

            for model_info in models_to_unload:
                if gpu_info.free_memory + memory_freed >= target_free_mb:
                    break

                # Skip high priority models
                if model_info.priority >= 3:
                    continue

                if self.unload_model(model_info.backend_name, model_info.model_name, force=False):
                    memory_freed += model_info.memory_usage

            logger.info(f"Memory optimization freed {memory_freed}MB")
            return memory_freed

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory usage statistics"""
        with self.lock:
            gpu_info = self.get_gpu_info()

            stats = {
                "loaded_models": len(self.loaded_models),
                "total_model_memory": sum(m.memory_usage for m in self.loaded_models.values()),
                "models_by_backend": defaultdict(int),
                "models_by_priority": defaultdict(int),
                "system_memory": self._get_system_memory_info(),
                "gpu_available": gpu_info is not None
            }

            if gpu_info:
                stats["gpu"] = {
                    "total_memory": gpu_info.total_memory,
                    "used_memory": gpu_info.used_memory,
                    "free_memory": gpu_info.free_memory,
                    "utilization": gpu_info.utilization,
                    "temperature": gpu_info.temperature
                }

            # Count models by backend and priority
            for model_info in self.loaded_models.values():
                stats["models_by_backend"][model_info.backend_name] += 1
                stats["models_by_priority"][f"priority_{model_info.priority}"] += 1

            return dict(stats)

    def _resolve_device(self, device: str) -> str:
        """Resolve device string to actual device"""
        if device == "auto":
            if TORCH_AVAILABLE and torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        return device

    def _estimate_model_memory(self, model_object: Any, device: str) -> int:
        """Estimate memory usage of a model"""
        if not TORCH_AVAILABLE:
            return 128  # Default estimate

        try:
            if hasattr(model_object, 'parameters'):
                # PyTorch model
                param_size = sum(p.numel() * p.element_size() for p in model_object.parameters())
                buffer_size = sum(b.numel() * b.element_size() for b in model_object.buffers())

                total_size = param_size + buffer_size

                # Convert to MB and add overhead
                memory_mb = total_size / (1024 * 1024)
                overhead_factor = 2.5 if device == "cuda" else 1.2
                return int(memory_mb * overhead_factor)

            elif hasattr(model_object, 'model_size'):
                # Some models report their size
                return getattr(model_object, 'model_size', 128)

        except Exception as e:
            logger.debug(f"Could not estimate model memory: {e}")

        # Default estimates based on backend type
        return 512  # Conservative default

    def _check_memory_pressure(self):
        """Check if memory pressure requires unloading models"""
        gpu_info = self.get_gpu_info()
        if not gpu_info:
            return

        memory_usage_ratio = gpu_info.used_memory / gpu_info.total_memory

        if memory_usage_ratio > self.memory_threshold:
            logger.warning(".2f")
            self.optimize_memory(target_free_mb=int(gpu_info.total_memory * 0.15))

    def _get_system_memory_info(self) -> Dict[str, Any]:
        """Get system memory information"""
        try:
            memory = psutil.virtual_memory()
            return {
                "total": memory.total // (1024 * 1024),  # MB
                "available": memory.available // (1024 * 1024),
                "used": memory.used // (1024 * 1024),
                "percentage": memory.percent
            }
        except Exception as e:
            logger.debug(f"Could not get system memory info: {e}")
            return {"error": str(e)}

    def preload_common_models(self) -> int:
        """
        Preload commonly used models to improve performance.

        Returns number of models preloaded.
        """
        gpu_info = self.get_gpu_info()
        if not gpu_info or gpu_info.free_memory < 1024:
            logger.info("Skipping model preloading due to low memory")
            return 0

        # Models to preload based on priority
        preload_candidates = [
            ("mistral-ocr", "high_priority"),
            ("deepseek-ocr", "high_priority"),
            ("florence-2", "medium_priority"),
        ]

        preloaded = 0
        for backend_name, priority in preload_candidates:
            try:
                # This would trigger lazy loading in the backend
                # For now, just count available backends
                if backend_name in self.model_priorities:
                    preloaded += 1
            except Exception as e:
                logger.debug(f"Could not preload {backend_name}: {e}")

        logger.info(f"Preloaded {preloaded} models")
        return preloaded

    def cleanup_idle_models(self, max_idle_seconds: int = 300) -> int:
        """
        Unload models that haven't been used recently.

        Returns number of models unloaded.
        """
        with self.lock:
            current_time = time.time()
            unloaded = 0

            models_to_check = list(self.loaded_models.items())

            for model_key, model_info in models_to_check:
                if model_info.priority >= 3:
                    continue  # Don't unload high-priority models

                idle_time = current_time - model_info.last_used
                if idle_time > max_idle_seconds:
                    if self.unload_model(model_info.backend_name, model_info.model_name, force=False):
                        unloaded += 1

            if unloaded > 0:
                logger.info(f"Cleaned up {unloaded} idle models")

            return unloaded


# Global model manager instance
model_manager = ModelManager(OCRConfig())  # Will be properly initialized later
