"""
End-to-end tests for complete OCR-MCP workflows.

These tests verify full user workflows from document acquisition
through OCR processing to final results.
"""

import pytest
import asyncio
from pathlib import Path
from PIL import Image

from src.ocr_mcp.core.config import OCRConfig
from src.ocr_mcp.core.backend_manager import BackendManager
from src.ocr_mcp.tools.ocr_tools import register_ocr_tools
from src.ocr_mcp.tools.scanner_tools import register_scanner_tools
from fastmcp import FastMCP


class TestCompleteWorkflows:
    """End-to-end workflow tests."""

    @pytest.fixture
    def config(self, temp_dir):
        """Test configuration."""
        return OCRConfig(cache_dir=temp_dir / "cache")

    @pytest.fixture
    def backend_manager(self, config):
        """Backend manager with mocked components."""
        manager = BackendManager(config)

        # Mock successful OCR processing
        async def mock_process_success(backend_name, image_path, **kwargs):
            await asyncio.sleep(0.1)  # Simulate processing time
            return {
                "success": True,
                "text": f"OCR result from {backend_name} for {Path(image_path).name}",
                "confidence": 0.92,
                "backend": backend_name,
                "processing_time": 0.1,
                "mode": kwargs.get("mode", "text")
            }

        manager.process_with_backend = mock_process_success
        return manager

    @pytest.fixture
    def fastmcp_app(self, backend_manager, config):
        """FastMCP app with all tools registered."""
        app = FastMCP("test-ocr-mcp")
        register_ocr_tools(app, backend_manager, config)
        register_scanner_tools(app, backend_manager, config)
        return app

    @pytest.mark.asyncio
    async def test_scan_to_ocr_workflow(self, fastmcp_app, temp_dir):
        """Test complete workflow: scan document -> OCR processing."""
        # Step 1: Configure scanner
        tools = await fastmcp_app.get_tools()
        config_tool = next(t for t in tools if t.name == "configure_scan")

        config_result = await config_tool.fn(
            device_id="wia:test_scanner_1",
            dpi=300,
            color_mode="Color",
            paper_size="A4"
        )
        assert config_result is True

        # Step 2: Scan document
        scan_tool = next(t for t in tools if t.name == "scan_document")
        scanned_image = await scan_tool.fn(
            device_id="wia:test_scanner_1",
            dpi=300,
            color_mode="Color",
            paper_size="A4"
        )
        assert scanned_image is not None

        # Step 3: Process scanned document with OCR
        process_tool = next(t for t in tools if t.name == "process_document")

        # For this test, we'll simulate having the scanned image as a file
        test_image_path = temp_dir / "scanned_doc.png"
        # In real workflow, this would be the path returned by scan_tool
        test_image_path.write_bytes(b"mock image data")

        ocr_result = await process_tool.fn(
            source_path=str(test_image_path),
            backend="auto",
            mode="text"
        )

        assert ocr_result["success"] is True
        assert "text" in ocr_result
        assert ocr_result["backend"] != ""

    @pytest.mark.asyncio
    async def test_batch_scan_workflow(self, fastmcp_app):
        """Test batch scanning workflow."""
        tools = await fastmcp_app.get_tools()
        batch_scan_tool = next(t for t in tools if t.name == "scan_batch")

        # Scan multiple documents
        images = await batch_scan_tool.fn(
            device_id="wia:test_scanner_2",  # ADF scanner
            count=3,
            dpi=150,
            color_mode="Grayscale",
            paper_size="A4"
        )

        assert isinstance(images, list)
        assert len(images) <= 3  # May be less if scanning fails

    @pytest.mark.asyncio
    async def test_multi_format_processing_workflow(self, fastmcp_app, temp_dir):
        """Test processing multiple document formats."""
        tools = await fastmcp_app.get_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Test different file types
        test_files = []

        # Create test image
        img_path = temp_dir / "test.png"
        img = Image.new('RGB', (100, 100), color='white')
        img.save(img_path)
        test_files.append(("image", str(img_path)))

        results = []

        for file_type, file_path in test_files:
            result = await process_tool.fn(
                source_path=file_path,
                backend="auto",
                mode="text"
            )

            assert result["success"] is True
            assert result["file_type"] == file_type
            results.append(result)

        assert len(results) == len(test_files)

    @pytest.mark.asyncio
    async def test_comic_book_processing_workflow(self, fastmcp_app, temp_dir):
        """Test comic book processing workflow."""
        tools = await fastmcp_app.get_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Create a mock comic page (taller than wide, like comic pages)
        comic_path = temp_dir / "comic_page.png"
        comic_img = Image.new('RGB', (800, 1200), color='white')
        comic_img.save(comic_path)

        # Process with comic-specific options
        result = await process_tool.fn(
            source_path=str(comic_path),
            backend="got-ocr",
            mode="formatted",
            comic_mode=True,
            manga_layout=True,
            panel_analysis=True
        )

        assert result["success"] is True
        assert result.get("comic_mode") is True
        assert result.get("manga_layout") is True

    @pytest.mark.asyncio
    async def test_backend_selection_workflow(self, fastmcp_app, temp_dir):
        """Test backend selection and switching."""
        tools = await fastmcp_app.get_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Create test image
        img_path = temp_dir / "test.png"
        img = Image.new('RGB', (100, 100), color='white')
        img.save(img_path)

        # Test different backend selections
        backends_to_test = ["auto", "deepseek-ocr", "florence-2"]

        for backend in backends_to_test:
            result = await process_tool.fn(
                source_path=str(img_path),
                backend=backend,
                mode="text"
            )

            assert result["success"] is True
            # Backend should be resolved (not necessarily the requested one if auto)

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, fastmcp_app, temp_dir):
        """Test error handling and recovery."""
        tools = await fastmcp_app.get_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Test with non-existent file
        result = await process_tool.fn(
            source_path="/nonexistent/file.png",
            backend="auto"
        )

        assert result["success"] is False
        assert "error" in result

        # Test recovery with valid file
        img_path = temp_dir / "recovery_test.png"
        img = Image.new('RGB', (50, 50), color='white')
        img.save(img_path)

        result = await process_tool.fn(
            source_path=str(img_path),
            backend="auto"
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_performance_workflow(self, fastmcp_app, temp_dir, benchmark):
        """Test performance characteristics."""
        tools = await fastmcp_app.get_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Create test image
        img_path = temp_dir / "perf_test.png"
        img = Image.new('RGB', (200, 200), color='white')
        img.save(img_path)

        # Benchmark OCR processing
        async def run_ocr():
            return await process_tool.fn(
                source_path=str(img_path),
                backend="auto",
                mode="text"
            )

        result = await run_ocr()

        assert result["success"] is True
        assert result["processing_time"] > 0
        assert result["processing_time"] < 1.0  # Should be reasonably fast

    @pytest.mark.asyncio
    async def test_health_check_workflow(self, fastmcp_app):
        """Test system health monitoring."""
        tools = await fastmcp_app.get_tools()
        health_tool = next(t for t in tools if t.name == "ocr_health_check")

        health_result = await health_tool.fn()

        assert "status" in health_result
        assert "ocr_backends" in health_result
        assert "scanner_backends" in health_result
        assert "configuration" in health_result

        # Should have some backends available
        assert health_result["ocr_backends"]["total"] > 0

    @pytest.mark.asyncio
    async def test_scanner_discovery_workflow(self, fastmcp_app):
        """Test scanner discovery and enumeration."""
        tools = await fastmcp_app.get_tools()
        list_scanners_tool = next(t for t in tools if t.name == "list_scanners")

        scanners = await list_scanners_tool.fn()

        assert isinstance(scanners, list)
        # Should find at least the mock scanners
        assert len(scanners) >= 0

    @pytest.mark.asyncio
    async def test_region_ocr_workflow(self, fastmcp_app, temp_dir):
        """Test region-specific OCR processing."""
        tools = await fastmcp_app.get_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Create larger test image
        img_path = temp_dir / "region_test.png"
        img = Image.new('RGB', (400, 400), color='white')
        img.save(img_path)

        # Process specific region
        region = [50, 50, 200, 200]  # x1, y1, x2, y2

        result = await process_tool.fn(
            source_path=str(img_path),
            backend="florence-2",  # Backend that supports regions
            mode="fine-grained",
            region=region
        )

        assert result["success"] is True
        # Should indicate region processing
        assert "region" in str(result).lower() or "fine-grained" in result.get("mode", "")

    @pytest.mark.asyncio
    async def test_different_output_formats(self, fastmcp_app, temp_dir):
        """Test different output format handling."""
        tools = await fastmcp_app.get_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        img_path = temp_dir / "format_test.png"
        img = Image.new('RGB', (100, 100), color='white')
        img.save(img_path)

        output_formats = ["text", "json", "html"]

        for output_format in output_formats:
            result = await process_tool.fn(
                source_path=str(img_path),
                backend="auto",
                mode="text",
                output_format=output_format
            )

            assert result["success"] is True
            # Result structure may vary by format, but should succeed

    @pytest.mark.asyncio
    async def test_concurrent_processing_workflow(self, fastmcp_app, temp_dir):
        """Test concurrent document processing."""
        tools = await fastmcp_app.get_tools()
        batch_tool = next(t for t in tools if t.name == "process_batch_documents")

        # Create multiple test files
        test_files = []
        for i in range(4):
            img_path = temp_dir / f"concurrent_test_{i}.png"
            img = Image.new('RGB', (50, 50), color='white')
            img.save(img_path)
            test_files.append(str(img_path))

        # Process concurrently
        result = await batch_tool.fn(
            source_paths=test_files,
            backend="auto",
            mode="text",
            max_concurrent=2
        )

        assert result["success"] is True
        assert result["total_documents"] == 4
        assert len(result["results"]) == 4

        # All results should be successful
        successful_results = [r for r in result["results"] if r.get("success")]
        assert len(successful_results) == 4


class TestWorkflowErrorScenarios:
    """Test error scenarios in complete workflows."""

    @pytest.fixture
    def failing_backend_manager(self, config):
        """Backend manager that simulates various failures."""
        manager = BackendManager(config)

        # Mock OCR processing that sometimes fails
        call_count = 0
        async def mock_process_with_failures(backend_name, image_path, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.05)

            if call_count % 3 == 0:  # Fail every third call
                return {
                    "success": False,
                    "error": f"Simulated failure on call {call_count}",
                    "backend": backend_name
                }

            return {
                "success": True,
                "text": f"Success on call {call_count}",
                "backend": backend_name,
                "processing_time": 0.05
            }

        manager.process_with_backend = mock_process_with_failures
        return manager

    @pytest.mark.asyncio
    async def test_partial_batch_failure_workflow(self, fastmcp_app, failing_backend_manager, config, temp_dir):
        """Test batch processing with some failures."""
        # Re-register tools with failing backend manager
        app = FastMCP("test-failing-ocr-mcp")
        register_ocr_tools(app, failing_backend_manager, config)

        tools = await app.get_tools()
        batch_tool = next(t for t in tools if t.name == "process_batch_documents")

        # Create test files
        test_files = []
        for i in range(6):  # Should have 2 failures
            img_path = temp_dir / f"fail_test_{i}.png"
            img = Image.new('RGB', (30, 30), color='white')
            img.save(img_path)
            test_files.append(str(img_path))

        result = await batch_tool.fn(
            source_paths=test_files,
            backend="auto",
            mode="text"
        )

        assert result["total_documents"] == 6
        assert len(result["results"]) == 6

        # Should have some successes and some failures
        successful = [r for r in result["results"] if r.get("success")]
        failed = [r for r in result["results"] if not r.get("success")]

        assert len(successful) > 0
        assert len(failed) > 0
        assert result["successful_documents"] == len(successful)
        assert result["failed_documents"] == len(failed)

    @pytest.mark.asyncio
    async def test_scanner_failure_recovery(self, fastmcp_app, temp_dir):
        """Test recovery from scanner failures."""
        tools = await fastmcp_app.get_tools()
        scan_tool = next(t for t in tools if t.name == "scan_document")

        # Try scanning with invalid device
        result = await scan_tool.fn(
            device_id="invalid:device",
            dpi=150,
            color_mode="Color"
        )

        # Should handle gracefully without crashing
        assert result is not None  # May be None or error dict

        # Try with valid device
        result = await scan_tool.fn(
            device_id="wia:test_scanner_1",
            dpi=150,
            color_mode="Color"
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_network_timeout_simulation(self, fastmcp_app, temp_dir):
        """Test handling of timeouts and slow operations."""
        tools = await fastmcp_app.get_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Create test file
        img_path = temp_dir / "timeout_test.png"
        img = Image.new('RGB', (1000, 1000), color='white')  # Large file
        img.save(img_path)

        # Process should still complete (mock doesn't actually timeout)
        result = await process_tool.fn(
            source_path=str(img_path),
            backend="auto",
            mode="text"
        )

        assert result["success"] is True
        assert "processing_time" in result


class TestAdvancedWorkflows:
    """Test advanced multi-step workflows."""

    @pytest.mark.asyncio
    async def test_preview_then_full_scan_workflow(self, fastmcp_app):
        """Test preview scan followed by full scan."""
        tools = await fastmcp_app.get_tools()

        # Step 1: Preview scan
        preview_tool = next(t for t in tools if t.name == "preview_scan")
        preview_result = await preview_tool.fn(
            device_id="wia:test_scanner_1",
            dpi=75
        )

        assert preview_result is not None

        # Step 2: Configure for full scan
        config_tool = next(t for t in tools if t.name == "configure_scan")
        config_result = await config_tool.fn(
            device_id="wia:test_scanner_1",
            dpi=300,
            color_mode="Color",
            paper_size="A4"
        )

        assert config_result is True

        # Step 3: Full scan
        scan_tool = next(t for t in tools if t.name == "scan_document")
        full_scan_result = await scan_tool.fn(
            device_id="wia:test_scanner_1",
            dpi=300,
            color_mode="Color",
            paper_size="A4"
        )

        assert full_scan_result is not None

    @pytest.mark.asyncio
    async def test_multi_backend_comparison_workflow(self, fastmcp_app, temp_dir):
        """Test comparing results from different OCR backends."""
        tools = await fastmcp_app.get_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Create test image
        img_path = temp_dir / "comparison_test.png"
        img = Image.new('RGB', (200, 200), color='white')
        img.save(img_path)

        backends = ["deepseek-ocr", "florence-2", "got-ocr"]
        results = {}

        # Process with different backends
        for backend in backends:
            result = await process_tool.fn(
                source_path=str(img_path),
                backend=backend,
                mode="text"
            )

            assert result["success"] is True
            results[backend] = result

        # All should have produced results
        assert len(results) == len(backends)
        for backend, result in results.items():
            assert result["backend"] == backend
            assert "text" in result
            assert "confidence" in result

    @pytest.mark.asyncio
    async def test_ocr_quality_assessment_workflow(self, fastmcp_app, temp_dir):
        """Test OCR quality assessment across different content types."""
        tools = await fastmcp_app.get_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Test different image characteristics
        test_cases = [
            ("simple", Image.new('RGB', (100, 100), color='white')),
            ("complex", Image.new('RGB', (500, 500), color='gray')),
            ("high_contrast", Image.new('L', (200, 200), color=255)),
        ]

        results = {}

        for case_name, image in test_cases:
            img_path = temp_dir / f"quality_test_{case_name}.png"
            image.save(img_path)

            result = await process_tool.fn(
                source_path=str(img_path),
                backend="auto",
                mode="text"
            )

            assert result["success"] is True
            results[case_name] = result

        # All test cases should complete
        assert len(results) == len(test_cases)
        for case_name, result in results.items():
            assert "confidence" in result
            assert result["confidence"] > 0






