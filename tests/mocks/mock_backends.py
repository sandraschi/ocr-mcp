"""
Mock OCR Backend Implementations

Comprehensive mock implementations for all OCR backends to enable
testing without requiring actual model downloads or GPU resources.
"""

import asyncio
from typing import Dict, Any

from src.ocr_mcp.core.backend_manager import OCRBackend
from src.ocr_mcp.core.config import OCRConfig


class MockDeepSeekBackend(OCRBackend):
    """Mock DeepSeek-OCR backend for testing."""

    def __init__(self, config: OCRConfig):
        super().__init__("deepseek-ocr", config)
        self._available = True
        self.call_count = 0
        self.last_call_args = None

    def is_available(self) -> bool:
        return self._available

    async def process_image(self, image_path: str, mode: str = "text", **kwargs) -> Dict[str, Any]:
        self.call_count += 1
        self.last_call_args = (image_path, mode, kwargs)

        # Simulate processing delay
        await asyncio.sleep(0.1)

        result = {
            "success": True,
            "text": f"DeepSeek OCR result for {image_path} in {mode} mode",
            "confidence": 0.95,
            "backend": "deepseek-ocr",
            "processing_time": 0.1,
            "mode": mode,
            "gpu_used": False
        }

        # Add mode-specific features
        if mode == "formatted":
            result["layout_analysis"] = {
                "paragraphs": 3,
                "lines": 12,
                "words": 45
            }
        elif mode == "fine-grained":
            result["regions"] = [
                {"text": "Header text", "bbox": [10, 10, 200, 50]},
                {"text": "Body content", "bbox": [10, 60, 400, 200]}
            ]

        return result

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name": "deepseek-ocr",
            "available": True,
            "modes": ["text", "formatted", "fine-grained"],
            "languages": ["en", "multilingual"],
            "gpu_support": False,
            "description": "Vision-language OCR with advanced text understanding"
        }


class MockFlorenceBackend(OCRBackend):
    """Mock Florence-2 backend for testing."""

    def __init__(self, config: OCRConfig):
        super().__init__("florence-2", config)
        self._available = True
        self.call_count = 0

    def is_available(self) -> bool:
        return self._available

    async def process_image(self, image_path: str, mode: str = "text", **kwargs) -> Dict[str, Any]:
        self.call_count += 1
        await asyncio.sleep(0.15)

        result = {
            "success": True,
            "text": f"Florence-2 OCR result for {image_path}",
            "confidence": 0.92,
            "backend": "florence-2",
            "processing_time": 0.15,
            "mode": mode,
            "gpu_used": False
        }

        # Florence-2 specific features
        if "region" in kwargs:
            result["region_ocr"] = True
            result["region_coords"] = kwargs["region"]

        return result

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name": "florence-2",
            "available": True,
            "modes": ["text", "formatted", "fine-grained"],
            "languages": ["en", "multilingual"],
            "gpu_support": False,
            "description": "Microsoft's Vision Foundation Model for various vision tasks"
        }


class MockDOTSBackend(OCRBackend):
    """Mock DOTS.OCR backend for testing."""

    def __init__(self, config: OCRConfig):
        super().__init__("dots-ocr", config)
        self._available = True
        self.call_count = 0

    def is_available(self) -> bool:
        return self._available

    async def process_image(self, image_path: str, mode: str = "text", **kwargs) -> Dict[str, Any]:
        self.call_count += 1
        await asyncio.sleep(0.12)

        result = {
            "success": True,
            "text": f"DOTS.OCR result with document structure analysis for {image_path}",
            "confidence": 0.94,
            "backend": "dots-ocr",
            "processing_time": 0.12,
            "mode": mode,
            "gpu_used": False,
            "layout_analysis": {
                "tables": 2,
                "paragraphs": 5,
                "headings": 3,
                "lists": 1
            },
            "table_data": [
                {"rows": 3, "cols": 4, "content": "Sample table data"}
            ]
        }

        return result

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name": "dots-ocr",
            "available": True,
            "modes": ["text", "formatted"],
            "languages": ["en", "multilingual"],
            "gpu_support": False,
            "description": "Document understanding specialist for layout analysis"
        }


