"""
Unit tests for OCR-MCP backend implementations.
"""

import pytest

from tests.mocks.mock_backends import (
    MockDeepSeekBackend,
    MockFlorenceBackend,
    MockDOTSBackend,
    MockPPOCRBackend,
    MockQwenBackend,
    MockGOTBackend,
    MockTesseractBackend,
    MockEasyOCRBackend
)


class TestMockDeepSeekBackend:
    """Test cases for MockDeepSeekBackend."""

    @pytest.fixture
    def backend(self, config):
        return MockDeepSeekBackend(config)

    def test_initialization(self, backend, config):
        """Test backend initialization."""
        assert backend.name == "deepseek-ocr"
        assert backend.config == config
        assert backend.is_available()
        assert backend.call_count == 0

    @pytest.mark.asyncio
    async def test_process_image_text_mode(self, backend, sample_image_path):
        """Test OCR processing in text mode."""
        result = await backend.process_image(str(sample_image_path), mode="text")

        assert result["success"] is True
        assert "DeepSeek OCR result" in result["text"]
        assert result["confidence"] == 0.95
        assert result["backend"] == "deepseek-ocr"
        assert result["mode"] == "text"
        assert not result["gpu_used"]
        assert backend.call_count == 1

    @pytest.mark.asyncio
    async def test_process_image_formatted_mode(self, backend, sample_image_path):
        """Test OCR processing in formatted mode."""
        result = await backend.process_image(str(sample_image_path), mode="formatted")

        assert result["success"] is True
        assert "formatted" in result["mode"]
        assert "layout_analysis" in result
        assert "paragraphs" in result["layout_analysis"]
        assert backend.call_count == 1

    @pytest.mark.asyncio
    async def test_process_image_fine_grained_mode(self, backend, sample_image_path):
        """Test OCR processing in fine-grained mode."""
        result = await backend.process_image(str(sample_image_path), mode="fine-grained")

        assert result["success"] is True
        assert "fine-grained" in result["mode"]
        assert "regions" in result
        assert isinstance(result["regions"], list)
        assert backend.call_count == 1

    @pytest.mark.asyncio
    async def test_process_image_with_region(self, backend, sample_image_path):
        """Test OCR processing with region specification."""
        region = [10, 10, 200, 200]
        result = await backend.process_image(
            str(sample_image_path),
            mode="fine-grained",
            region=region
        )

        assert result["success"] is True
        assert backend.last_call_args == (str(sample_image_path), "fine-grained", {"region": region})

    def test_get_capabilities(self, backend):
        """Test backend capabilities."""
        capabilities = backend.get_capabilities()

        assert capabilities["name"] == "deepseek-ocr"
        assert capabilities["available"] is True
        assert "text" in capabilities["modes"]
        assert "formatted" in capabilities["modes"]
        assert "fine-grained" in capabilities["modes"]
        assert "en" in capabilities["languages"]
        assert "multilingual" in capabilities["languages"]
        assert not capabilities["gpu_support"]

    def test_call_tracking(self, backend, sample_image_path):
        """Test that backend tracks calls correctly."""
        initial_count = backend.call_count
        backend.process_image(str(sample_image_path))
        assert backend.call_count == initial_count + 1


class TestMockFlorenceBackend:
    """Test cases for MockFlorenceBackend."""

    @pytest.fixture
    def backend(self, config):
        return MockFlorenceBackend(config)

    def test_initialization(self, backend, config):
        """Test backend initialization."""
        assert backend.name == "florence-2"
        assert backend.is_available()

    @pytest.mark.asyncio
    async def test_process_image_basic(self, backend, sample_image_path):
        """Test basic OCR processing."""
        result = await backend.process_image(str(sample_image_path))

        assert result["success"] is True
        assert "Florence-2 OCR result" in result["text"]
        assert result["backend"] == "florence-2"

    @pytest.mark.asyncio
    async def test_process_image_with_region(self, backend, sample_image_path):
        """Test OCR with region specification."""
        region = [50, 50, 300, 300]
        result = await backend.process_image(
            str(sample_image_path),
            region=region
        )

        assert result["success"] is True
        assert result["region_ocr"] is True
        assert result["region_coords"] == region

    def test_get_capabilities(self, backend):
        """Test backend capabilities."""
        capabilities = backend.get_capabilities()

        assert capabilities["name"] == "florence-2"
        assert capabilities["available"] is True
        assert "Microsoft's Vision Foundation Model" in capabilities["description"]


