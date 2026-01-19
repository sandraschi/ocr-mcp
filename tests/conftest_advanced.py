"""
Advanced OCR-MCP Test Configuration

Extends the base conftest.py with advanced testing utilities,
performance monitoring, and comprehensive test scenarios.
"""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.ocr_mcp.core.backend_manager import BackendManager
from src.ocr_mcp.core.config import OCRConfig

# Import our enhanced test utilities
from .utils.test_helpers import (
    AsyncTestHelper,
    MockBackendFactory,
    MockServerManager,
    PerformanceProfiler,
    TestDataGenerator,
    TestDataValidator,
    TestFileManager,
)

# ===== ADVANCED FIXTURES =====


@pytest.fixture(scope="session")
def advanced_config() -> OCRConfig:
    """Advanced OCR configuration for comprehensive testing."""
    return OCRConfig(
        cache_dir=Path(tempfile.mkdtemp(prefix="ocr_advanced_test_")),
        device="cpu",  # Use CPU for consistent testing across environments
        default_backend="auto",
        batch_size=8,
        max_concurrent_jobs=4,
        got_ocr_model_size="base",
        tesseract_languages="eng+fra+deu",
    )


@pytest.fixture(scope="session")
def backend_manager_with_mocks(advanced_config) -> BackendManager:
    """Backend manager with comprehensive mock backends."""
    manager = BackendManager(advanced_config)

    # Replace real backends with mocks for consistent testing
    mock_backends = MockBackendFactory.create_backend_suite()
    manager.backends = mock_backends

    # Make some backends available, others unavailable for testing
    available_backends = ["deepseek-ocr", "florence-2", "tesseract"]
    for name, backend in manager.backends.items():
        backend.is_available.return_value = name in available_backends

    return manager


@pytest.fixture
def performance_monitor() -> PerformanceProfiler:
    """Performance monitoring fixture."""
    return PerformanceProfiler()


@pytest.fixture(scope="function")
def file_manager() -> Generator[TestFileManager, None, None]:
    """File manager with automatic cleanup."""
    manager = TestFileManager()
    yield manager
    manager.cleanup()


@pytest.fixture
def async_test_helper() -> AsyncTestHelper:
    """Async testing utilities."""
    return AsyncTestHelper()


@pytest.fixture
def data_validator() -> TestDataValidator:
    """Data validation utilities."""
    return TestDataValidator()


# ===== TEST SCENARIO FIXTURES =====


@pytest.fixture
def realistic_document_scenarios():
    """Realistic document testing scenarios."""
    return {
        "invoice": {
            "text": """
            ACME CORPORATION INVOICE
            Invoice #: INV-2025-0456
            Date: January 18, 2026
            Bill To: Tech Solutions Inc.
            123 Business Ave, Suite 100
            New York, NY 10001

            Description              Qty   Unit Price   Total
            Professional Services    40    $125.00      $5,000.00
            Software License         5     $299.00      $1,495.00
            Training Session         2     $750.00      $1,500.00

            Subtotal: $8,995.00
            Tax (8.5%): $764.58
            Total Due: $9,759.58

            Payment due within 30 days.
            """,
            "expected_elements": ["invoice", "table", "totals", "dates"],
            "complexity": "medium",
        },
        "receipt": {
            "text": """
            STARBUCKS COFFEE
            123 Main Street
            New York, NY 10001
            (212) 555-0123

            Date: Jan 18, 2026  2:34 PM
            Transaction: #987654321

            Item                 Qty  Price
            Latte (Grande)       2   $8.50
            Blueberry Muffin     1   $3.75
            Tax (8.875%)           $1.08
            Total                  $13.33

            Thank you for visiting Starbucks!
            """,
            "expected_elements": ["receipt", "items", "prices", "transaction_id"],
            "complexity": "low",
        },
        "contract": {
            "text": """
            SERVICE AGREEMENT CONTRACT

            This Service Agreement ("Agreement") is entered into as of January 18, 2026,
            by and between TechCorp Solutions LLC ("Provider") and DataSys Inc. ("Client").

            1. SERVICES
            Provider agrees to provide the following services to Client:
            - Software development and maintenance
            - Technical support and consulting
            - System integration services

            2. COMPENSATION
            Client shall pay Provider the sum of Fifty Thousand Dollars ($50,000.00)
            for the services rendered pursuant to this Agreement.

            3. TERM
            This Agreement shall commence on the date first written above and
            shall continue for a period of twelve (12) months thereafter.

            IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first above written.

            TechCorp Solutions LLC              DataSys Inc.
            _______________________________     _______________________________
            By: John Smith                      By: Jane Doe
            Title: CEO                          Title: CTO
            """,
            "expected_elements": ["contract", "legal_language", "signatures", "dates"],
            "complexity": "high",
        },
    }


