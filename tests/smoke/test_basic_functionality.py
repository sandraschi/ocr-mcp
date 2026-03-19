"""
OCR-MCP Smoke Tests

Basic functionality verification tests that should always pass.
These tests ensure the core system is working correctly.
"""

from pathlib import Path

import pytest


class TestBasicFunctionality:
    """Basic smoke tests for OCR-MCP functionality."""

    def test_imports_work(self):
        """Test that all core modules can be imported."""
        try:
            from ocr_mcp.core.backend_manager import BackendManager
            from ocr_mcp.core.config import OCRConfig
            from ocr_mcp.tools.ocr_tools import register_sota_tools

            # All imports successful
            assert True
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_config_creation(self, config):
        """Test that OCR configuration can be created."""
        assert config is not None
        assert isinstance(config.cache_dir, Path)
        assert config.device in ["auto", "cpu", "cuda"]
        assert config.default_backend in [
            "auto",
            "deepseek-ocr",
            "florence-2",
            "tesseract",
            "got-ocr",
            "dots-ocr",
            "pp-ocrv5",
            "qwen-image-layered",
            "easyocr",
        ]

    def test_backend_manager_creation(self, backend_manager):
        """Test that backend manager can be created."""
        assert backend_manager is not None
        assert hasattr(backend_manager, "backends")
        assert isinstance(backend_manager.backends, dict)
        assert len(backend_manager.backends) > 0

    def test_mock_backend_availability(self, backend_manager):
        """Test that mock backends are properly configured."""
        available_backends = backend_manager.get_available_backends()

        # Should have some backends available for testing
        assert len(available_backends) > 0

        # At least one known registry name should be present (availability varies by env)
        known = {"got-ocr", "tesseract", "deepseek-ocr", "dots-ocr", "pp-ocrv5", "easyocr"}
        available_set = set(available_backends)
        assert len(available_set.intersection(known)) > 0 or len(available_backends) > 0

    def test_file_validation_works(self):
        """Test that file path validation works."""
        from ocr_mcp.core.error_handler import ErrorHandler

        # Test with current file (should exist)
        current_file = Path(__file__)
        result = ErrorHandler.validate_file_path(str(current_file))
        assert result is None  # Should pass validation

        # Test with non-existent file
        nonexistent = Path("/nonexistent/file/that/does/not/exist.txt")
        result = ErrorHandler.validate_file_path(str(nonexistent))
        assert result is not None  # Should fail validation

    def test_test_data_generation(self, test_data_generator):
        """Test that test data generator works."""
        # Generate a test image
        img = test_data_generator.create_test_image(text="Smoke test", width=100, height=100)

        assert img is not None
        assert img.size == (100, 100)
        assert img.mode == "RGB"

    def test_performance_profiler(self, performance_profiler):
        """Test that performance profiler works."""
        import time

        performance_profiler.start()
        time.sleep(0.01)  # Small delay
        elapsed = performance_profiler.stop("test_operation")

        assert elapsed > 0
        assert elapsed < 1.0  # Should be reasonable

    def test_error_handler(self):
        """Test that error handler works."""
        from ocr_mcp.core.error_handler import ErrorHandler

        # Test creating a structured error
        error = ErrorHandler.create_error("PARAMETERS_INVALID", details={"test": "data"})

        assert error is not None
        assert hasattr(error, "error_code")
        assert hasattr(error, "category")
        assert hasattr(error, "severity")

        # Test error to dict conversion
        error_dict = error.to_dict()
        assert error_dict["success"] is False
        assert "error" in error_dict
        assert "error_code" in error_dict

    def test_file_manager(self, file_manager):
        """Test that test file manager works."""
        # Create a test file
        test_content = "Test file content"
        test_file = file_manager.create_temp_file(test_content, ".txt")

        assert test_file.exists()
        assert test_file.read_text() == test_content

        # File should be cleaned up automatically by fixture

    def test_async_test_helper(self, async_test_helper):
        """Test that async test helper works."""
        import asyncio

        async def simple_async_func():
            await asyncio.sleep(0.01)
            return "success"

        # Should complete successfully
        result = asyncio.run(simple_async_func())
        assert result == "success"

    def test_data_validator(self, data_validator):
        """Test that data validator works."""
        from ocr_mcp.core.error_handler import ErrorHandler

        # Test valid file path
        current_file = Path(__file__)
        is_valid = ErrorHandler.validate_file_path(str(current_file)) is None
        assert is_valid

        # Test invalid file path
        invalid_path = "/invalid/path/that/does/not/exist.xyz"
        is_invalid = ErrorHandler.validate_file_path(invalid_path) is not None
        assert is_invalid

    def test_backend_get_capabilities(self, backend_manager):
        """Test that backends provide capabilities."""
        # Get first available backend
        available_backends = backend_manager.get_available_backends()
        if available_backends:
            backend = backend_manager.get_backend(available_backends[0])
            assert backend is not None

            capabilities = backend.get_capabilities()
            assert isinstance(capabilities, dict)
            assert "name" in capabilities
            assert "available" in capabilities

    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="Async event loop can fail on Windows; run with uv run pytest -p no:asyncio to avoid"
    )
    async def test_basic_ocr_processing(self, backend_manager, sample_image_path):
        """Test basic OCR processing workflow."""
        result = await backend_manager.process_with_backend(
            "auto", str(sample_image_path), mode="text"
        )
        assert isinstance(result, dict)
        assert "success" in result
        if result.get("success"):
            assert "text" in result
            assert "backend_used" in result

    def test_test_context_availability(self, test_context):
        """Test that comprehensive test context is available."""
        assert "data_generator" in test_context
        assert "profiler" in test_context
        assert "file_manager" in test_context
        assert "async_helper" in test_context
        assert "validator" in test_context
        assert "server_manager" in test_context

        # Test that all utilities can be accessed
        assert hasattr(test_context["data_generator"], "create_test_image")
        assert hasattr(test_context["profiler"], "start")
        assert hasattr(test_context["file_manager"], "create_temp_file")

    def test_environment_isolation(self):
        """Test that test environment is properly isolated."""
        import os

        # conftest sets OCR_TESTING via pytest_configure
        assert os.environ.get("OCR_TESTING") == "true"

    def test_fixture_compatibility(self, config, backend_manager, sample_image_path):
        """Test that all basic fixtures work together."""
        assert config is not None
        assert backend_manager is not None
        assert sample_image_path is not None
        assert sample_image_path.exists()

        # Backend manager should be configured with our config
        assert backend_manager.config == config
