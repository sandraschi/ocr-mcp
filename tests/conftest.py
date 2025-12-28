"""
OCR-MCP Test Configuration and Global Fixtures

This module provides comprehensive test configuration and shared fixtures
for the OCR-MCP test suite.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from PIL import Image

# Import OCR-MCP modules
from src.ocr_mcp.core.config import OCRConfig
from src.ocr_mcp.core.backend_manager import BackendManager


# Test Configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def temp_dir():
    """Provide a temporary directory for the test session."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="session")
def test_assets_dir():
    """Provide path to test assets directory."""
    return Path(__file__).parent / "fixtures" / "assets"


@pytest.fixture(scope="session")
def config():
    """Provide OCR configuration for testing."""
    return OCRConfig(
        cache_dir=Path(tempfile.mkdtemp(prefix="ocr_test_")),
        device="cpu",  # Use CPU for consistent testing
        default_backend="got-ocr"
    )


@pytest.fixture(scope="session")
def backend_manager(config):
    """Provide backend manager instance."""
    manager = BackendManager(config)
    yield manager


# Mock Fixtures
@pytest.fixture(scope="session")
def mock_image():
    """Create a mock PIL Image for testing."""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    return img


@pytest.fixture(scope="session")
def sample_image_path(temp_dir, mock_image):
    """Create a sample image file for testing."""
    image_path = temp_dir / "test_image.png"
    mock_image.save(image_path)
    return image_path


@pytest.fixture(scope="session")
def mock_ocr_result():
    """Provide mock OCR result data."""
    return {
        "success": True,
        "text": "This is test OCR text extracted from an image.",
        "confidence": 0.95,
        "backend": "test-backend",
        "processing_time": 0.5,
        "mode": "text"
    }


@pytest.fixture(scope="session")
def mock_scanner_info():
    """Provide mock scanner device information."""
    return {
        "device_id": "wia:test_scanner",
        "name": "Test Scanner",
        "manufacturer": "Test Manufacturer",
        "description": "Mock scanner for testing",
        "device_type": "Flatbed",
        "supports_adf": True,
        "supports_duplex": False,
        "max_dpi": 600
    }


@pytest.fixture(scope="session")
def mock_scan_settings():
    """Provide mock scan settings."""
    return {
        "dpi": 300,
        "color_mode": "Color",
        "paper_size": "A4",
        "brightness": 0,
        "contrast": 0,
        "use_adf": False,
        "duplex": False
    }


# Backend Mocks
@pytest.fixture
def mock_deepseek_backend():
    """Mock DeepSeek-OCR backend."""
    mock_backend = Mock()
    mock_backend.name = "deepseek-ocr"
    mock_backend.is_available.return_value = True
    mock_backend.process_image = Mock(return_value={
        "success": True,
        "text": "DeepSeek OCR result",
        "backend": "deepseek-ocr"
    })
    mock_backend.get_capabilities.return_value = {
        "name": "deepseek-ocr",
        "available": True,
        "modes": ["text", "formatted"],
        "languages": ["en", "multilingual"],
        "gpu_support": False
    }
    return mock_backend


@pytest.fixture
def mock_florence_backend():
    """Mock Florence-2 backend."""
    mock_backend = Mock()
    mock_backend.name = "florence-2"
    mock_backend.is_available.return_value = True
    mock_backend.process_image = Mock(return_value={
        "success": True,
        "text": "Florence-2 OCR result",
        "backend": "florence-2"
    })
    mock_backend.get_capabilities.return_value = {
        "name": "florence-2",
        "available": True,
        "modes": ["text", "formatted", "fine-grained"],
        "languages": ["en", "multilingual"],
        "gpu_support": False
    }
    return mock_backend


@pytest.fixture
def mock_dots_backend():
    """Mock DOTS.OCR backend."""
    mock_backend = Mock()
    mock_backend.name = "dots-ocr"
    mock_backend.is_available.return_value = True
    mock_backend.process_image = Mock(return_value={
        "success": True,
        "text": "DOTS.OCR result with table analysis",
        "layout_analysis": {"tables": 1, "paragraphs": 3},
        "backend": "dots-ocr"
    })
    mock_backend.get_capabilities.return_value = {
        "name": "dots-ocr",
        "available": True,
        "modes": ["text", "formatted"],
        "languages": ["en", "multilingual"],
        "gpu_support": False
    }
    return mock_backend


@pytest.fixture
def mock_ppocr_backend():
    """Mock PP-OCRv5 backend."""
    mock_backend = Mock()
    mock_backend.name = "pp-ocrv5"
    mock_backend.is_available.return_value = True
    mock_backend.process_image = Mock(return_value={
        "success": True,
        "text": "PP-OCRv5 industrial OCR result",
        "backend": "pp-ocrv5"
    })
    mock_backend.get_capabilities.return_value = {
        "name": "pp-ocrv5",
        "available": True,
        "modes": ["text", "formatted"],
        "languages": ["en", "zh", "multilingual"],
        "gpu_support": True
    }
    return mock_backend