@pytest.fixture
def image_quality_scenarios():
    """Different image quality scenarios for testing."""
    return {
        "perfect": {
            "description": "High-quality scanned document",
            "quality_score": 0.95,
            "issues": [],
            "expected_ocr_success": True,
        },
        "good": {
            "description": "Good quality with minor artifacts",
            "quality_score": 0.85,
            "issues": ["minor_noise"],
            "expected_ocr_success": True,
        },
        "fair": {
            "description": "Fair quality with some degradation",
            "quality_score": 0.70,
            "issues": ["blur", "contrast_issues"],
            "expected_ocr_success": True,
        },
        "poor": {
            "description": "Poor quality document",
            "quality_score": 0.45,
            "issues": ["heavy_noise", "blur", "low_contrast", "skew"],
            "expected_ocr_success": False,
        },
        "terrible": {
            "description": "Very poor quality, barely readable",
            "quality_score": 0.20,
            "issues": ["extreme_noise", "severe_blur", "very_low_contrast", "heavy_skew"],
            "expected_ocr_success": False,
        },
    }


@pytest.fixture
def backend_comparison_matrix():
    """Matrix of backend comparisons for different document types."""
    return {
        "clean_text": {
            "expected_best": ["deepseek-ocr", "florence-2"],
            "expected_worst": ["tesseract"],
            "min_accuracy": 0.90,
        },
        "handwriting": {
            "expected_best": ["florence-2", "deepseek-ocr"],
            "expected_worst": ["tesseract"],
            "min_accuracy": 0.60,
        },
        "tables": {
            "expected_best": ["dots-ocr", "florence-2"],
            "expected_worst": ["tesseract"],
            "min_accuracy": 0.75,
        },
        "mixed_content": {
            "expected_best": ["deepseek-ocr", "florence-2"],
            "expected_worst": ["tesseract"],
            "min_accuracy": 0.80,
        },
        "low_quality": {
            "expected_best": ["florence-2", "deepseek-ocr"],
            "expected_worst": ["tesseract"],
            "min_accuracy": 0.50,
        },
    }


# ===== PERFORMANCE TESTING FIXTURES =====


@pytest.fixture
def performance_test_config():
    """Configuration for performance testing."""
    return {
        "warmup_iterations": 5,
        "benchmark_iterations": 20,
        "max_execution_time": 300,  # 5 minutes
        "memory_threshold_mb": 1024,
        "cpu_threshold_percent": 80,
        "acceptable_latency_ms": 5000,  # 5 seconds
        "throughput_target": 10,  # documents per minute
    }


@pytest.fixture
def load_test_scenarios():
    """Scenarios for load testing."""
    return {
        "light": {
            "concurrent_users": 2,
            "documents_per_user": 5,
            "total_documents": 10,
            "expected_completion_time": 30,  # seconds
        },
        "medium": {
            "concurrent_users": 5,
            "documents_per_user": 10,
            "total_documents": 50,
            "expected_completion_time": 120,  # seconds
        },
        "heavy": {
            "concurrent_users": 10,
            "documents_per_user": 20,
            "total_documents": 200,
            "expected_completion_time": 600,  # seconds
        },
        "extreme": {
            "concurrent_users": 20,
            "documents_per_user": 50,
            "total_documents": 1000,
            "expected_completion_time": 1800,  # seconds
        },
    }


# ===== SECURITY TESTING FIXTURES =====


@pytest.fixture
def security_test_cases():
    """Security test cases for input validation."""
    return {
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\sam",
        ],
        "command_injection": ["; rm -rf /", "&& del /F /Q C:\\*", "| cat /etc/passwd", "`whoami`"],
        "large_files": [
            {"size": 100 * 1024 * 1024},  # 100MB
            {"size": 1024 * 1024 * 1024},  # 1GB
            {"size": 10 * 1024 * 1024 * 1024},  # 10GB
        ],
        "malformed_files": [
            b"",  # Empty file
            b"not_an_image",  # Invalid image
            b"%PDF-1.4\n%invalid_pdf_content",  # Corrupted PDF
        ],
        "special_characters": [
            "file_with_特殊字符.jpg",
            "file with spaces.png",
            "file-with-dashes.pdf",
            "file.with.many.dots.txt",
        ],
    }


# ===== FUZZING AND PROPERTY TESTING FIXTURES =====


@pytest.fixture
def fuzzing_inputs():
    """Inputs for fuzzing tests."""
    return {
        "text_lengths": [0, 1, 10, 100, 1000, 10000, 100000],
        "image_sizes": [(1, 1), (10, 10), (100, 100), (1000, 1000), (10000, 10000)],
        "file_formats": ["png", "jpg", "jpeg", "tiff", "bmp", "gif", "webp"],
        "encodings": ["utf-8", "utf-16", "ascii", "latin-1", "cp1252"],
        "special_strings": [
            "",
            "\x00",
            "\n",
            "\r\n",
            "\t",
            "<script>",
            "<?php",
            "<!--",
            "🚀🔥💯",
            "αβγδε",
            "中文",
            "русский",
        ],
    }


# ===== MOCKING FIXTURES =====


@pytest.fixture
def mock_external_services():
    """Mock external services (APIs, databases, etc.)."""
    with (
        patch("requests.get") as mock_get,
        patch("requests.post") as mock_post,
        patch("httpx.AsyncClient") as mock_client,
    ):
        # Configure mock responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "ok"}

        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"id": "123", "status": "created"}

        mock_client.return_value.__aenter__.return_value.get.return_value.status_code = 200
        mock_client.return_value.__aenter__.return_value.get.return_value.json.return_value = {
            "data": "mock"
        }

        yield {"get": mock_get, "post": mock_post, "client": mock_client}


