"""
OCR-MCP Test Mocks

Comprehensive mock implementations for external dependencies and hardware interfaces.
"""

from .mock_backends import *
from .mock_document_processor import *
from .mock_scanner import *

__all__ = [
    "MockDOTSBackend",
    "MockDeepSeekBackend",
    "MockDocumentProcessor",
    "MockEasyOCRBackend",
    "MockFlorenceBackend",
    "MockGOTBackend",
    "MockPPOCRBackend",
    "MockQwenBackend",
    "MockScannerManager",
    "MockTesseractBackend",
    "MockWIABackend",
    "create_mock_image",
    "create_mock_ocr_result",
    "create_mock_scanner_info",
]
