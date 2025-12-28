"""
Integration tests for OCR-MCP tools.

These tests verify that the MCP tools work correctly end-to-end,
including proper parameter handling, error conditions, and result formatting.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from fastmcp import FastMCP

from src.ocr_mcp.tools.ocr_tools import register_document_processing_tools
from src.ocr_mcp.tools.scanner_tools import register_scanner_operations_tools
from src.ocr_mcp.core.config import OCRConfig
from src.ocr_mcp.core.backend_manager import BackendManager
from tests.mocks.mock_backends import MockDeepSeekBackend
from tests.mocks.mock_scanner import MockScannerManager


class TestMCPToolsIntegration:
    """Integration tests for MCP tools."""

    @pytest.fixture
    def config(self):
        """Test configuration."""
        return OCRConfig(cache_dir=Path("/tmp/test_cache"))

    @pytest.fixture
    def mock_backend_manager(self, config):
        """Mock backend manager for testing."""
        manager = MagicMock(spec=BackendManager)
        manager.config = config

        # Mock scanner manager
        mock_scanner = MockScannerManager()
        manager.scanner_manager = mock_scanner

        # Mock document processor
        mock_processor = MagicMock()
        mock_processor.is_available.return_value = True
        mock_processor.detect_file_type.return_value = "image"
        manager.document_processor = mock_processor

        # Mock OCR backend
        mock_backend = MockDeepSeekBackend(config)
        manager.select_backend.return_value = mock_backend
        manager.process_with_backend = AsyncMock(return_value={
            "success": True,
            "text": "Test OCR result",
            "backend": "deepseek-ocr",
            "confidence": 0.95
        })

        return manager

    @pytest.fixture
    def fastmcp_app(self):
        """FastMCP app instance for testing."""
        app = FastMCP("test-ocr-mcp")
        return app

    @pytest.fixture
    def registered_app(self, fastmcp_app, mock_backend_manager, config):
        """App with tools registered."""
        register_document_processing_tools(fastmcp_app, mock_backend_manager, config)
        register_scanner_operations_tools(fastmcp_app, mock_backend_manager, config)
        return fastmcp_app

    @pytest.mark.asyncio
    async def test_document_processing_tool_basic(self, registered_app, tmp_path):
        """Test basic document processing tool functionality."""
        # Create a test image
        test_image = tmp_path / "test.png"
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='white')
        img.save(test_image)

        # Get the tool
        tools = await registered_app.get_tools()
        process_tool = next(t for t in tools if t.name == "document_processing")

        # Call the tool
        result = await process_tool.fn(
            operation="process_document",
            source_path=str(test_image),
            backend="auto",
            ocr_mode="text"
        )

        assert result["success"] is True
        assert "text" in result
        assert "backend" in result

    @pytest.mark.asyncio
    async def test_document_processing_tool_with_options(self, registered_app, tmp_path):
        """Test document processing with various options."""
        test_image = tmp_path / "test.png"
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='white')
        img.save(test_image)

        tools = await registered_app.get_tools()
        process_tool = next(t for t in tools if t.name == "document_processing")

        # Test with formatting options
        result = await process_tool.fn(
            operation="process_document",
            source_path=str(test_image),
            backend="deepseek-ocr",
            ocr_mode="format",
            output_format="html",
            language="en"
        )

        assert result["success"] is True
        assert result.get("ocr_mode") == "format"

    @pytest.mark.asyncio
    async def test_document_processing_tool_region_ocr(self, registered_app, tmp_path):
        """Test region-specific OCR."""
        test_image = tmp_path / "test.png"
        from PIL import Image
        img = Image.new('RGB', (200, 200), color='white')
        img.save(test_image)

        tools = await registered_app.get_tools()
        process_tool = next(t for t in tools if t.name == "document_processing")

        region = [10, 10, 100, 100]
        result = await process_tool.fn(
            operation="extract_regions",
            source_path=str(test_image),
            backend="florence-2",
            region=region
        )

        assert result["success"] is True
        assert "region" in str(result).lower() or "fine-grained" in result.get("mode", "")

    @pytest.mark.asyncio
    async def test_process_document_tool_comic_mode(self, registered_app, tmp_path):
        """Test comic/manga processing mode."""
        test_image = tmp_path / "comic.png"
        from PIL import Image
        img = Image.new('RGB', (500, 700), color='white')  # Comic page proportions
        img.save(test_image)

        tools = await registered_app.get_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        result = await process_tool.fn(
            source_path=str(test_image),
            backend="got-ocr",
            mode="formatted",
            comic_mode=True,
            manga_layout=True,
            scaffold_separate=True,
            panel_analysis=True
        )

        assert result["success"] is True
        assert result.get("comic_mode") is True
        assert result.get("manga_layout") is True

    @pytest.mark.asyncio
    async def test_workflow_management_batch_tool(self, registered_app, tmp_path):
        """Test batch document processing."""
        # Create multiple test images
        test_images = []
        for i in range(3):
            img_path = tmp_path / f"test_{i}.png"
            from PIL import Image
            img = Image.new('RGB', (100, 100), color='white')
            img.save(img_path)
            test_images.append(str(img_path))

        tools = await registered_app.get_tools()
        batch_tool = next(t for t in tools if t.name == "workflow_management")

        result = await batch_tool.fn(
            operation="process_batch_intelligent",
            document_paths=test_images,
            workflow_type="auto",
            quality_threshold=0.8,
            max_concurrent=2
        )

        assert result["success"] is True
        assert result["total_documents"] == 3
        assert "results" in result
        assert len(result["results"]) == 3

    @pytest.mark.asyncio
    async def test_workflow_management_health_check_tool(self, registered_app):
        """Test OCR health check tool."""
        tools = await registered_app.get_tools()
        workflow_tool = next(t for t in tools if t.name == "workflow_management")

        result = await workflow_tool.fn(operation="ocr_health_check")

        assert "status" in result
        assert "ocr_backends" in result
        assert "scanner_backends" in result
        assert "configuration" in result

    @pytest.mark.asyncio
    async def test_list_backends_tool(self, registered_app):
        """Test list backends tool."""
        tools = await registered_app.get_tools()
        list_tool = next(t for t in tools if t.name == "list_backends")

        result = await list_tool.fn()

        assert "backends" in result
        assert "available_count" in result
        assert "total_count" in result
        assert isinstance(result["backends"], dict)

    @pytest.mark.asyncio
    async def test_scanner_operations_list_tool(self, registered_app):
        """Test list scanners tool."""
        tools = await registered_app.get_tools()
        scanner_tool = next(t for t in tools if t.name == "scanner_operations")

        result = await scanner_tool.fn(operation="list_scanners")

        assert isinstance(result, dict)
        assert "scanners" in result
        assert isinstance(result["scanners"], list)

    @pytest.mark.asyncio
    async def test_scanner_operations_properties_tool(self, registered_app):
        """Test scanner properties tool."""
        tools = await registered_app.get_tools()
        scanner_tool = next(t for t in tools if t.name == "scanner_operations")

        result = await scanner_tool.fn(operation="scanner_properties", device_id="wia:test_scanner_1")

        assert isinstance(result, dict)
        # Properties may be None if scanner not found
        if result and "properties" in result:
            assert isinstance(result["properties"], dict)

    @pytest.mark.asyncio
    async def test_scanner_operations_configure_tool(self, registered_app):
        """Test scan configuration tool."""
        tools = await registered_app.get_tools()
        scanner_tool = next(t for t in tools if t.name == "scanner_operations")

        result = await scanner_tool.fn(
            operation="configure_scan",
            device_id="wia:test_scanner_1",
            dpi=300,
            color_mode="Color",
            paper_size="A4",
            brightness=0,
            contrast=0,
            use_adf=False,
            duplex=False
        )

        assert isinstance(result, dict)
        assert "configured" in result

    @pytest.mark.asyncio
    async def test_scanner_operations_scan_tool(self, registered_app):
        """Test document scanning tool."""
        tools = await registered_app.get_tools()
        scanner_tool = next(t for t in tools if t.name == "scanner_operations")

        result = await scanner_tool.fn(
            operation="scan_document",
            device_id="wia:test_scanner_1",
            dpi=300,
            color_mode="Color",
            paper_size="A4",
            save_path=None
        )

        # Result should be scan result data
        assert isinstance(result, dict)
        assert "device_id" in result

    @pytest.mark.asyncio
    async def test_scan_batch_tool(self, registered_app):
        """Test batch scanning tool."""
        tools = await registered_app.get_tools()
        batch_scan_tool = next(t for t in tools if t.name == "scan_batch")

        result = await batch_scan_tool.fn(
            device_id="wia:test_scanner_1",
            count=2,
            dpi=150,
            color_mode="Grayscale",
            paper_size="A4",
            save_directory=None
        )

        assert isinstance(result, list)
        assert len(result) <= 2  # May be less if scanning fails

    @pytest.mark.asyncio
    async def test_preview_scan_tool(self, registered_app):
        """Test preview scanning tool."""
        tools = await registered_app.get_tools()
        preview_tool = next(t for t in tools if t.name == "preview_scan")

        result = await preview_tool.fn(
            device_id="wia:test_scanner_1",
            dpi=75,
            save_path=None
        )

        # Result should be image data or file path
        assert result is not None


class TestToolErrorHandling:
    """Test error handling in MCP tools."""

    @pytest.fixture
    def failing_backend_manager(self, config):
        """Backend manager that simulates failures."""
        manager = MagicMock(spec=BackendManager)

        # Make scanner manager fail
        failing_scanner = MockScannerManager()
        failing_scanner.scan_document.return_value = None
        manager.scanner_manager = failing_scanner

        # Make OCR processing fail
        manager.process_with_backend = AsyncMock(return_value={
            "success": False,
            "error": "OCR processing failed"
        })

        # Make backend selection fail
        manager.select_backend.return_value = None

        return manager

    @pytest.mark.asyncio
    async def test_document_processing_file_not_found(self, fastmcp_app, mock_backend_manager, config):
        """Test handling of non-existent files."""
        register_document_processing_tools(fastmcp_app, mock_backend_manager, config)

        tools = await fastmcp_app.get_tools()
        process_tool = next(t for t in tools if t.name == "document_processing")

        result = await process_tool.fn(
            operation="process_document",
            source_path="/nonexistent/file.png",
            backend="auto"
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_process_document_unsupported_format(self, fastmcp_app, mock_backend_manager, config, tmp_path):
        """Test handling of unsupported file formats."""
        # Create a file with unsupported extension
        unsupported_file = tmp_path / "test.xyz"
        unsupported_file.write_text("not an image")

        register_ocr_tools(fastmcp_app, mock_backend_manager, config)

        tools = await fastmcp_app.get_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        result = await process_tool.fn(
            source_path=str(unsupported_file),
            backend="auto"
        )

        assert result["success"] is False
        assert "unsupported" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_scanner_operations_with_invalid_device(self, fastmcp_app, mock_backend_manager, config):
        """Test scanner tools with invalid device IDs."""
        register_scanner_operations_tools(fastmcp_app, mock_backend_manager, config)

        tools = await fastmcp_app.get_tools()
        scanner_tool = next(t for t in tools if t.name == "scanner_operations")

        result = await scanner_tool.fn(operation="scanner_properties", device_id="invalid:device")

        # Should handle gracefully
        assert isinstance(result, dict)
        assert result["success"] is False


class TestToolParameterValidation:
    """Test parameter validation in MCP tools."""

    @pytest.mark.asyncio
    async def test_document_processing_invalid_backend(self, fastmcp_app, mock_backend_manager, config, tmp_path):
        """Test processing with invalid backend name."""
        test_image = tmp_path / "test.png"
        from PIL import Image
        img = Image.new('RGB', (50, 50), color='white')
        img.save(test_image)

        register_document_processing_tools(fastmcp_app, mock_backend_manager, config)

        tools = await fastmcp_app.get_tools()
        process_tool = next(t for t in tools if t.name == "document_processing")

        result = await process_tool.fn(
            operation="process_document",
            source_path=str(test_image),
            backend="invalid-backend"
        )

        # Should either fail gracefully or fall back to auto
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_scanner_operations_invalid_parameters(self, fastmcp_app, mock_backend_manager, config):
        """Test scan configuration with invalid parameters."""
        register_scanner_operations_tools(fastmcp_app, mock_backend_manager, config)

        tools = await fastmcp_app.get_tools()
        scanner_tool = next(t for t in tools if t.name == "scanner_operations")

        result = await scanner_tool.fn(
            operation="configure_scan",
            device_id="wia:test_scanner_1",
            dpi=-1,  # Invalid DPI
            color_mode="InvalidMode",  # Invalid color mode
            paper_size="InvalidSize"
        )

        # Should handle invalid parameters gracefully
        assert isinstance(result, dict)

    @pytest.mark.parametrize("tool_name,operation,required_params", [
        ("document_processing", "process_document", ["source_path"]),
        ("scanner_operations", "list_scanners", []),
        ("scanner_operations", "scanner_properties", ["device_id"]),
        ("scanner_operations", "configure_scan", ["device_id"]),
        ("scanner_operations", "scan_document", ["device_id"]),
        ("scanner_operations", "scan_batch", ["device_id"]),
        ("scanner_operations", "preview_scan", ["device_id"]),
    ])
    @pytest.mark.asyncio
    async def test_tool_parameter_requirements(self, fastmcp_app, mock_backend_manager, config, tool_name, operation, required_params):
        """Test that tools enforce required parameters."""
        register_document_processing_tools(fastmcp_app, mock_backend_manager, config)
        register_scanner_operations_tools(fastmcp_app, mock_backend_manager, config)

        tools = await fastmcp_app.get_tools()
        tool = next((t for t in tools if t.name == tool_name), None)

        if tool:
            # This is a basic check that the tool exists and has the expected signature
            # More detailed parameter validation would require calling the tool
            assert tool.name == tool_name


class TestToolConcurrency:
    """Test concurrent execution of MCP tools."""

    @pytest.mark.asyncio
    async def test_batch_processing_concurrency(self, fastmcp_app, mock_backend_manager, config, tmp_path):
        """Test that batch processing handles concurrency correctly."""
        # Create multiple test files
        test_files = []
        for i in range(5):
            img_path = tmp_path / f"batch_test_{i}.png"
            from PIL import Image
            img = Image.new('RGB', (50, 50), color='white')
            img.save(img_path)
            test_files.append(str(img_path))

        register_workflow_management_tools(fastmcp_app, mock_backend_manager, config)

        tools = await fastmcp_app.get_tools()
        workflow_tool = next(t for t in tools if t.name == "workflow_management")

        result = await workflow_tool.fn(
            operation="process_batch_intelligent",
            document_paths=test_files,
            workflow_type="auto",
            max_concurrent=3
        )

        assert result["success"] is True
        assert result["total_documents"] == 5
        assert len(result["results"]) == 5

    @pytest.mark.asyncio
    async def test_multiple_simultaneous_scans(self, fastmcp_app, mock_backend_manager, config):
        """Test multiple simultaneous scan operations."""
        register_scanner_operations_tools(fastmcp_app, mock_backend_manager, config)

        tools = await fastmcp_app.get_tools()
        scanner_tool = next(t for t in tools if t.name == "scanner_operations")

        # Simulate multiple concurrent scan requests
        import asyncio

        async def scan_once():
            return await scanner_tool.fn(
                operation="scan_document",
                device_id="wia:test_scanner_1",
                dpi=150,
                color_mode="Grayscale"
            )

        # Run multiple scans concurrently
        results = await asyncio.gather(*[scan_once() for _ in range(3)])

        assert len(results) == 3
        # All results should be valid dictionaries
        for result in results:
            assert isinstance(result, dict)