@pytest.fixture
def mock_qwen_backend():
    """Mock Qwen-Image-Layered backend."""
    mock_backend = Mock()
    mock_backend.name = "qwen-image-layered"
    mock_backend.is_available.return_value = True
    mock_backend.process_image = Mock(return_value={
        "success": True,
        "text": "Qwen image decomposition result",
        "layers": 4,
        "backend": "qwen-image-layered"
    })
    mock_backend.get_capabilities.return_value = {
        "name": "qwen-image-layered",
        "available": True,
        "modes": ["text", "formatted", "fine-grained"],
        "languages": ["en", "multilingual"],
        "gpu_support": True
    }
    return mock_backend


@pytest.fixture
def mock_got_backend():
    """Mock GOT-OCR2.0 backend."""
    mock_backend = Mock()
    mock_backend.name = "got-ocr"
    mock_backend.is_available.return_value = True
    mock_backend.process_image = Mock(return_value={
        "success": True,
        "text": "GOT-OCR2.0 advanced result",
        "backend": "got-ocr"
    })
    mock_backend.get_capabilities.return_value = {
        "name": "got-ocr",
        "available": True,
        "modes": ["text", "formatted", "fine-grained"],
        "languages": ["en", "multilingual"],
        "gpu_support": True
    }
    return mock_backend


@pytest.fixture
def mock_tesseract_backend():
    """Mock Tesseract backend."""
    mock_backend = Mock()
    mock_backend.name = "tesseract"
    mock_backend.is_available.return_value = True
    mock_backend.process_image = Mock(return_value={
        "success": True,
        "text": "Tesseract OCR result",
        "backend": "tesseract"
    })
    mock_backend.get_capabilities.return_value = {
        "name": "tesseract",
        "available": True,
        "modes": ["text"],
        "languages": ["en", "multilingual"],
        "gpu_support": False
    }
    return mock_backend


@pytest.fixture
def mock_easyocr_backend():
    """Mock EasyOCR backend."""
    mock_backend = Mock()
    mock_backend.name = "easyocr"
    mock_backend.is_available.return_value = True
    mock_backend.process_image = Mock(return_value={
        "success": True,
        "text": "EasyOCR result",
        "backend": "easyocr"
    })
    mock_backend.get_capabilities.return_value = {
        "name": "easyocr",
        "available": True,
        "modes": ["text", "formatted"],
        "languages": ["en", "ch_sim", "ch_tra"],
        "gpu_support": True
    }
    return mock_backend


# Scanner Mocks
@pytest.fixture
def mock_wia_backend():
    """Mock WIA scanner backend."""
    mock_scanner = Mock()
    mock_scanner.is_available.return_value = True
    mock_scanner.discover_scanners.return_value = [
        {
            "device_id": "wia:test_scanner_1",
            "name": "Test Scanner 1",
            "manufacturer": "Test Corp",
            "device_type": "Flatbed",
            "supports_adf": True,
            "max_dpi": 600
        },
        {
            "device_id": "wia:test_scanner_2",
            "name": "Test Scanner 2",
            "manufacturer": "Another Corp",
            "device_type": "Feeder",
            "supports_adf": False,
            "max_dpi": 300
        }
    ]
    mock_scanner.get_scanner_properties.return_value = {
        "supported_resolutions": [75, 150, 200, 300, 600],
        "supported_color_modes": ["Color", "Grayscale", "BlackWhite"],
        "supported_paper_sizes": ["A4", "Letter", "Legal"],
        "max_paper_width": 5100,
        "max_paper_height": 6600,
        "supports_adf": True,
        "supports_duplex": False,
        "supports_preview": True,
        "manufacturer": "Test Corp",
        "model": "Test Scanner",
        "firmware_version": "1.0.0"
    }
    mock_scanner.configure_scan.return_value = True
    mock_scanner.scan_document.return_value = Image.new('RGB', (1000, 1500), color='white')
    return mock_scanner


@pytest.fixture
def mock_scanner_manager(mock_wia_backend):
    """Mock scanner manager."""
    mock_manager = Mock()
    mock_manager.is_available.return_value = True
    mock_manager.discover_scanners.return_value = mock_wia_backend.discover_scanners()
    mock_manager.get_scanner_info.return_value = mock_wia_backend.discover_scanners()[0]
    mock_manager.get_scanner_properties.return_value = mock_wia_backend.get_scanner_properties()
    mock_manager.configure_scan.return_value = True
    mock_manager.scan_document.return_value = mock_wia_backend.scan_document()
    mock_manager.get_available_backends.return_value = ["wia"]
    return mock_manager


# Document Processor Mocks
@pytest.fixture
def mock_document_processor():
    """Mock document processor."""
    mock_processor = Mock()
    mock_processor.is_available.return_value = True
    mock_processor.detect_file_type.return_value = "pdf"
    mock_processor.extract_images.return_value = [
        {
            "image_path": "/tmp/test_page_0.png",
            "page_number": 0,
            "metadata": {
                "width": 1000,
                "height": 1500,
                "dpi": 300,
                "format": "PNG",
                "source_type": "pdf",
                "total_pages": 1
            }
        }
    ]
    mock_processor.cleanup_temp_files.return_value = None
    return mock_processor


