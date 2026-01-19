"""
OCR-MCP Test Helpers and Utilities

Comprehensive testing utilities for OCR-MCP test suite.
"""

import asyncio
import tempfile
import time
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont


class TestDataGenerator:
    """Generate realistic test data for OCR testing."""

    @staticmethod
    def create_test_image(
        width: int = 800,
        height: int = 600,
        background_color: str = "white",
        text: str = "Sample OCR Test Text",
        font_size: int = 24,
        text_color: str = "black",
        format: str = "PNG",
    ) -> Image.Image:
        """Create a test image with text for OCR testing."""
        # Create image
        img = Image.new("RGB", (width, height), color=background_color)
        draw = ImageDraw.Draw(img)

        try:
            # Try to use a system font
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            # Fallback to default font
            font = ImageFont.load_default()

        # Calculate text position (centered)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2

        # Draw text
        draw.text((x, y), text, fill=text_color, font=font)

        return img

    @staticmethod
    def create_complex_document_image(
        pages: int = 1,
        include_tables: bool = True,
        include_headers: bool = True,
        include_images: bool = True,
    ) -> list[Image.Image]:
        """Create complex document images for testing."""
        images = []

        for page_num in range(pages):
            # Create base image
            img = Image.new("RGB", (1000, 1400), color="white")
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype("arial.ttf", 20)
                header_font = ImageFont.truetype("arial.ttf", 24)
            except OSError:
                font = ImageFont.load_default()
                header_font = ImageFont.load_default()

            y_offset = 50

            if include_headers:
                # Add header
                header_text = f"Document Page {page_num + 1}"
                draw.text((50, y_offset), header_text, fill="black", font=header_font)
                y_offset += 60

            # Add paragraphs of text
            paragraphs = [
                "This is a sample document for OCR testing purposes.",
                "It contains various types of content including text,",
                "tables, and potentially images to test OCR accuracy.",
                "The goal is to evaluate how well different OCR engines",
                "can extract and preserve document structure and content.",
            ]

            for para in paragraphs:
                draw.text((50, y_offset), para, fill="black", font=font)
                y_offset += 40

            if include_tables:
                # Add a simple table
                table_data = [
                    ["Item", "Quantity", "Price", "Total"],
                    ["Widget A", "10", "$5.00", "$50.00"],
                    ["Widget B", "5", "$8.50", "$42.50"],
                    ["Widget C", "2", "$12.00", "$24.00"],
                ]

                y_offset += 40
                table_start_y = y_offset

                # Draw table
                for i, row in enumerate(table_data):
                    for j, cell in enumerate(row):
                        x = 50 + j * 150
                        y = y_offset + i * 30

                        # Draw cell border
                        draw.rectangle([x, y, x + 140, y + 25], outline="black", width=1)

                        # Draw cell text
                        draw.text((x + 5, y + 2), cell, fill="black", font=font)

                y_offset += len(table_data) * 30 + 40

            # Add footer
            footer_text = f"Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}"
            draw.text((50, img.height - 50), footer_text, fill="gray", font=font)

            images.append(img)

        return images

    @staticmethod
    def create_test_pdf(
        output_path: Path, pages: int = 1, content: str = "Sample PDF content for testing."
    ) -> Path:
        """Create a simple test PDF file."""
        # For now, create a text file as placeholder
        # In production, would use reportlab or similar
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"PDF Content ({pages} pages):\n{content}")

        return output_path

    @staticmethod
    def create_test_cbz(
        output_path: Path, pages: int = 3, content: str = "Sample comic content"
    ) -> Path:
        """Create a simple test CBZ file."""
        # For now, create a text file as placeholder
        # In production, would create actual CBZ archive
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"CBZ Archive ({pages} pages):\n{content}")

        return output_path


