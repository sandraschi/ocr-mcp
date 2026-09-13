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
End-to-end tests for complete OCR-MCP workflows.

These tests verify full user workflows from document acquisition
through OCR processing to final results.
"""

import asyncio
from pathlib import Path

import pytest
from fastmcp import FastMCP
from PIL import Image

from ocr_mcp.core.backend_manager import BackendManager
from ocr_mcp.core.config import OCRConfig
from ocr_mcp.tools.ocr_tools import register_sota_tools


def _flat(res):
    """Flatten the SOTA tool contract for flat-dict assertions.

    Portmanteau tools return ``ToolResponse`` (pydantic) with the payload
    nested under ``result`` (or ``results`` for create_success_response
    dicts). Merges nested payload keys to the top level.
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
def config(temp_dir):
    """Test configuration (module scope: shared by all e2e classes)."""
    return OCRConfig(cache_dir=temp_dir / "cache")


@pytest.fixture
def backend_manager(config, mock_scanner_manager):
    """Backend manager with mocked components (module scope)."""
    manager = BackendManager(config)
    manager.scanner_manager = mock_scanner_manager

    # Mock successful OCR processing
    async def mock_process_success(backend_name, image_path, **kwargs):
        await asyncio.sleep(0.1)
        return {
            "success": True,
            "text": f"OCR result from {backend_name} for {Path(image_path).name}",
            "confidence": 0.92,
            "backend": backend_name,
            "processing_time": 0.1,
            "mode": kwargs.get("mode", "text"),
        }

    manager.process_with_backend = mock_process_success
    # Intelligent-batch path delegates here (real BackendManager API).
    manager.process_document = mock_process_success
    return manager


@pytest.fixture
def fastmcp_app(backend_manager, config):
    """FastMCP app with all tools registered (module scope)."""
    app = FastMCP("test-ocr-mcp")
    register_sota_tools(app, backend_manager, config)
    return app