class TestMockDOTSBackend:
    """Test cases for MockDOTSBackend."""

    @pytest.fixture
    def backend(self, config):
        return MockDOTSBackend(config)

    def test_initialization(self, backend):
        """Test backend initialization."""
        assert backend.name == "dots-ocr"
        assert backend.is_available()

    @pytest.mark.asyncio
    async def test_process_image_with_layout_analysis(self, backend, sample_image_path):
        """Test OCR with layout analysis."""
        result = await backend.process_image(str(sample_image_path), mode="formatted")

        assert result["success"] is True
        assert "layout_analysis" in result
        assert "tables" in result["layout_analysis"]
        assert "paragraphs" in result["layout_analysis"]
        assert "table_data" in result

    def test_get_capabilities(self, backend):
        """Test backend capabilities."""
        capabilities = backend.get_capabilities()

        assert capabilities["name"] == "dots-ocr"
        assert "document understanding specialist" in capabilities["description"]


class TestMockPPOCRBackend:
    """Test cases for MockPPOCRBackend."""

    @pytest.fixture
    def backend(self, config):
        return MockPPOCRBackend(config)

    def test_initialization(self, backend):
        """Test backend initialization."""
        assert backend.name == "pp-ocrv5"
        assert backend.is_available()

    @pytest.mark.asyncio
    async def test_process_image_fast_processing(self, backend, sample_image_path):
        """Test fast industrial OCR processing."""
        result = await backend.process_image(str(sample_image_path))

        assert result["success"] is True
        assert "PP-OCRv5 industrial OCR result" in result["text"]
        assert result["processing_time"] == 0.08  # Fast processing
        assert result["gpu_used"] is True
        assert "industrial_metrics" in result

    def test_get_capabilities(self, backend):
        """Test backend capabilities."""
        capabilities = backend.get_capabilities()

        assert capabilities["name"] == "pp-ocrv5"
        assert capabilities["gpu_support"] is True
        assert "industrial-grade" in capabilities["description"]


class TestMockQwenBackend:
    """Test cases for MockQwenBackend."""

    @pytest.fixture
    def backend(self, config):
        return MockQwenBackend(config)

    def test_initialization(self, backend):
        """Test backend initialization."""
        assert backend.name == "qwen-image-layered"
        assert backend.is_available()

    @pytest.mark.asyncio
    async def test_process_image_layered_decomposition(self, backend, sample_image_path):
        """Test image layered decomposition."""
        result = await backend.process_image(str(sample_image_path))

        assert result["success"] is True
        assert "Qwen-Image-Layered decomposition result" in result["text"]
        assert "layers" in result
        assert result["layers"]["count"] == 4
        assert "decomposition" in result

    def test_get_capabilities(self, backend):
        """Test backend capabilities."""
        capabilities = backend.get_capabilities()

        assert capabilities["name"] == "qwen-image-layered"
        assert "image decomposition" in capabilities["description"]


class TestMockGOTBackend:
    """Test cases for MockGOTBackend."""

    @pytest.fixture
    def backend(self, config):
        return MockGOTBackend(config)

    def test_initialization(self, backend):
        """Test backend initialization."""
        assert backend.name == "got-ocr"
        assert backend.is_available()

    @pytest.mark.asyncio
    async def test_process_image_comic_mode(self, backend, sample_image_path):
        """Test OCR with comic mode."""
        result = await backend.process_image(
            str(sample_image_path),
            mode="text",
            comic_mode=True
        )

        assert result["success"] is True
        assert "GOT-OCR2.0 advanced OCR result" in result["text"]
        assert "comic_analysis" in result
        assert result["comic_analysis"]["panels_detected"] == 4

    def test_get_capabilities(self, backend):
        """Test backend capabilities."""
        capabilities = backend.get_capabilities()

        assert capabilities["name"] == "got-ocr"
        assert capabilities["gpu_support"] is True
        assert "General OCR Theory" in capabilities["description"]