@pytest.fixture
def mock_file_operations():
    """Mock file system operations."""
    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("pathlib.Path.is_file") as mock_is_file,
        patch("pathlib.Path.read_bytes") as mock_read_bytes,
        patch("pathlib.Path.write_bytes") as mock_write_bytes,
        patch("builtins.open") as mock_open,
    ):
        # Configure defaults
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_read_bytes.return_value = b"mock file content"
        mock_write_bytes.return_value = None

        mock_file = Mock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = None
        mock_file.read.return_value = "mock text content"
        mock_file.write.return_value = None
        mock_open.return_value = mock_file

        yield {
            "exists": mock_exists,
            "is_file": mock_is_file,
            "read_bytes": mock_read_bytes,
            "write_bytes": mock_write_bytes,
            "open": mock_open,
        }


# ===== INTEGRATION TESTING FIXTURES =====


@pytest.fixture(scope="session")
def mock_server():
    """Mock OCR-MCP server for integration tests."""
    server = MockServerManager()
    # In a real scenario, would start actual server
    return server


@pytest.fixture
def integration_test_config():
    """Configuration for integration tests."""
    return {
        "server_url": "http://localhost:15550",
        "timeout": 30,
        "retry_attempts": 3,
        "validate_responses": True,
        "check_performance": True,
        "cleanup_after_test": True,
    }


# ===== END-TO-END TESTING FIXTURES =====


@pytest.fixture
def e2e_test_flows():
    """End-to-end test flows."""
    return {
        "single_document_ocr": {
            "steps": [
                "upload_document",
                "select_backend",
                "process_ocr",
                "view_results",
                "export_results",
            ],
            "expected_outcomes": [
                "document_uploaded",
                "backend_selected",
                "ocr_completed",
                "results_displayed",
                "export_successful",
            ],
        },
        "batch_processing": {
            "steps": [
                "upload_multiple_documents",
                "configure_batch_settings",
                "start_batch_processing",
                "monitor_progress",
                "review_batch_results",
                "bulk_export",
            ],
            "expected_outcomes": [
                "all_documents_uploaded",
                "batch_configured",
                "processing_started",
                "progress_visible",
                "results_available",
                "bulk_export_completed",
            ],
        },
        "quality_assessment_workflow": {
            "steps": [
                "upload_document",
                "run_quality_analysis",
                "review_quality_metrics",
                "apply_recommendations",
                "reprocess_if_needed",
                "compare_results",
            ],
            "expected_outcomes": [
                "quality_analyzed",
                "metrics_displayed",
                "recommendations_provided",
                "improvements_applied",
                "results_compared",
            ],
        },
    }


# ===== UTILITY FIXTURES =====


@pytest.fixture
def test_context():
    """Comprehensive test context with all utilities."""
    return {
        "data_generator": TestDataGenerator(),
        "profiler": PerformanceProfiler(),
        "file_manager": TestFileManager(),
        "async_helper": AsyncTestHelper(),
        "validator": TestDataValidator(),
        "server_manager": MockServerManager(),
    }


@pytest.fixture
def parametrized_test_data(request):
    """Parametrized test data based on test parameters."""
    # This fixture can be used to provide different test data
    # based on pytest parametrization
    return getattr(request, "param", {})


# ===== ENVIRONMENT SETUP =====


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables and cleanup."""
    # Store original environment
    original_env = dict(os.environ)

    # Set test-specific environment variables
    os.environ.update(
        {
            "OCR_TESTING": "true",
            "OCR_DISABLE_GPU": "true",
            "OCR_CACHE_DIR": tempfile.mkdtemp(prefix="ocr_test_env_"),
            "OCR_LOG_LEVEL": "WARNING",  # Reduce log noise during tests
        }
    )

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def cleanup_test_artifacts():
    """Clean up test artifacts after each test."""
    yield

    # Clean up any temporary files created during test
    # This is a basic implementation - could be enhanced
    pass


# ===== MARKERS =====


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")
    config.addinivalue_line("markers", "fuzzing: marks tests as fuzzing tests")
    config.addinivalue_line("markers", "property: marks tests as property-based tests")


# ===== HOOKS =====


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture test results and add custom reporting."""
    outcome = yield
    report = outcome.get_result()

    # Add custom metadata to test reports
    if hasattr(item, "funcargs"):
        # Capture fixture values for debugging
        report.user_properties = getattr(report, "user_properties", [])
        report.user_properties.append(("fixtures", list(item.funcargs.keys())))

    # Log performance metrics if available
    if "performance_monitor" in item.funcargs:
        profiler = item.funcargs["performance_monitor"]
        stats = profiler.get_stats()
        if stats:
            report.user_properties.append(("performance_stats", stats))


@pytest.fixture
def capture_logs(caplog):
    """Enhanced log capture fixture."""
    # Set log level for more detailed capture
    caplog.set_level(10)  # DEBUG level
    return caplog