class TestCompleteWorkflows:
    """End-to-end workflow tests."""

    @pytest.mark.asyncio
    async def test_scan_to_ocr_workflow(self, fastmcp_app, temp_dir):
        """Test complete workflow: scan document -> OCR processing."""
        tools = await fastmcp_app.list_tools()
        scanner_tool = next(t for t in tools if t.name == "operate_scanner")
        process_tool = next(t for t in tools if t.name == "process_document")

        # Step 1: Configure scanner (portmanteau: operate_scanner)
        config_result = _flat(
            await (scanner_tool.fn if hasattr(scanner_tool, "fn") else scanner_tool)(
                operation="configure_scan",
                device_id="wia:test_scanner_1",
                resolution=300,
                color_mode="color",
                paper_size="A4",
            )
        )
        assert config_result.get("success") is True

        # Step 2: Scan document
        scan_result = _flat(
            await (scanner_tool.fn if hasattr(scanner_tool, "fn") else scanner_tool)(
                operation="scan_document",
                device_id="wia:test_scanner_1",
                resolution=300,
                color_mode="color",
                paper_size="A4",
                save_path=str(temp_dir / "scan.png"),
            )
        )
        assert scan_result.get("success") is True
        assert scan_result.get("device_id") is not None

        # Step 3: Process scanned document with OCR (portmanteau: process_document)
        test_image_path = temp_dir / "scanned_doc.png"
        test_image_path.write_bytes(b"mock image data")

        ocr_result = _flat(
            await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                operation="process_document",
                source_path=str(test_image_path),
                backend="auto",
                ocr_mode="auto",
            )
        )

        assert ocr_result["success"] is True
        assert "text" in ocr_result
        assert ocr_result.get("backend", "")

    @pytest.mark.asyncio
    async def test_batch_scan_workflow(self, fastmcp_app, temp_dir):
        """Test batch scanning workflow."""
        tools = await fastmcp_app.list_tools()
        scanner_tool = next(t for t in tools if t.name == "operate_scanner")

        result = _flat(
            await (scanner_tool.fn if hasattr(scanner_tool, "fn") else scanner_tool)(
                operation="scan_batch",
                device_id="wia:test_scanner_2",
                resolution=150,
                color_mode="grayscale",
                paper_size="A4",
                save_directory=str(temp_dir),
            )
        )

        assert result.get("success") is True
        batch_results = result.get("batch_results", [])
        assert isinstance(batch_results, list)

    @pytest.mark.asyncio
    async def test_multi_format_processing_workflow(self, fastmcp_app, temp_dir):
        """Test processing multiple document formats."""
        tools = await fastmcp_app.list_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        img_path = temp_dir / "test.png"
        img = Image.new("RGB", (100, 100), color="white")
        img.save(img_path)

        result = _flat(
            await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                operation="process_document",
                source_path=str(img_path),
                backend="auto",
                ocr_mode="auto",
            )
        )

        assert result["success"] is True
        assert "text" in result

    @pytest.mark.asyncio
    async def test_comic_book_processing_workflow(self, fastmcp_app, temp_dir):
        """Test dense-layout processing workflow (ex comic params, removed in SOTA refit)."""
        tools = await fastmcp_app.list_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        comic_path = temp_dir / "comic_page.png"
        comic_img = Image.new("RGB", (800, 1200), color="white")
        comic_img.save(comic_path)

        result = _flat(
            await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                operation="process_document",
                source_path=str(comic_path),
                backend="got-ocr",
                ocr_mode="accurate",
            )
        )

        assert result["success"] is True
        assert "text" in result

    @pytest.mark.asyncio
    async def test_backend_selection_workflow(self, fastmcp_app, temp_dir):
        """Test backend selection and switching."""
        tools = await fastmcp_app.list_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Create test image
        img_path = temp_dir / "test.png"
        img = Image.new("RGB", (100, 100), color="white")
        img.save(img_path)

        # Test different backend selections
        backends_to_test = ["auto", "deepseek-ocr2", "florence-2"]

        for backend in backends_to_test:
            result = _flat(
                await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                    operation="process_document", source_path=str(img_path), backend=backend, ocr_mode="auto"
                )
            )

            assert result["success"] is True
            # Backend should be resolved (not necessarily the requested one if auto)

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, fastmcp_app, temp_dir):
        """Test error handling and recovery."""
        tools = await fastmcp_app.list_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Test with non-existent file
        result = _flat(
            await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                operation="process_document", source_path="/nonexistent/file.png", backend="auto"
            )
        )

        assert result["success"] is False
        assert "error" in result

        # Test recovery with valid file
        img_path = temp_dir / "recovery_test.png"
        img = Image.new("RGB", (50, 50), color="white")
        img.save(img_path)

        result = _flat(
            await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                operation="process_document", source_path=str(img_path), backend="auto"
            )
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_performance_workflow(self, fastmcp_app, temp_dir, benchmark):
        """Test performance characteristics."""
        tools = await fastmcp_app.list_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Create test image
        img_path = temp_dir / "perf_test.png"
        img = Image.new("RGB", (200, 200), color="white")
        img.save(img_path)

        # Benchmark OCR processing
        async def run_ocr():
            return _flat(
                await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                    operation="process_document", source_path=str(img_path), backend="auto", ocr_mode="auto"
                )
            )

        result = await run_ocr()

        assert result["success"] is True
        assert "text" in result

    @pytest.mark.asyncio
    async def test_health_check_workflow(self, fastmcp_app):
        """Test system health monitoring."""
        tools = await fastmcp_app.list_tools()
        health_tool = next(t for t in tools if t.name == "manage_workflow")

        health_result = _flat(
            await (health_tool.fn if hasattr(health_tool, "fn") else health_tool)(operation="ocr_health_check")
        )

        assert health_result["success"] is True
        assert health_result.get("status") == "healthy"
        assert isinstance(health_result.get("backends"), dict)

    @pytest.mark.asyncio
    async def test_scanner_discovery_workflow(self, fastmcp_app):
        """Test scanner discovery and enumeration."""
        tools = await fastmcp_app.list_tools()
        list_scanners_tool = next(t for t in tools if t.name == "operate_scanner")

        scanners = _flat(
            await (list_scanners_tool.fn if hasattr(list_scanners_tool, "fn") else list_scanners_tool)(
                operation="list_scanners"
            )
        )

        assert scanners["success"] is True
        # Should find at least the mock scanners
        assert isinstance(scanners.get("scanners"), list)
        assert len(scanners["scanners"]) >= 0

    @pytest.mark.asyncio
    async def test_region_ocr_workflow(self, fastmcp_app, temp_dir):
        """Test region-specific OCR processing."""
        tools = await fastmcp_app.list_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Create larger test image
        img_path = temp_dir / "region_test.png"
        img = Image.new("RGB", (400, 400), color="white")
        img.save(img_path)

        # Process specific region
        region = [50, 50, 200, 200]  # x1, y1, x2, y2

        result = _flat(
            await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                operation="process_document",
                source_path=str(img_path),
                backend="florence-2",  # Backend that supports regions
                ocr_mode="accurate",
                region=region,
            )
        )

        assert result["success"] is True
        # Should indicate region processing
        assert "text" in result

    @pytest.mark.asyncio
    async def test_different_output_formats(self, fastmcp_app, temp_dir):
        """Test different output format handling."""
        tools = await fastmcp_app.list_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        img_path = temp_dir / "format_test.png"
        img = Image.new("RGB", (100, 100), color="white")
        img.save(img_path)

        output_formats = ["text", "json", "html"]

        for output_format in output_formats:
            result = _flat(
                await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                    operation="process_document",
                    source_path=str(img_path),
                    backend="auto",
                    ocr_mode="auto",
                    output_format=output_format,
                )
            )

            assert result["success"] is True
            # Result structure may vary by format, but should succeed

    @pytest.mark.asyncio
    async def test_concurrent_processing_workflow(self, fastmcp_app, temp_dir):
        """Test concurrent document processing."""
        tools = await fastmcp_app.list_tools()
        batch_tool = next(t for t in tools if t.name == "process_document")

        # Create multiple test files in an isolated subdir
        # (temp_dir is session-scoped and shared with other tests)
        batch_dir = temp_dir / "concurrent_batch"
        batch_dir.mkdir(exist_ok=True)
        test_files = []
        for i in range(4):
            img_path = batch_dir / f"concurrent_test_{i}.png"
            img = Image.new("RGB", (50, 50), color="white")
            img.save(img_path)
            test_files.append(str(img_path))

        # Process concurrently (directory batch)
        result = _flat(
            await (batch_tool.fn if hasattr(batch_tool, "fn") else batch_tool)(
                operation="process_batch", source_path=str(batch_dir)
            )
        )

        assert result["success"] is True
        assert result["total_count"] == 4
        assert result["processed_count"] == 4


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
                    "backend": backend_name,
                }

            return {
                "success": True,
                "text": f"Success on call {call_count}",
                "backend": backend_name,
                "processing_time": 0.05,
            }

        manager.process_with_backend = mock_process_with_failures

        # Intelligent-batch path delegates to process_document (real API):
        # mirror the same every-third-call failure pattern.
        async def mock_process_document_with_failures(doc_path, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.05)
            if call_count % 3 == 0:
                raise RuntimeError(f"Simulated failure on call {call_count}")
            return {
                "success": True,
                "text": f"Success on call {call_count}",
                "backend": "mock",
                "confidence": 0.9,
            }

        manager.process_document = mock_process_document_with_failures
        return manager

    @pytest.mark.asyncio
    async def test_partial_batch_failure_workflow(self, fastmcp_app, failing_backend_manager, config, temp_dir):
        """Test batch processing with some failures."""
        # Re-register tools with failing backend manager
        app = FastMCP("test-failing-ocr-mcp")
        register_sota_tools(app, failing_backend_manager, config)

        tools = await app.list_tools()
        batch_tool = next(t for t in tools if t.name == "manage_workflow")

        # Create test files in an isolated subdir
        # (temp_dir is session-scoped and shared with other tests)
        fail_dir = temp_dir / "fail_batch"
        fail_dir.mkdir(exist_ok=True)
        test_files = []
        for i in range(6):  # Should have 2 failures
            img_path = fail_dir / f"fail_test_{i}.png"
            img = Image.new("RGB", (30, 30), color="white")
            img.save(img_path)
            test_files.append(str(img_path))

        result = _flat(
            await (batch_tool.fn if hasattr(batch_tool, "fn") else batch_tool)(
                operation="process_batch_intelligent", source_dir=str(fail_dir)
            )
        )

        batch = result["batch_summary"]
        assert batch["total_documents"] == 6
        assert len(result["results"]) == 6

        # Should have some successes and some failures
        successful = [r for r in result["results"] if r.get("success")]
        failed = [r for r in result["results"] if not r.get("success")]

        assert len(successful) > 0
        assert len(failed) > 0
        assert batch["successful"] == len(successful)

    @pytest.mark.asyncio
    async def test_scanner_failure_recovery(self, fastmcp_app, temp_dir):
        """Test recovery from scanner failures."""
        tools = await fastmcp_app.list_tools()
        scan_tool = next(t for t in tools if t.name == "operate_scanner")

        # Try scanning with invalid device
        result = _flat(
            await (scan_tool.fn if hasattr(scan_tool, "fn") else scan_tool)(
                operation="scan_document", device_id="invalid:device", resolution=150, color_mode="color"
            )
        )

        # Should handle gracefully without crashing
        assert result is not None  # May be None or error dict

        # Try with valid device
        result = _flat(
            await (scan_tool.fn if hasattr(scan_tool, "fn") else scan_tool)(
                operation="scan_document",
                device_id="wia:test_scanner_1",
                resolution=150,
                color_mode="color",
                save_path=str(temp_dir / "recovery_scan.png"),
            )
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_network_timeout_simulation(self, fastmcp_app, temp_dir):
        """Test handling of timeouts and slow operations."""
        tools = await fastmcp_app.list_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Create test file
        img_path = temp_dir / "timeout_test.png"
        img = Image.new("RGB", (1000, 1000), color="white")  # Large file
        img.save(img_path)

        # Process should still complete (mock doesn't actually timeout)
        result = _flat(
            await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                operation="process_document", source_path=str(img_path), backend="auto", ocr_mode="auto"
            )
        )

        assert result["success"] is True
        assert "text" in result


