"""
OCR-MCP Test Mocks

Comprehensive mock implementations for external dependencies and hardware interfaces.
"""

from .mock_backends import *
from .mock_scanner import *
from .mock_document_processor import *

__all__ = [
    # Backend mocks
    "MockDeepSeekBackend",
    "MockFlorenceBackend",
    "MockDOTSBackend",
    "MockPPOCRBackend",
    "MockQwenBackend",
    "MockGOTBackend",
    "MockTesseractBackend",
    "MockEasyOCRBackend",

    # Scanner mocks
    "MockWIABackend",
    "MockScannerManager",

    # Document processor mocks
    "MockDocumentProcessor",

    # Utility mocks
    "create_mock_image",
    "create_mock_ocr_result",
    "create_mock_scanner_info"
]