class MockPPOCRBackend(OCRBackend):
    """Mock PP-OCRv5 backend for testing."""

    def __init__(self, config: OCRConfig):
        super().__init__("pp-ocrv5", config)
        self._available = True
        self.call_count = 0

    def is_available(self) -> bool:
        return self._available

    async def process_image(self, image_path: str, mode: str = "text", **kwargs) -> Dict[str, Any]:
        self.call_count += 1
        await asyncio.sleep(0.08)  # Fast industrial processing

        result = {
            "success": True,
            "text": f"PP-OCRv5 industrial OCR result for {image_path}",
            "confidence": 0.96,
            "backend": "pp-ocrv5",
            "processing_time": 0.08,
            "mode": mode,
            "gpu_used": True,  # Industrial version supports GPU
            "industrial_metrics": {
                "inference_speed": "45 FPS",
                "accuracy": "96.2%",
                "edge_deployment": True
            }
        }

        return result

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name": "pp-ocrv5",
            "available": True,
            "modes": ["text", "formatted"],
            "languages": ["en", "zh", "multilingual"],
            "gpu_support": True,
            "description": "Industrial-grade PaddlePaddle OCR system"
        }


class MockQwenBackend(OCRBackend):
    """Mock Qwen-Image-Layered backend for testing."""

    def __init__(self, config: OCRConfig):
        super().__init__("qwen-image-layered", config)
        self._available = True
        self.call_count = 0

    def is_available(self) -> bool:
        return self._available

    async def process_image(self, image_path: str, mode: str = "text", **kwargs) -> Dict[str, Any]:
        self.call_count += 1
        await asyncio.sleep(0.2)

        result = {
            "success": True,
            "text": f"Qwen-Image-Layered decomposition result for {image_path}",
            "confidence": 0.93,
            "backend": "qwen-image-layered",
            "processing_time": 0.2,
            "mode": mode,
            "gpu_used": True,
            "layers": {
                "count": 4,
                "types": ["background", "text", "graphics", "foreground"],
                "editability_score": 0.89
            },
            "decomposition": {
                "rgba_layers": 4,
                "semantic_separation": True,
                "independent_manipulation": True
            }
        }

        return result

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name": "qwen-image-layered",
            "available": True,
            "modes": ["text", "formatted", "fine-grained"],
            "languages": ["en", "multilingual"],
            "gpu_support": True,
            "description": "Image decomposition model for layered editing"
        }


class MockGOTBackend(OCRBackend):
    """Mock GOT-OCR2.0 backend for testing."""

    def __init__(self, config: OCRConfig):
        super().__init__("got-ocr", config)
        self._available = True
        self.call_count = 0

    def is_available(self) -> bool:
        return self._available

    async def process_image(self, image_path: str, mode: str = "text", **kwargs) -> Dict[str, Any]:
        self.call_count += 1
        await asyncio.sleep(0.18)

        result = {
            "success": True,
            "text": f"GOT-OCR2.0 advanced OCR result for {image_path}",
            "confidence": 0.97,
            "backend": "got-ocr",
            "processing_time": 0.18,
            "mode": mode,
            "gpu_used": True,
            "advanced_features": {
                "multi_modal": True,
                "layout_understanding": True,
                "text_line_detection": True
            }
        }

        # GOT-specific features
        if kwargs.get("comic_mode"):
            result["comic_analysis"] = {
                "panels_detected": 4,
                "speech_bubbles": 3,
                "reading_order": [0, 1, 2, 3]
            }

        return result

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name": "got-ocr",
            "available": True,
            "modes": ["text", "formatted", "fine-grained"],
            "languages": ["en", "multilingual"],
            "gpu_support": True,
            "description": "General OCR Theory implementation with advanced features"
        }