class MockBackendFactory:
    """Factory for creating comprehensive mock OCR backends."""

    @staticmethod
    def create_mock_backend(
        name: str,
        available: bool = True,
        capabilities: dict[str, Any] | None = None,
        process_behavior: str | None = "success",
    ) -> Mock:
        """Create a comprehensive mock backend."""

        mock_backend = Mock()
        mock_backend.name = name
        mock_backend.is_available.return_value = available

        # Default capabilities
        default_capabilities = {
            "name": name,
            "available": available,
            "modes": ["text", "formatted"],
            "languages": ["en"],
            "gpu_support": False,
            "model_size": "base",
            "processing_speed": "fast",
            "accuracy": 0.85,
        }

        if capabilities:
            default_capabilities.update(capabilities)

        mock_backend.get_capabilities.return_value = default_capabilities

        # Configure processing behavior
        if process_behavior == "success":
            mock_backend.process_image = AsyncMock(
                return_value={
                    "success": True,
                    "text": f"Mock OCR result from {name}",
                    "confidence": 0.85,
                    "backend": name,
                    "processing_time": 0.5,
                }
            )
        elif process_behavior == "failure":
            mock_backend.process_image = AsyncMock(
                side_effect=Exception(f"{name} processing failed")
            )
        elif process_behavior == "timeout":

            async def timeout_process(*args, **kwargs):
                await asyncio.sleep(30)  # Simulate timeout
                return {"success": False, "error": "Timeout"}

            mock_backend.process_image = AsyncMock(side_effect=timeout_process)

        return mock_backend

    @staticmethod
    def create_backend_suite() -> dict[str, Mock]:
        """Create a complete suite of mock backends."""
        backends = {}

        backend_configs = [
            ("deepseek-ocr", {"gpu_support": True, "accuracy": 0.92, "processing_speed": "medium"}),
            ("florence-2", {"gpu_support": True, "accuracy": 0.89, "processing_speed": "fast"}),
            ("dots-ocr", {"gpu_support": False, "accuracy": 0.87, "processing_speed": "fast"}),
            ("pp-ocrv5", {"gpu_support": True, "accuracy": 0.86, "processing_speed": "fast"}),
            ("qwen-layered", {"gpu_support": True, "accuracy": 0.88, "processing_speed": "slow"}),
            ("got-ocr", {"gpu_support": True, "accuracy": 0.85, "processing_speed": "medium"}),
            ("tesseract", {"gpu_support": False, "accuracy": 0.78, "processing_speed": "fast"}),
            ("easyocr", {"gpu_support": True, "accuracy": 0.82, "processing_speed": "medium"}),
        ]

        for name, capabilities in backend_configs:
            backends[name] = MockBackendFactory.create_mock_backend(name, capabilities=capabilities)

        return backends


class PerformanceProfiler:
    """Performance profiling utilities for tests."""

    def __init__(self):
        self.start_time = None
        self.measurements = []

    def start(self):
        """Start performance measurement."""
        self.start_time = time.perf_counter()

    def stop(self, operation: str = "operation") -> float:
        """Stop measurement and return elapsed time."""
        if self.start_time is None:
            return 0.0

        elapsed = time.perf_counter() - self.start_time
        self.measurements.append({"operation": operation, "time": elapsed})
        self.start_time = None
        return elapsed

    def get_stats(self) -> dict[str, Any]:
        """Get performance statistics."""
        if not self.measurements:
            return {}

        times = [m["time"] for m in self.measurements]
        return {
            "count": len(times),
            "total": sum(times),
            "average": np.mean(times),
            "median": np.median(times),
            "min": min(times),
            "max": max(times),
            "std_dev": np.std(times),
        }