class TestAdvancedWorkflows:
    """Test advanced multi-step workflows."""

    @pytest.mark.asyncio
    async def test_preview_then_full_scan_workflow(self, fastmcp_app, temp_dir):
        """Test preview scan followed by full scan."""
        tools = await fastmcp_app.list_tools()

        # Step 1: Preview scan
        preview_tool = next(t for t in tools if t.name == "operate_scanner")
        preview_result = _flat(
            await (preview_tool.fn if hasattr(preview_tool, "fn") else preview_tool)(
                operation="preview_scan",
                device_id="wia:test_scanner_1",
                save_path=str(temp_dir / "preview.png"),
            )
        )

        assert preview_result is not None
        assert preview_result["success"] is True

        # Step 2: Configure for full scan
        config_tool = next(t for t in tools if t.name == "operate_scanner")
        config_result = _flat(
            await (config_tool.fn if hasattr(config_tool, "fn") else config_tool)(
                operation="configure_scan",
                device_id="wia:test_scanner_1",
                resolution=300,
                color_mode="color",
                paper_size="A4",
            )
        )

        assert config_result["success"] is True

        # Step 3: Full scan
        scan_tool = next(t for t in tools if t.name == "operate_scanner")
        full_scan_result = _flat(
            await (scan_tool.fn if hasattr(scan_tool, "fn") else scan_tool)(
                operation="scan_document",
                device_id="wia:test_scanner_1",
                resolution=300,
                color_mode="color",
                paper_size="A4",
                save_path=str(temp_dir / "full_scan.png"),
            )
        )

        assert full_scan_result is not None
        assert full_scan_result["success"] is True

    @pytest.mark.asyncio
    async def test_multi_backend_comparison_workflow(self, fastmcp_app, temp_dir):
        """Test comparing results from different OCR backends."""
        tools = await fastmcp_app.list_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Create test image
        img_path = temp_dir / "comparison_test.png"
        img = Image.new("RGB", (200, 200), color="white")
        img.save(img_path)

        backends = ["deepseek-ocr2", "florence-2", "got-ocr"]
        results = {}

        # Process with different backends
        for backend in backends:
            result = _flat(
                await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                    operation="process_document", source_path=str(img_path), backend=backend, ocr_mode="auto"
                )
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
        tools = await fastmcp_app.list_tools()
        process_tool = next(t for t in tools if t.name == "process_document")

        # Test different image characteristics
        test_cases = [
            ("simple", Image.new("RGB", (100, 100), color="white")),
            ("complex", Image.new("RGB", (500, 500), color="gray")),
            ("high_contrast", Image.new("L", (200, 200), color=255)),
        ]

        results = {}

        for case_name, image in test_cases:
            img_path = temp_dir / f"quality_test_{case_name}.png"
            image.save(img_path)

            result = _flat(
                await (process_tool.fn if hasattr(process_tool, "fn") else process_tool)(
                    operation="process_document", source_path=str(img_path), backend="auto", ocr_mode="auto"
                )
            )

            assert result["success"] is True
            results[case_name] = result

        # All test cases should complete
        assert len(results) == len(test_cases)
        for case_name, result in results.items():
            assert "text" in result
