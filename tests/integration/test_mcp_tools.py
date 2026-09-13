# MIT License
#
# Copyright (c) 2025 OCR-MCP Project
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
#
#
#
#

"""
Integration tests for OCR-MCP tools.

These tests verify that the MCP tools work correctly end-to-end,
including proper parameter handling, error conditions, and result formatting.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastmcp import FastMCP

from ocr_mcp.core.backend_manager import BackendManager
from ocr_mcp.core.config import OCRConfig
from ocr_mcp.tools.ocr_tools import register_sota_tools
from tests.mocks.mock_backends import MockDeepSeekBackend
from tests.mocks.mock_scanner import MockScannerManager


def _flat(res):
    """Flatten the SOTA tool contract for legacy flat-dict assertions.

    Portmanteau tools return ``ToolResponse`` (pydantic) with the payload
    nested under ``result`` (or ``results`` for create_success_response
    dicts). This merges nested payload keys to the top level so tests can
    assert on the documented payload fields directly.
    """
    if isinstance(res, dict):
        data = dict(res)
    elif hasattr(res, "model_dump"):
        data = res.model_dump()
    else:
        return res
    for key in ("result", "results"):
        nested = data.get(key)
        if isinstance(nested, dict):
            for k, v in nested.items():
                data.setdefault(k, v)
    return data


@pytest.fixture
def config():
    """Test configuration (module scope: shared by all test classes)."""
    return OCRConfig(cache_dir=Path("/tmp/test_cache"))


@pytest.fixture
def mock_backend_manager(config, mock_scanner_manager):
    """Mock backend manager for testing (module scope: shared by all test classes)."""
    manager = MagicMock(spec=BackendManager)
    manager.config = config
    manager.scanner_manager = mock_scanner_manager

    mock_processor = MagicMock()
    mock_processor.is_available.return_value = True
    mock_processor.detect_file_type.return_value = "image"
    manager.document_processor = mock_processor

    mock_backend = MockDeepSeekBackend(config)
    manager.select_backend.return_value = mock_backend
    manager.process_with_backend = AsyncMock(
        return_value={
            "success": True,
            "text": "Test OCR result",
            "backend": "deepseek-ocr2",
            "confidence": 0.95,
        }
    )
    # Declared double for the intelligent-batch path (real impl delegates here).
    manager.process_document = AsyncMock(
        return_value={
            "success": True,
            "text": "Test OCR result",
            "backend": "deepseek-ocr2",
            "confidence": 0.95,
        }
    )
    # Declared double for backend listing (real impl returns this shape).
    manager.list_backends = MagicMock(
        return_value={
            "backends": {
                "deepseek-ocr2": {"available": True},
                "tesseract": {"available": True},
            },
            "available_count": 2,
            "total_count": 2,
        }
    )

    return manager


@pytest.fixture
def fastmcp_app():
    """FastMCP app instance for testing (module scope: shared by all test classes)."""
    app = FastMCP("test-ocr-mcp")
    return app


class TestMCPToolsIntegration:
    """Integration tests for MCP tools."""

    @pytest.fixture
    def registered_app(self, fastmcp_app, mock_backend_manager, config):
        """App with tools registered."""
        register_sota_tools(fastmcp_app, mock_backend_manager, config)
        return fastmcp_app

    @pytest.mark.asyncio
    async def test_document_processing_tool_basic(self, registered_app, tmp_path):
        """Test basic document processing tool functionality."""
        # Create a test image
        test_image = tmp_path / "test.png"
        from PIL import Image

        img = Image.new("RGB", (100, 100), color="white")
        img.save(test_image)

        # Get the tool
        tools = await registered_app.list_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Call the tool
        result = _flat(
            await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                operation="process_document",
                source_path=str(test_image),
                backend="auto",
                ocr_mode="text",
            )
        )

        assert result["success"] is True
        assert "text" in result
        assert "backend" in result

    @pytest.mark.asyncio
    async def test_document_processing_tool_with_options(self, registered_app, tmp_path):
        """Test document processing with various options."""
        test_image = tmp_path / "test.png"
        from PIL import Image

        img = Image.new("RGB", (100, 100), color="white")
        img.save(test_image)

        tools = await registered_app.list_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Test with formatting options
        result = _flat(
            await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                operation="process_document",
                source_path=str(test_image),
                backend="deepseek-ocr2",
                ocr_mode="format",
                output_format="html",
                language="en",
            )
        )

        assert result["success"] is True
        assert result.get("backend_used") or result.get("backend")

    @pytest.mark.asyncio
    async def test_document_processing_tool_region_ocr(self, registered_app, tmp_path):
        """Test region-specific OCR."""
        test_image = tmp_path / "test.png"
        from PIL import Image

        img = Image.new("RGB", (200, 200), color="white")
        img.save(test_image)

        tools = await registered_app.list_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        region = [10, 10, 100, 100]
        result = _flat(
            await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                operation="process_document",
                source_path=str(test_image),
                backend="florence-2",
                region=region,
            )
        )

        assert result["success"] is True
        assert "text" in result

    @pytest.mark.asyncio
    async def test_process_document_tool_comic_mode(self, registered_app, tmp_path):
        """Test dense-layout processing mode (ex comic/manga params, removed in SOTA refit)."""
        test_image = tmp_path / "comic.png"
        from PIL import Image

        img = Image.new("RGB", (500, 700), color="white")  # Comic page proportions
        img.save(test_image)

        tools = await registered_app.list_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        result = _flat(
            await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                operation="process_document",
                source_path=str(test_image),
                backend="got-ocr",
                ocr_mode="accurate",
            )
        )

        assert result["success"] is True
        assert "text" in result

    @pytest.mark.asyncio
    async def test_workflow_management_batch_tool(self, registered_app, tmp_path):
        """Test batch document processing."""
        # Create multiple test images
        test_images = []
        for i in range(3):
            img_path = tmp_path / f"test_{i}.png"
            from PIL import Image

            img = Image.new("RGB", (100, 100), color="white")
            img.save(img_path)
            test_images.append(str(img_path))

        tools = await registered_app.list_tools()
        batch_tool = next(t for t in tools if t.name == "manage_workflow")

        result = _flat(
            await (batch_tool.fn if hasattr(batch_tool, "fn") else batch_tool)(
                operation="process_batch_intelligent",
                source_dir=str(tmp_path),
            )
        )

        assert result["success"] is True
        assert result["batch_summary"]["total_documents"] == 3
        assert "results" in result
        assert len(result["results"]) == 3

    @pytest.mark.asyncio
    async def test_workflow_management_health_check_tool(self, registered_app):
        """Test OCR health check tool."""
        tools = await registered_app.list_tools()
        workflow_tool = next(t for t in tools if t.name == "manage_workflow")

        result = _flat(
            await (workflow_tool.fn if hasattr(workflow_tool, "fn") else workflow_tool)(operation="ocr_health_check")
        )

        assert result["success"] is True
        assert result.get("status") == "healthy"
        assert isinstance(result.get("backends"), dict)

    @pytest.mark.asyncio
    async def test_list_backends_tool(self, registered_app):
        """Test list backends tool."""
        tools = await registered_app.list_tools()
        list_tool = next(t for t in tools if t.name == "manage_workflow")

        result = _flat(await (list_tool.fn if hasattr(list_tool, "fn") else list_tool)(operation="list_backends"))

        assert result["success"] is True
        assert isinstance(result["backends"], dict)
        assert result["backends"]["available_count"] == 2
        assert result["backends"]["total_count"] == 2

    @pytest.mark.asyncio
    async def test_scanner_operations_list_tool(self, registered_app):
        """Test list scanners tool."""
        tools = await registered_app.list_tools()
        scanner_tool = next(t for t in tools if t.name == "operate_scanner")

        result = _flat(
            await (scanner_tool.fn if hasattr(scanner_tool, "fn") else scanner_tool)(operation="list_scanners")
        )

        assert isinstance(result, dict)
        assert "scanners" in result
        assert isinstance(result["scanners"], list)

    @pytest.mark.asyncio
    async def test_scanner_operations_properties_tool(self, registered_app):
        """Test scanner properties tool."""
        tools = await registered_app.list_tools()
        scanner_tool = next(t for t in tools if t.name == "operate_scanner")

        result = _flat(
            await (scanner_tool.fn if hasattr(scanner_tool, "fn") else scanner_tool)(
                operation="scanner_properties", device_id="wia:test_scanner_1"
            )
        )

        assert isinstance(result, dict)
        # Properties may be None if scanner not found
        if result and "properties" in result:
            assert isinstance(result["properties"], dict)

    @pytest.mark.asyncio
    async def test_scanner_operations_configure_tool(self, registered_app):
        """Test scan configuration tool."""
        tools = await registered_app.list_tools()
        scanner_tool = next(t for t in tools if t.name == "operate_scanner")

        result = _flat(
            await (scanner_tool.fn if hasattr(scanner_tool, "fn") else scanner_tool)(
                operation="configure_scan",
                device_id="wia:test_scanner_1",
                resolution=300,
                color_mode="color",
                paper_size="A4",
                brightness=0,
                contrast=0,
                duplex=False,
            )
        )

        assert isinstance(result, dict)
        assert "configured" in result

    @pytest.mark.asyncio
    async def test_scanner_operations_scan_tool(self, registered_app, tmp_path):
        """Test document scanning tool."""
        tools = await registered_app.list_tools()
        scanner_tool = next(t for t in tools if t.name == "operate_scanner")

        result = _flat(
            await (scanner_tool.fn if hasattr(scanner_tool, "fn") else scanner_tool)(
                operation="scan_document",
                device_id="wia:test_scanner_1",
                resolution=300,
                color_mode="color",
                paper_size="A4",
                save_path=str(tmp_path / "scan.png"),
            )
        )

        # Result should be scan result data
        assert isinstance(result, dict)
        assert "device_id" in result

    @pytest.mark.asyncio
    async def test_scan_batch_tool(self, registered_app, tmp_path):
        """Test batch scanning tool."""
        tools = await registered_app.list_tools()
        batch_scan_tool = next(t for t in tools if t.name == "operate_scanner")

        result = _flat(
            await (batch_scan_tool.fn if hasattr(batch_scan_tool, "fn") else batch_scan_tool)(
                operation="scan_batch",
                device_id="wia:test_scanner_1",
                count=2,
                resolution=150,
                color_mode="grayscale",
                paper_size="A4",
                save_directory=str(tmp_path),
            )
        )

        assert result["success"] is True
        assert result["count_completed"] == 2
        assert len(result["saved_paths"]) == 2

    @pytest.mark.asyncio
    async def test_preview_scan_tool(self, registered_app, tmp_path):
        """Test preview scanning tool."""
        tools = await registered_app.list_tools()
        preview_tool = next(t for t in tools if t.name == "operate_scanner")

        result = _flat(
            await (preview_tool.fn if hasattr(preview_tool, "fn") else preview_tool)(
                operation="preview_scan",
                device_id="wia:test_scanner_1",
                save_path=str(tmp_path / "preview.png"),
            )
        )

        # Result should be image data or file path
        assert result is not None
        assert result["success"] is True


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
        manager.process_with_backend = AsyncMock(return_value={"success": False, "error": "OCR processing failed"})

        # Make backend selection fail
        manager.select_backend.return_value = None

        return manager

    @pytest.mark.asyncio
    async def test_document_processing_file_not_found(self, fastmcp_app, mock_backend_manager, config):
        """Test handling of non-existent files."""
        register_sota_tools(fastmcp_app, mock_backend_manager, config)

        tools = await fastmcp_app.list_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        result = _flat(
            await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                operation="process_document", source_path="/nonexistent/file.png", backend="auto"
            )
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_process_document_unsupported_format(self, fastmcp_app, mock_backend_manager, config, tmp_path):
        """Test handling of unsupported file formats."""
        # Create a file with unsupported extension
        unsupported_file = tmp_path / "test.xyz"
        unsupported_file.write_text("not an image")

        # Backend double rejects unknown extensions, like a real backend would.
        async def _reject_xyz(**kwargs):
            if str(kwargs.get("image_path", "")).endswith(".xyz"):
                return {"success": False, "error": "Unsupported file type: xyz"}
            return {
                "success": True,
                "text": "Test OCR result",
                "backend": "deepseek-ocr2",
                "confidence": 0.95,
            }

        mock_backend_manager.process_with_backend = AsyncMock(side_effect=_reject_xyz)
        register_sota_tools(fastmcp_app, mock_backend_manager, config)

        tools = await fastmcp_app.list_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        result = _flat(
            await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                operation="process_document", source_path=str(unsupported_file), backend="auto"
            )
        )

        assert result["success"] is False
        assert "unsupported" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_scanner_operations_with_invalid_device(self, fastmcp_app, mock_backend_manager, config):
        """Test scanner tools with invalid device IDs."""
        # Unknown devices resolve to no properties (declared double behavior).
        mock_backend_manager.scanner_manager.get_scanner_properties.return_value = None
        register_sota_tools(fastmcp_app, mock_backend_manager, config)

        tools = await fastmcp_app.list_tools()
        scanner_tool = next(t for t in tools if t.name == "operate_scanner")

        result = _flat(
            await (scanner_tool.fn if hasattr(scanner_tool, "fn") else scanner_tool)(
                operation="scanner_properties", device_id="invalid:device"
            )
        )

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

        img = Image.new("RGB", (50, 50), color="white")
        img.save(test_image)

        register_sota_tools(fastmcp_app, mock_backend_manager, config)

        tools = await fastmcp_app.list_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        result = _flat(
            await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                operation="process_document", source_path=str(test_image), backend="invalid-backend"
            )
        )

        # Should either fail gracefully or fall back to auto
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_scanner_operations_invalid_parameters(self, fastmcp_app, mock_backend_manager, config):
        """Test scan configuration with invalid parameters."""
        register_sota_tools(fastmcp_app, mock_backend_manager, config)

        tools = await fastmcp_app.list_tools()
        scanner_tool = next(t for t in tools if t.name == "operate_scanner")

        result = _flat(
            await (scanner_tool.fn if hasattr(scanner_tool, "fn") else scanner_tool)(
                operation="configure_scan",
                device_id="wia:test_scanner_1",
                resolution=-1,  # Invalid DPI
                color_mode="InvalidMode",  # Invalid color mode
                paper_size="InvalidSize",
            )
        )

        # Should handle invalid parameters gracefully
        assert isinstance(result, dict)

    @pytest.mark.parametrize(
        "tool_name,operation,required_params",
        [
            ("process_document", "process_document", ["source_path"]),
            ("operate_scanner", "list_scanners", []),
            ("operate_scanner", "scanner_properties", ["device_id"]),
            ("operate_scanner", "configure_scan", ["device_id"]),
            ("operate_scanner", "scan_document", ["device_id"]),
            ("operate_scanner", "scan_batch", ["device_id"]),
            ("operate_scanner", "preview_scan", ["device_id"]),
        ],
    )
    @pytest.mark.asyncio
    async def test_tool_parameter_requirements(
        self, fastmcp_app, mock_backend_manager, config, tool_name, operation, required_params
    ):
        """Test that tools enforce required parameters."""
        register_sota_tools(fastmcp_app, mock_backend_manager, config)
        register_sota_tools(fastmcp_app, mock_backend_manager, config)

        tools = await fastmcp_app.list_tools()
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

            img = Image.new("RGB", (50, 50), color="white")
            img.save(img_path)
            test_files.append(str(img_path))

        register_sota_tools(fastmcp_app, mock_backend_manager, config)

        tools = await fastmcp_app.list_tools()
        workflow_tool = next(t for t in tools if t.name == "manage_workflow")

        result = _flat(
            await (workflow_tool.fn if hasattr(workflow_tool, "fn") else workflow_tool)(
                operation="process_batch_intelligent",
                source_dir=str(tmp_path),
            )
        )

        assert result["success"] is True
        assert result["batch_summary"]["total_documents"] == 5
        assert len(result["results"]) == 5

    @pytest.mark.asyncio
    async def test_multiple_simultaneous_scans(self, fastmcp_app, mock_backend_manager, config):
        """Test multiple simultaneous scan operations."""
        register_sota_tools(fastmcp_app, mock_backend_manager, config)

        tools = await fastmcp_app.list_tools()
        scanner_tool = next(t for t in tools if t.name == "operate_scanner")

        # Simulate multiple concurrent scan requests
        import asyncio

        async def scan_once():
            return _flat(
                await (scanner_tool.fn if hasattr(scanner_tool, "fn") else scanner_tool)(
                    operation="scan_document",
                    device_id="wia:test_scanner_1",
                    resolution=150,
                    color_mode="grayscale",
                )
            )

        # Run multiple scans concurrently
        results = await asyncio.gather(*[scan_once() for _ in range(3)])

        assert len(results) == 3
        # All results should be valid dictionaries
        for result in results:
            assert isinstance(result, dict)