class TestFileManager:
    """Manage test files and cleanup."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path(tempfile.mkdtemp(prefix="ocr_test_"))
        self.created_files = []

    def create_temp_file(
        self, content: str | bytes, suffix: str = ".txt", encoding: str = "utf-8"
    ) -> Path:
        """Create a temporary file and track it for cleanup."""
        file_path = self.base_dir / f"test_{len(self.created_files)}{suffix}"

        if isinstance(content, str):
            file_path.write_text(content, encoding=encoding)
        else:
            file_path.write_bytes(content)

        self.created_files.append(file_path)
        return file_path

    def create_temp_image(self, image: Image.Image, format: str = "PNG") -> Path:
        """Create a temporary image file."""
        suffix = f".{format.lower()}"
        file_path = self.base_dir / f"test_img_{len(self.created_files)}{suffix}"
        image.save(file_path, format=format)
        self.created_files.append(file_path)
        return file_path

    def cleanup(self):
        """Clean up all created files."""
        for file_path in self.created_files:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception:
                pass  # Ignore cleanup errors

        self.created_files.clear()


class AsyncTestHelper:
    """Helpers for async testing."""

    @staticmethod
    async def wait_for_condition(
        condition_func, timeout: float = 5.0, interval: float = 0.1
    ) -> bool:
        """Wait for a condition to become true."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if condition_func():
                return True
            await asyncio.sleep(interval)

        return False

    @staticmethod
    async def run_with_timeout(
        coro, timeout: float = 10.0, timeout_message: str = "Operation timed out"
    ):
        """Run a coroutine with timeout."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except TimeoutError:
            raise TimeoutError(timeout_message)


class TestDataValidator:
    """Validate test data and results."""

    @staticmethod
    def validate_ocr_result(result: dict[str, Any]) -> bool:
        """Validate OCR result structure."""
        required_fields = ["success", "text", "confidence", "backend"]
        return all(field in result for field in required_fields)

    @staticmethod
    def validate_image_file(file_path: Path) -> bool:
        """Validate that file is a valid image."""
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception:
            return False

    @staticmethod
    def validate_pdf_file(file_path: Path) -> bool:
        """Validate that file appears to be a PDF."""
        try:
            with open(file_path, "rb") as f:
                header = f.read(4)
            return header == b"%PDF"
        except Exception:
            return False


class MockServerManager:
    """Mock server management for integration tests."""

    def __init__(self):
        self.server_process = None
        self.is_running = False

    async def start_server(self, port: int = 15550) -> bool:
        """Start mock OCR-MCP server."""
        # In real implementation, would start actual server
        self.is_running = True
        return True

    async def stop_server(self) -> bool:
        """Stop mock server."""
        if self.server_process:
            # Kill process
            pass
        self.is_running = False
        return True

    def is_server_responding(self, port: int = 15550) -> bool:
        """Check if server is responding."""
        return self.is_running


# Convenience fixtures for common test scenarios
@pytest.fixture
def test_data_generator():
    """Fixture for test data generator."""
    return TestDataGenerator()


@pytest.fixture
def performance_profiler():
    """Fixture for performance profiling."""
    return PerformanceProfiler()


@pytest.fixture
def test_file_manager():
    """Fixture for test file management."""
    manager = TestFileManager()
    yield manager
    manager.cleanup()


@pytest.fixture
def mock_server_manager():
    """Fixture for mock server management."""
    manager = MockServerManager()
    yield manager
    asyncio.run(manager.stop_server())


@pytest.fixture
def async_helper():
    """Fixture for async test helpers."""
    return AsyncTestHelper()


@pytest.fixture
def data_validator():
    """Fixture for data validation."""
    return TestDataValidator()


# Common test data fixtures
@pytest.fixture
def sample_document_text():
    """Sample document text for testing."""
    return """
    INVOICE

    Invoice Number: INV-2025-001
    Date: January 18, 2026
    Customer: Test Company Inc.

    Item                    Quantity    Unit Price    Total
    Widget A                10          $5.00        $50.00
    Widget B                5           $8.50        $42.50
    Widget C                2           $12.00       $24.00

    Subtotal: $114.50
    Tax (8%): $9.16
    Total: $123.66

    Thank you for your business!
    """


@pytest.fixture
def sample_table_data():
    """Sample table data for testing."""
    return [
        ["Product", "Price", "Quantity", "Total"],
        ["Laptop", "$999.99", "1", "$999.99"],
        ["Mouse", "$25.99", "2", "$51.98"],
        ["Keyboard", "$79.99", "1", "$79.99"],
    ]


@pytest.fixture
def complex_document_content():
    """Complex document content with various elements."""
    return {
        "title": "Annual Report 2025",
        "sections": [
            {
                "heading": "Executive Summary",
                "content": "This report summarizes the company's performance...",
                "type": "text",
            },
            {
                "heading": "Financial Results",
                "content": "Revenue increased by 15% year-over-year...",
                "type": "text",
            },
            {
                "heading": "Sales by Region",
                "data": [
                    ["Region", "Q1", "Q2", "Q3", "Q4"],
                    ["North America", "$1.2M", "$1.5M", "$1.8M", "$2.1M"],
                    ["Europe", "$800K", "$950K", "$1.1M", "$1.3M"],
                    ["Asia Pacific", "$600K", "$750K", "$900K", "$1.0M"],
                ],
                "type": "table",
            },
        ],
    }