# FastMCP Server Mock
@pytest.fixture
def mock_fastmcp_app():
    """Mock FastMCP application for testing."""
    mock_app = Mock()
    mock_app.tool = Mock(return_value=lambda func: func)  # Decorator that returns function unchanged
    mock_app.get_tools = Mock(return_value=[])
    return mock_app


# Test Data Fixtures
@pytest.fixture(params=[
    "text", "formatted", "fine-grained"
])
def ocr_mode(request):
    """Parametrize OCR processing modes."""
    return request.param


@pytest.fixture(params=[
    "auto", "deepseek-ocr", "florence-2", "dots-ocr", "pp-ocrv5", "qwen-image-layered", "got-ocr", "tesseract", "easyocr"
])
def ocr_backend_name(request):
    """Parametrize OCR backend names."""
    return request.param


@pytest.fixture(params=[
    "png", "jpg", "tiff", "bmp"
])
def image_format(request):
    """Parametrize image formats."""
    return request.param


@pytest.fixture(params=[
    "pdf", "cbz", "cbr", "image"
])
def document_type(request):
    """Parametrize document types."""
    return request.param


@pytest.fixture(params=[
    "text", "html", "json", "markdown", "xml"
])
def output_format(request):
    """Parametrize output formats."""
    return request.param


# Environment Fixtures
@pytest.fixture
def clean_env():
    """Ensure clean environment for testing."""
    # Store original environment
    original_env = dict(os.environ)

    # Clear OCR-MCP related environment variables
    ocr_env_vars = [
        'OCR_CACHE_DIR',
        'OCR_DEVICE',
        'OCR_DEFAULT_BACKEND',
        'OCR_MAX_CONCURRENT',
        'OCR_MODEL_CACHE_SIZE'
    ]

    for var in ocr_env_vars:
        os.environ.pop(var, None)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Async Test Utilities
@pytest.fixture
async def async_cleanup():
    """Provide async cleanup context."""
    cleanup_tasks = []

    def add_cleanup_task(task):
        cleanup_tasks.append(task)

    yield add_cleanup_task

    # Run cleanup tasks
    for task in cleanup_tasks:
        try:
            if asyncio.iscoroutinefunction(task):
                await task()
            else:
                task()
        except Exception as e:
            print(f"Cleanup task failed: {e}")


# Performance Testing Fixtures
@pytest.fixture
def benchmark_config():
    """Configuration for benchmark tests."""
    return {
        "warmup_iterations": 3,
        "benchmark_iterations": 10,
        "max_time": 60,  # seconds
        "min_rounds": 5,
        "timeout": 300  # seconds
    }


# Test Asset Creation
@pytest.fixture(scope="session")
def create_test_image(temp_dir):
    """Factory fixture for creating test images."""
    def _create_image(width=100, height=100, color='white', format='PNG'):
        img = Image.new('RGB', (width, height), color=color)
        return img
    return _create_image


@pytest.fixture(scope="session")
def create_test_pdf(temp_dir):
    """Factory fixture for creating test PDF files."""
    def _create_pdf(pages=1, content="Test PDF content"):
        # This would require a PDF library like reportlab
        # For now, return a mock path
        pdf_path = temp_dir / f"test_{pages}page.pdf"
        # In real implementation, create actual PDF
        pdf_path.write_text(f"Mock PDF with {pages} pages: {content}")
        return pdf_path
    return _create_pdf


@pytest.fixture(scope="session")
def create_test_cbz(temp_dir, create_test_image):
    """Factory fixture for creating test CBZ files."""
    def _create_cbz(pages=3):
        cbz_path = temp_dir / f"test_{pages}page.cbz"
        # In real implementation, create actual CBZ archive
        cbz_path.write_text(f"Mock CBZ with {pages} pages")
        return cbz_path
    return _create_cbz


# Error Testing Fixtures
@pytest.fixture(params=[
    "FileNotFoundError",
    "PermissionError",
    "OSError",
    "ValueError",
    "RuntimeError"
])
def expected_exception(request):
    """Parametrize expected exceptions for error testing."""
    return request.param


@pytest.fixture
def exception_context():
    """Provide context for testing exception handling."""
    return {
        "raised": False,
        "exception_type": None,
        "exception_message": None,
        "context": {}
    }


# Integration Test Fixtures
@pytest.fixture
def integration_config():
    """Configuration for integration tests."""
    return {
        "timeout": 30,  # seconds
        "retry_attempts": 3,
        "retry_delay": 1,  # seconds
        "cleanup_temp_files": True,
        "validate_results": True
    }


# E2E Test Fixtures
@pytest.fixture
def e2e_config():
    """Configuration for end-to-end tests."""
    return {
        "server_startup_timeout": 10,  # seconds
        "tool_execution_timeout": 30,  # seconds
        "cleanup_timeout": 5,  # seconds
        "validate_outputs": True,
        "check_performance": False
    }