class TestMockTesseractBackend:
    """Test cases for MockTesseractBackend."""

    @pytest.fixture
    def backend(self, config):
        return MockTesseractBackend(config)

    def test_initialization(self, backend):
        """Test backend initialization."""
        assert backend.name == "tesseract"
        assert backend.is_available()

    @pytest.mark.asyncio
    async def test_process_image_traditional_ocr(self, backend, sample_image_path):
        """Test traditional Tesseract OCR."""
        result = await backend.process_image(str(sample_image_path))

        assert result["success"] is True
        assert "Tesseract OCR result" in result["text"]
        assert result["processing_time"] == 0.05  # Fast traditional OCR
        assert not result["gpu_used"]
        assert "tesseract_version" in result

    def test_get_capabilities(self, backend):
        """Test backend capabilities."""
        capabilities = backend.get_capabilities()

        assert capabilities["name"] == "tesseract"
        assert not capabilities["gpu_support"]
        assert "Traditional Tesseract" in capabilities["description"]


class TestMockEasyOCRBackend:
    """Test cases for MockEasyOCRBackend."""

    @pytest.fixture
    def backend(self, config):
        return MockEasyOCRBackend(config)

    def test_initialization(self, backend):
        """Test backend initialization."""
        assert backend.name == "easyocr"
        assert backend.is_available()

    @pytest.mark.asyncio
    async def test_process_image_with_bounding_boxes(self, backend, sample_image_path):
        """Test OCR with bounding box detection."""
        result = await backend.process_image(str(sample_image_path))

        assert result["success"] is True
        assert "EasyOCR result" in result["text"]
        assert "detection_boxes" in result
        assert isinstance(result["detection_boxes"], list)
        assert len(result["detection_boxes"]) == 2  # Mock has 2 boxes

    def test_get_capabilities(self, backend):
        """Test backend capabilities."""
        capabilities = backend.get_capabilities()

        assert capabilities["name"] == "easyocr"
        assert capabilities["gpu_support"] is True
        assert "ch_sim" in capabilities["languages"]
        assert "ch_tra" in capabilities["languages"]


class TestBackendCommonBehavior:
    """Test common behavior across all backends."""

    @pytest.mark.parametrize("backend_class,backend_name", [
        (MockDeepSeekBackend, "deepseek-ocr"),
        (MockFlorenceBackend, "florence-2"),
        (MockDOTSBackend, "dots-ocr"),
        (MockPPOCRBackend, "pp-ocrv5"),
        (MockQwenBackend, "qwen-image-layered"),
        (MockGOTBackend, "got-ocr"),
        (MockTesseractBackend, "tesseract"),
        (MockEasyOCRBackend, "easyocr"),
    ])
    def test_all_backends_initialization(self, config, backend_class, backend_name):
        """Test that all backends initialize correctly."""
        backend = backend_class(config)

        assert backend.name == backend_name
        assert backend.config == config
        assert backend.is_available()

    @pytest.mark.parametrize("backend_class", [
        MockDeepSeekBackend,
        MockFlorenceBackend,
        MockDOTSBackend,
        MockPPOCRBackend,
        MockQwenBackend,
        MockGOTBackend,
        MockTesseractBackend,
        MockEasyOCRBackend,
    ])
    @pytest.mark.asyncio
    async def test_all_backends_process_image(self, config, sample_image_path, backend_class):
        """Test that all backends can process images."""
        backend = backend_class(config)

        result = await backend.process_image(str(sample_image_path))

        assert isinstance(result, dict)
        assert "success" in result
        assert "text" in result
        assert "backend" in result
        assert result["backend"] == backend.name

    @pytest.mark.parametrize("backend_class", [
        MockDeepSeekBackend,
        MockFlorenceBackend,
        MockDOTSBackend,
        MockPPOCRBackend,
        MockQwenBackend,
        MockGOTBackend,
        MockTesseractBackend,
        MockEasyOCRBackend,
    ])
    def test_all_backends_capabilities(self, config, backend_class):
        """Test that all backends provide capabilities."""
        backend = backend_class(config)

        capabilities = backend.get_capabilities()

        assert isinstance(capabilities, dict)
        assert "name" in capabilities
        assert "available" in capabilities
        assert "modes" in capabilities
        assert "languages" in capabilities
        assert "gpu_support" in capabilities
        assert "description" in capabilities

    @pytest.mark.parametrize("mode", ["text", "formatted", "fine-grained"])
    @pytest.mark.parametrize("backend_class", [
        MockDeepSeekBackend,
        MockFlorenceBackend,
        MockGOTBackend,
    ])
    @pytest.mark.asyncio
    async def test_mode_support(self, config, sample_image_path, backend_class, mode):
        """Test mode support across backends."""
        backend = backend_class(config)

        result = await backend.process_image(str(sample_image_path), mode=mode)

        assert result["success"] is True
        assert result["mode"] == mode






