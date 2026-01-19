"""
OCR Performance Testing Suite

Comprehensive performance benchmarks for OCR-MCP backends.
Tests throughput, latency, memory usage, and scalability.
"""

import asyncio
import time
from typing import Any

import numpy as np
import pytest


class TestOCRPerformance:
    """Performance tests for OCR operations."""

    @pytest.mark.performance
    @pytest.mark.parametrize("backend_name", ["deepseek-ocr", "florence-2", "tesseract"])
    def test_single_document_processing_speed(
        self, backend_manager_with_mocks, sample_image_path, performance_monitor, backend_name
    ):
        """Test processing speed for single documents across backends."""
        backend = backend_manager_with_mocks.get_backend(backend_name)
        assert backend and backend.is_available()

        performance_monitor.start()

        # Process document
        result = asyncio.run(
            backend_manager_with_mocks.process_with_backend(
                backend_name, str(sample_image_path), mode="text"
            )
        )

        elapsed = performance_monitor.stop(f"{backend_name}_single_doc")

        # Assertions
        assert result["success"] is True
        assert result["backend_used"] == backend_name
        assert elapsed < 5.0  # Should complete within 5 seconds
        assert "text" in result

    @pytest.mark.performance
    def test_batch_processing_throughput(
        self, backend_manager_with_mocks, file_manager, test_data_generator, performance_monitor
    ):
        """Test batch processing throughput and scalability."""
        # Create multiple test images
        test_images = []
        for i in range(10):
            img = test_data_generator.create_test_image(
                text=f"Batch test document {i + 1}", width=800, height=600
            )
            img_path = file_manager.create_temp_image(img)
            test_images.append(str(img_path))

        performance_monitor.start()

        # Process batch
        results = []
        for img_path in test_images:
            result = asyncio.run(
                backend_manager_with_mocks.process_with_backend("auto", img_path, mode="text")
            )
            results.append(result)

        elapsed = performance_monitor.stop("batch_processing_10_docs")

        # Assertions
        successful = sum(1 for r in results if r.get("success"))
        success_rate = successful / len(results)

        assert success_rate >= 0.9  # At least 90% success rate
        assert elapsed < 30.0  # Should complete within 30 seconds
        assert len(results) == 10

        # Calculate throughput
        throughput = len(results) / elapsed  # documents per second
        assert throughput >= 0.2  # At least 0.2 docs/second

    @pytest.mark.performance
    @pytest.mark.parametrize("concurrent_jobs", [1, 2, 4, 8])
    def test_concurrent_processing_scalability(
        self,
        backend_manager_with_mocks,
        file_manager,
        test_data_generator,
        performance_monitor,
        concurrent_jobs,
    ):
        """Test how well the system scales with concurrent jobs."""
        # Create test images
        test_images = []
        for i in range(concurrent_jobs * 2):  # 2 jobs per concurrent worker
            img = test_data_generator.create_test_image(
                text=f"Concurrent test {i + 1}", width=600, height=400
            )
            img_path = file_manager.create_temp_image(img)
            test_images.append(str(img_path))

        async def process_single(image_path: str) -> dict[str, Any]:
            return await backend_manager_with_mocks.process_with_backend(
                "auto", image_path, mode="text"
            )

        async def process_batch_concurrent() -> list[dict[str, Any]]:
            tasks = [process_single(img_path) for img_path in test_images]
            return await asyncio.gather(*tasks)

        performance_monitor.start()
        results = asyncio.run(process_batch_concurrent())
        elapsed = performance_monitor.stop(f"concurrent_{concurrent_jobs}_jobs")

        # Assertions
        successful = sum(1 for r in results if r.get("success"))
        success_rate = successful / len(results)

        assert success_rate >= 0.8
        assert elapsed < 60.0  # Should complete within 1 minute

        # Check for performance degradation
        expected_time = len(test_images) * 2.0  # 2 seconds per document baseline
        efficiency = expected_time / elapsed

        # Efficiency should improve with concurrency (up to a point)
        if concurrent_jobs <= 4:
            assert efficiency >= 1.0  # At least baseline performance
        elif concurrent_jobs == 8:
            assert efficiency >= 0.8  # Allow some overhead for high concurrency

    @pytest.mark.performance
    def test_memory_usage_stability(
        self, backend_manager_with_mocks, file_manager, test_data_generator, performance_monitor
    ):
        """Test memory usage stability during prolonged operation."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process multiple documents in sequence
        memory_samples = []

        for i in range(20):
            img = test_data_generator.create_test_image(
                text=f"Memory test document {i + 1}", width=1000, height=800
            )
            img_path = file_manager.create_temp_image(img)

            result = asyncio.run(
                backend_manager_with_mocks.process_with_backend("auto", str(img_path), mode="text")
            )

            assert result["success"] is True

            # Sample memory usage
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)

        final_memory = memory_samples[-1]
        memory_increase = final_memory - initial_memory

        # Memory should not grow excessively
        assert memory_increase < 100  # Less than 100MB increase

        # Memory should stabilize (not continuously growing)
        recent_avg = np.mean(memory_samples[-5:])
        earlier_avg = np.mean(memory_samples[:5])
        memory_growth_rate = (recent_avg - earlier_avg) / earlier_avg

        assert abs(memory_growth_rate) < 0.1  # Less than 10% growth

    @pytest.mark.performance
    @pytest.mark.slow
    def test_long_running_stability(
        self, backend_manager_with_mocks, file_manager, test_data_generator, performance_monitor
    ):
        """Test system stability during long-running operations."""
        start_time = time.time()
        processed_count = 0
        error_count = 0

        # Run for 2 minutes or 100 documents, whichever comes first
        while (time.time() - start_time) < 120 and processed_count < 100:
            try:
                img = test_data_generator.create_test_image(
                    text=f"Stability test {processed_count + 1}", width=800, height=600
                )
                img_path = file_manager.create_temp_image(img)

                result = asyncio.run(
                    backend_manager_with_mocks.process_with_backend(
                        "auto", str(img_path), mode="text"
                    )
                )

                if result.get("success"):
                    processed_count += 1
                else:
                    error_count += 1

            except Exception:
                error_count += 1
                continue

        elapsed = time.time() - start_time

        # Assertions
        total_operations = processed_count + error_count
        success_rate = processed_count / total_operations if total_operations > 0 else 0

        assert success_rate >= 0.95  # 95% success rate
        assert processed_count >= 50  # At least 50 successful operations
        assert error_count < 5  # Less than 5 errors

        # Performance should be consistent
        ops_per_second = processed_count / elapsed
        assert ops_per_second >= 0.3  # At least 0.3 ops/second

    @pytest.mark.performance
    def test_backend_selection_performance(
        self, backend_manager_with_mocks, sample_image_path, performance_monitor
    ):
        """Test performance of intelligent backend selection."""
        # Test auto-selection performance
        performance_monitor.start()

        for _ in range(50):
            backend = backend_manager_with_mocks.select_backend("auto", sample_image_path)
            assert backend is not None

        elapsed = performance_monitor.stop("backend_selection_50_times")

        # Backend selection should be fast
        assert elapsed < 1.0  # Less than 1 second for 50 selections
        avg_time = elapsed / 50
        assert avg_time < 0.02  # Less than 20ms per selection

    @pytest.mark.performance
    @pytest.mark.parametrize("image_size", [(400, 300), (800, 600), (1600, 1200), (3200, 2400)])
    def test_image_size_scaling_performance(
        self,
        backend_manager_with_mocks,
        file_manager,
        test_data_generator,
        performance_monitor,
        image_size,
    ):
        """Test how processing time scales with image size."""
        width, height = image_size

        # Create test image of specified size
        img = test_data_generator.create_test_image(
            width=width, height=height, text=f"Size test {width}x{height}"
        )
        img_path = file_manager.create_temp_image(img)

        performance_monitor.start()

        result = asyncio.run(
            backend_manager_with_mocks.process_with_backend("auto", str(img_path), mode="text")
        )

        elapsed = performance_monitor.stop(f"size_{width}x{height}")

        assert result["success"] is True

        # Processing time should scale roughly with image size
        pixel_count = width * height
        time_per_pixel = elapsed / pixel_count

        # Time per pixel should be reasonable (not exponential growth)
        assert time_per_pixel < 1e-6  # Less than 1 microsecond per pixel

        # But should increase with size (linear or near-linear)
        if width >= 800:  # For larger images
            assert elapsed > 0.1  # Should take at least some time