class MockTesseractBackend(OCRBackend):
    """Mock Tesseract backend for testing."""

    def __init__(self, config: OCRConfig):
        super().__init__("tesseract", config)
        self._available = True
        self.call_count = 0

    def is_available(self) -> bool:
        return self._available

    async def process_image(self, image_path: str, mode: str = "text", **kwargs) -> Dict[str, Any]:
        self.call_count += 1
        await asyncio.sleep(0.05)  # Fast traditional OCR

        result = {
            "success": True,
            "text": f"Tesseract OCR result for {image_path}",
            "confidence": 0.85,
            "backend": "tesseract",
            "processing_time": 0.05,
            "mode": mode,
            "gpu_used": False,
            "tesseract_version": "5.3.0"
        }

        return result

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name": "tesseract",
            "available": True,
            "modes": ["text"],
            "languages": ["en", "multilingual"],
            "gpu_support": False,
            "description": "Traditional Tesseract OCR engine"
        }


class MockEasyOCRBackend(OCRBackend):
    """Mock EasyOCR backend for testing."""

    def __init__(self, config: OCRConfig):
        super().__init__("easyocr", config)
        self._available = True
        self.call_count = 0

    def is_available(self) -> bool:
        return self._available

    async def process_image(self, image_path: str, mode: str = "text", **kwargs) -> Dict[str, Any]:
        self.call_count += 1
        await asyncio.sleep(0.1)

        result = {
            "success": True,
            "text": f"EasyOCR result for {image_path}",
            "confidence": 0.88,
            "backend": "easyocr",
            "processing_time": 0.1,
            "mode": mode,
            "gpu_used": True,
            "detection_boxes": [
                [[10, 10], [100, 10], [100, 30], [10, 30]],
                [[10, 40], [150, 40], [150, 60], [10, 60]]
            ]
        }

        return result

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name": "easyocr",
            "available": True,
            "modes": ["text", "formatted"],
            "languages": ["en", "ch_sim", "ch_tra"],
            "gpu_support": True,
            "description": "EasyOCR with bounding box detection"
        }


# Factory functions for creating mock backends
def create_mock_deepseek_backend(config: OCRConfig) -> MockDeepSeekBackend:
    """Factory for DeepSeek backend mock."""
    return MockDeepSeekBackend(config)


def create_mock_florence_backend(config: OCRConfig) -> MockFlorenceBackend:
    """Factory for Florence-2 backend mock."""
    return MockFlorenceBackend(config)


def create_mock_dots_backend(config: OCRConfig) -> MockDOTSBackend:
    """Factory for DOTS.OCR backend mock."""
    return MockDOTSBackend(config)


def create_mock_ppocr_backend(config: OCRConfig) -> MockPPOCRBackend:
    """Factory for PP-OCRv5 backend mock."""
    return MockPPOCRBackend(config)


def create_mock_qwen_backend(config: OCRConfig) -> MockQwenBackend:
    """Factory for Qwen-Image-Layered backend mock."""
    return MockQwenBackend(config)


def create_mock_got_backend(config: OCRConfig) -> MockGOTBackend:
    """Factory for GOT-OCR2.0 backend mock."""
    return MockGOTBackend(config)


def create_mock_tesseract_backend(config: OCRConfig) -> MockTesseractBackend:
    """Factory for Tesseract backend mock."""
    return MockTesseractBackend(config)


def create_mock_easyocr_backend(config: OCRConfig) -> MockEasyOCRBackend:
    """Factory for EasyOCR backend mock."""
    return MockEasyOCRBackend(config)


# Utility functions for testing
def create_mock_image(width: int = 100, height: int = 100, color: str = 'white') -> Any:
    """Create a mock PIL Image for testing."""
    from PIL import Image
    return Image.new('RGB', (width, height), color=color)


def create_mock_ocr_result(
    success: bool = True,
    text: str = "Mock OCR text",
    backend: str = "test-backend",
    confidence: float = 0.9
) -> Dict[str, Any]:
    """Create a mock OCR result for testing."""
    return {
        "success": success,
        "text": text,
        "confidence": confidence,
        "backend": backend,
        "processing_time": 0.1,
        "mode": "text"
    }


def create_mock_scanner_info(
    device_id: str = "wia:test_scanner",
    name: str = "Test Scanner"
) -> Dict[str, Any]:
    """Create mock scanner information for testing."""
    return {
        "device_id": device_id,
        "name": name,
        "manufacturer": "Test Manufacturer",
        "description": f"Mock scanner: {name}",
        "device_type": "Flatbed",
        "supports_adf": True,
        "supports_duplex": False,
        "max_dpi": 600
    }






