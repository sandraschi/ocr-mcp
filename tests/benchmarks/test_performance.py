"""
Performance benchmarks for OCR-MCP.

Tests processing speed, memory usage, and scalability across different
backends and document types.
"""

import pytest
import asyncio
import time
import psutil
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from src.ocr_mcp.core.config import OCRConfig
from src.ocr_mcp.core.backend_manager import BackendManager


class TestOCRPerformance:
    """Performance benchmarks for OCR processing."""

    @pytest.fixture
    def config(self, temp_dir):
        """Performance test configuration."""
        return OCRConfig(
            cache_dir=temp_dir / "perf_cache",
            device="cpu"  # Use CPU for consistent benchmarking
        )

    @pytest.fixture
    def backend_manager(self, config):
        """Backend manager for performance testing."""
        return BackendManager(config)

    @pytest.fixture
    def benchmark_images(self, temp_dir):
        """Create benchmark test images of different sizes and complexities."""
        images = {}

        sizes = [
            ("small", (200, 200)),
            ("medium", (800, 600)),
            ("large", (2000, 1500)),
            ("xlarge", (4000, 3000))
        ]

        for name, size in sizes:
            # Create base image
            img = Image.new('RGB', size, color='white')
            draw = ImageDraw.Draw(img)

            # Add some content to make OCR non-trivial
            try:
                # Try to use default font
                font = ImageFont.load_default()
            except:
                font = None

            # Add text at different positions
            text_positions = [
                (10, 10, "TEST DOCUMENT"),
                (size[0]//4, size[1]//4, "Benchmark OCR Text"),
                (size[0]//2, size[1]//2, "Performance Test"),
                (3*size[0]//4, 3*size[1]//4, "Quality Assessment")
            ]

            for x, y, text in text_positions:
                if font:
                    draw.text((x, y), text, fill='black', font=font)
                else:
                    draw.text((x, y), text, fill='black')

            # Save image
            img_path = temp_dir / f"benchmark_{name}.png"
            img.save(img_path, optimize=True)
            images[name] = img_path

        return images

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    @pytest.mark.benchmark
    @pytest.mark.parametrize("backend_name", ["deepseek-ocr", "florence-2", "got-ocr", "tesseract"])
    def test_backend_processing_speed(self, benchmark, backend_manager, benchmark_images, backend_name):
        """Benchmark OCR processing speed for different backends."""

        async def run_benchmark():
            results = {}
            for img_name, img_path in benchmark_images.items():
                start_time = time.time()
                initial_memory = self.get_memory_usage()

                result = await backend_manager.process_with_backend(
                    backend_name,
                    str(img_path),
                    mode="text"
                )

                end_time = time.time()
                final_memory = self.get_memory_usage()

                results[img_name] = {
                    "success": result.get("success", False),
                    "processing_time": result.get("processing_time", end_time - start_time),
                    "memory_delta": final_memory - initial_memory,
                    "image_size": img_path.stat().st_size
                }

            return results

        # Run benchmark
        results = asyncio.run(run_benchmark())

        # Validate results
        for img_name, metrics in results.items():
            assert metrics["success"], f"OCR failed for {img_name} with {backend_name}"
            assert metrics["processing_time"] > 0, "Processing time should be positive"
            assert metrics["processing_time"] < 30, f"Processing too slow: {metrics['processing_time']}s"

        # Store results for analysis
        benchmark.extra_info = {
            "backend": backend_name,
            "results": results
        }

    @pytest.mark.benchmark
    def test_batch_processing_performance(self, benchmark, backend_manager, benchmark_images):
        """Benchmark batch processing performance."""

        async def run_batch_benchmark():
            image_paths = [str(path) for path in benchmark_images.values()]

            start_time = time.time()
            initial_memory = self.get_memory_usage()

            # Process all images concurrently
            tasks = []
            for img_path in image_paths:
                task = backend_manager.process_with_backend(
                    "auto",
                    img_path,
                    mode="text"
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            end_time = time.time()
            final_memory = self.get_memory_usage()

            return {
                "total_time": end_time - start_time,
                "memory_delta": final_memory - initial_memory,
                "images_processed": len(image_paths),
                "results": results
            }

        results = asyncio.run(run_batch_benchmark())

        # Validate batch processing
        assert results["total_time"] > 0
        assert results["images_processed"] == len(benchmark_images)
        successful = [r for r in results["results"] if not isinstance(r, Exception) and r.get("success")]
        assert len(successful) > 0, "No images processed successfully"

        benchmark.extra_info = results

    @pytest.mark.benchmark
    @pytest.mark.parametrize("mode", ["text", "formatted", "fine-grained"])
    def test_mode_performance_comparison(self, benchmark, backend_manager, benchmark_images, mode):
        """Compare performance across different OCR modes."""

        async def run_mode_benchmark():
            img_path = str(benchmark_images["medium"])  # Use medium image

            results = {}
            for test_mode in ["text", "formatted", "fine-grained"]:
                start_time = time.time()
                result = await backend_manager.process_with_backend(
                    "auto",
                    img_path,
                    mode=test_mode
                )
                end_time = time.time()

                results[test_mode] = {
                    "success": result.get("success", False),
                    "processing_time": result.get("processing_time", end_time - start_time),
                    "mode": test_mode
                }

            return results

        results = asyncio.run(run_mode_benchmark())

        # Focus on the parameterized mode
        mode_result = results[mode]
        assert mode_result["success"], f"Mode {mode} processing failed"
        assert mode_result["processing_time"] > 0

        benchmark.extra_info = {
            "tested_mode": mode,
            "all_results": results
        }

    @pytest.mark.benchmark
    def test_memory_usage_scaling(self, benchmark, backend_manager, temp_dir):
        """Test memory usage scaling with document size."""

        async def run_memory_benchmark():
            memory_stats = {}

            # Test different image sizes
            sizes = [(200, 200), (500, 500), (1000, 1000), (2000, 2000)]

            for width, height in sizes:
                # Create test image
                img = Image.new('RGB', (width, height), color='white')
                img_path = temp_dir / f"memory_test_{width}x{height}.png"
                img.save(img_path)

                # Measure memory before
                memory_before = self.get_memory_usage()

                # Process image
                result = await backend_manager.process_with_backend(
                    "auto",
                    str(img_path),
                    mode="text"
                )

                # Measure memory after
                memory_after = self.get_memory_usage()

                memory_stats[f"{width}x{height}"] = {
                    "memory_before": memory_before,
                    "memory_after": memory_after,
                    "memory_delta": memory_after - memory_before,
                    "file_size": img_path.stat().st_size,
                    "success": result.get("success", False)
                }

                # Cleanup
                img_path.unlink()

            return memory_stats

        memory_stats = asyncio.run(run_memory_benchmark())

        # Validate memory scaling is reasonable
        for size, stats in memory_stats.items():
            assert stats["success"], f"Processing failed for {size}"
            assert stats["memory_delta"] < 500, f"Memory usage too high for {size}: {stats['memory_delta']}MB"

        benchmark.extra_info = memory_stats

    @pytest.mark.benchmark
    def test_concurrent_processing_limits(self, benchmark, backend_manager, temp_dir):
        """Test performance with different concurrency levels."""

        async def run_concurrency_benchmark():
            # Create multiple test images
            test_images = []
            for i in range(10):
                img = Image.new('RGB', (300, 300), color='white')
                img_path = temp_dir / f"concurrency_test_{i}.png"
                img.save(img_path)
                test_images.append(str(img_path))

            concurrency_levels = [1, 2, 4, 8]

            results = {}

            for concurrency in concurrency_levels:
                semaphore = asyncio.Semaphore(concurrency)

                async def process_with_semaphore(img_path):
                    async with semaphore:
                        return await backend_manager.process_with_backend(
                            "auto",
                            img_path,
                            mode="text"
                        )

                start_time = time.time()
                tasks = [process_with_semaphore(img) for img in test_images]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

                successful = [r for r in batch_results if not isinstance(r, Exception) and r.get("success")]

                results[f"concurrency_{concurrency}"] = {
                    "total_time": end_time - start_time,
                    "successful": len(successful),
                    "total": len(test_images),
                    "throughput": len(successful) / (end_time - start_time) if end_time > start_time else 0
                }

            # Cleanup
            for img_path in test_images:
                Path(img_path).unlink()

            return results

        concurrency_results = asyncio.run(run_concurrency_benchmark())

        # Validate concurrency scaling
        for level, stats in concurrency_results.items():
            assert stats["successful"] > 0, f"No successful processing at {level}"
            assert stats["throughput"] > 0, f"Zero throughput at {level}"

        benchmark.extra_info = concurrency_results


class TestScannerPerformance:
    """Performance benchmarks for scanner operations."""

    @pytest.fixture
    def mock_scanner_manager(self):
        """Mock scanner manager for performance testing."""
        from tests.mocks.mock_scanner import MockScannerManager
        return MockScannerManager()

    @pytest.mark.benchmark
    def test_scanner_discovery_speed(self, benchmark, mock_scanner_manager):
        """Benchmark scanner discovery performance."""

        def run_discovery():
            return mock_scanner_manager.discover_scanners()

        scanners = benchmark(run_discovery)

        assert len(scanners) >= 0
        benchmark.extra_info = {
            "scanners_found": len(scanners),
            "discovery_time": benchmark.stats["mean"]
        }

    @pytest.mark.benchmark
    def test_scan_configuration_speed(self, benchmark, mock_scanner_manager):
        """Benchmark scan configuration performance."""

        def run_configuration():
            return mock_scanner_manager.configure_scan(
                "wia:test_scanner_1",
                {
                    "dpi": 300,
                    "color_mode": "Color",
                    "paper_size": "A4",
                    "brightness": 0,
                    "contrast": 0
                }
            )

        result = benchmark(run_configuration)

        assert result is True
        benchmark.extra_info = {
            "configuration_time": benchmark.stats["mean"]
        }

    @pytest.mark.benchmark
    def test_document_scan_speed(self, benchmark, mock_scanner_manager):
        """Benchmark document scanning performance."""

        def run_scan():
            return mock_scanner_manager.scan_document(
                "wia:test_scanner_1",
                {
                    "dpi": 300,
                    "color_mode": "Color",
                    "paper_size": "A4"
                }
            )

        image = benchmark(run_scan)

        assert image is not None
        benchmark.extra_info = {
            "scan_time": benchmark.stats["mean"],
            "image_size": image.size if image else None
        }

    @pytest.mark.benchmark
    def test_batch_scan_performance(self, benchmark, mock_scanner_manager):
        """Benchmark batch scanning performance."""

        async def run_batch_scan():
            return await mock_scanner_manager.scan_batch(
                "wia:test_scanner_2",  # ADF scanner
                {
                    "dpi": 150,
                    "color_mode": "Grayscale",
                    "paper_size": "A4"
                },
                count=5
            )

        images = asyncio.run(run_batch_scan())

        benchmark.extra_info = {
            "images_scanned": len(images),
            "batch_time": benchmark.stats["mean"],
            "images_per_second": len(images) / benchmark.stats["mean"] if benchmark.stats["mean"] > 0 else 0
        }


class TestSystemPerformance:
    """System-level performance benchmarks."""

    @pytest.fixture
    def config(self, temp_dir):
        """System performance test configuration."""
        return OCRConfig(cache_dir=temp_dir / "system_cache")

    @pytest.mark.benchmark
    def test_backend_initialization_time(self, benchmark, config):
        """Benchmark backend manager initialization time."""

        def init_backend_manager():
            from src.ocr_mcp.core.backend_manager import BackendManager
            return BackendManager(config)

        manager = benchmark(init_backend_manager)

        assert manager is not None
        assert hasattr(manager, 'backends')
        benchmark.extra_info = {
            "backends_initialized": len(manager.backends),
            "init_time": benchmark.stats["mean"]
        }

    @pytest.mark.benchmark
    def test_tool_registration_performance(self, benchmark, config):
        """Benchmark MCP tool registration performance."""

        def register_tools():
            from fastmcp import FastMCP
            from src.ocr_mcp.core.backend_manager import BackendManager
            from src.ocr_mcp.tools.ocr_tools import register_ocr_tools
            from src.ocr_mcp.tools.scanner_tools import register_scanner_tools

            app = FastMCP("benchmark-ocr-mcp")
            manager = BackendManager(config)

            register_ocr_tools(app, manager, config)
            register_scanner_tools(app, manager, config)

            return app

        app = benchmark(register_tools)

        benchmark.extra_info = {
            "registration_time": benchmark.stats["mean"]
        }

    @pytest.mark.benchmark
    def test_server_startup_time(self, benchmark, config):
        """Benchmark server startup time."""

        async def start_server():
            from fastmcp import FastMCP
            from src.ocr_mcp.core.backend_manager import BackendManager
            from src.ocr_mcp.tools.ocr_tools import register_ocr_tools
            from src.ocr_mcp.tools.scanner_tools import register_scanner_tools

            app = FastMCP("benchmark-server")
            manager = BackendManager(config)

            register_ocr_tools(app, manager, config)
            register_scanner_tools(app, manager, config)

            # Simulate getting tools (startup operation)
            tools = await app.get_tools()
            return len(tools)

        tool_count = asyncio.run(start_server())

        benchmark.extra_info = {
            "startup_time": benchmark.stats["mean"],
            "tools_registered": tool_count
        }


# Performance assertion helpers
def assert_performance_threshold(benchmark_result, max_time: float, operation: str):
    """Assert that benchmark result meets performance threshold."""
    mean_time = benchmark_result.stats["mean"]
    assert mean_time < max_time, f"{operation} too slow: {mean_time:.2f}s (threshold: {max_time}s)"


def assert_memory_threshold(memory_delta: float, max_memory: float, operation: str):
    """Assert that memory usage meets threshold."""
    assert memory_delta < max_memory, f"{operation} memory usage too high: {memory_delta:.1f}MB (threshold: {max_memory}MB)"


def assert_throughput_threshold(throughput: float, min_throughput: float, operation: str):
    """Assert that throughput meets minimum threshold."""
    assert throughput >= min_throughput, f"{operation} throughput too low: {throughput:.1f} items/sec (minimum: {min_throughput})"






