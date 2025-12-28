"""
Unit tests for OCR-MCP scanner functionality.
"""

import pytest
from PIL import Image

from tests.mocks.mock_scanner import MockWIABackend, MockScannerManager


class TestMockWIABackend:
    """Test cases for MockWIABackend."""

    @pytest.fixture
    def backend(self):
        return MockWIABackend()

    def test_initialization(self, backend):
        """Test backend initialization."""
        assert backend.is_available()
        assert len(backend.scanners) == 2
        assert backend.call_count == 0

    def test_discover_scanners(self, backend):
        """Test scanner discovery."""
        scanners = backend.discover_scanners()

        assert len(scanners) == 2
        assert backend.call_count == 1

        # Check first scanner
        scanner1 = scanners[0]
        assert scanner1["device_id"] == "wia:test_scanner_1"
        assert scanner1["name"] == "Test Flatbed Scanner"
        assert scanner1["supports_adf"] is False
        assert scanner1["max_dpi"] == 1200

        # Check second scanner
        scanner2 = scanners[1]
        assert scanner2["device_id"] == "wia:test_scanner_2"
        assert scanner2["name"] == "Test ADF Scanner"
        assert scanner2["supports_adf"] is True
        assert scanner2["supports_duplex"] is True

    def test_get_scanner_properties_existing(self, backend):
        """Test getting properties for existing scanner."""
        properties = backend.get_scanner_properties("wia:test_scanner_1")

        assert properties is not None
        assert properties["manufacturer"] == "Test Corp"
        assert properties["model"] == "Test Flatbed Scanner"
        assert properties["supports_adf"] is False
        assert properties["max_paper_width"] == 5100
        assert backend.call_count == 1

    def test_get_scanner_properties_nonexistent(self, backend):
        """Test getting properties for non-existent scanner."""
        properties = backend.get_scanner_properties("wia:nonexistent_scanner")

        assert properties is None
        assert backend.call_count == 1

    def test_configure_scan_success(self, backend):
        """Test successful scan configuration."""
        settings = {
            "dpi": 300,
            "color_mode": "Color",
            "brightness": 0,
            "contrast": 0
        }

        result = backend.configure_scan("wia:test_scanner_1", settings)

        assert result is True
        assert backend.call_count == 1
        assert backend.last_call_args == ("wia:test_scanner_1", settings)

    def test_configure_scan_invalid_dpi(self, backend):
        """Test scan configuration with invalid DPI."""
        settings = {
            "dpi": 0,  # Invalid
            "color_mode": "Color"
        }

        result = backend.configure_scan("wia:test_scanner_1", settings)

        assert result is False
        assert backend.call_count == 1

    def test_configure_scan_invalid_color_mode(self, backend):
        """Test scan configuration with invalid color mode."""
        settings = {
            "dpi": 300,
            "color_mode": "InvalidMode"
        }

        result = backend.configure_scan("wia:test_scanner_1", settings)

        assert result is False
        assert backend.call_count == 1

    def test_scan_document_success(self, backend):
        """Test successful document scanning."""
        settings = {
            "dpi": 300,
            "color_mode": "Color",
            "paper_size": "A4"
        }

        image = backend.scan_document("wia:test_scanner_1", settings)

        assert image is not None
        assert isinstance(image, Image.Image)
        assert image.mode == "RGB"
        assert image.size == (2480, 3508)  # A4 at 300 DPI
        assert backend.call_count == 1

    def test_scan_document_nonexistent_scanner(self, backend):
        """Test scanning with non-existent scanner."""
        settings = {"dpi": 300, "color_mode": "Color"}

        image = backend.scan_document("wia:nonexistent", settings)

        assert image is None
        assert backend.call_count == 1

    def test_scan_document_grayscale(self, backend):
        """Test scanning in grayscale mode."""
        settings = {
            "dpi": 300,
            "color_mode": "Grayscale",
            "paper_size": "A4"
        }

        image = backend.scan_document("wia:test_scanner_1", settings)

        assert image is not None
        assert image.mode == "L"  # Grayscale
        assert backend.call_count == 1

    def test_scan_document_black_white(self, backend):
        """Test scanning in black and white mode."""
        settings = {
            "dpi": 150,
            "color_mode": "BlackWhite",
            "paper_size": "Letter"
        }

        image = backend.scan_document("wia:test_scanner_1", settings)

        assert image is not None
        assert image.mode == "1"  # Binary
        assert backend.call_count == 1

    def test_call_tracking(self, backend):
        """Test that call tracking works correctly."""
        initial_count = backend.call_count

        backend.discover_scanners()
        assert backend.call_count == initial_count + 1

        backend.get_scanner_properties("wia:test_scanner_1")
        assert backend.call_count == initial_count + 2


class TestMockScannerManager:
    """Test cases for MockScannerManager."""

    @pytest.fixture
    def manager(self):
        return MockScannerManager()

    def test_initialization(self, manager):
        """Test manager initialization."""
        assert manager.is_available()
        assert isinstance(manager.wia_backend, MockWIABackend)

    def test_discover_scanners(self, manager):
        """Test scanner discovery through manager."""
        scanners = manager.discover_scanners()

        assert len(scanners) == 2
        assert scanners[0]["device_id"] == "wia:test_scanner_1"
        assert scanners[1]["device_id"] == "wia:test_scanner_2"

    def test_get_scanner_info_existing(self, manager):
        """Test getting scanner info for existing scanner."""
        info = manager.get_scanner_info("wia:test_scanner_1")

        assert info is not None
        assert info["name"] == "Test Flatbed Scanner"
        assert info["supports_adf"] is False

    def test_get_scanner_info_nonexistent(self, manager):
        """Test getting scanner info for non-existent scanner."""
        info = manager.get_scanner_info("wia:nonexistent")

        assert info is None

    def test_get_scanner_properties(self, manager):
        """Test getting scanner properties."""
        properties = manager.get_scanner_properties("wia:test_scanner_1")

        assert properties is not None
        assert "manufacturer" in properties
        assert "supported_resolutions" in properties

    def test_configure_scan(self, manager):
        """Test scan configuration through manager."""
        settings = {
            "dpi": 600,
            "color_mode": "Grayscale",
            "brightness": 10,
            "contrast": -5
        }

        result = manager.configure_scan("wia:test_scanner_1", settings)

        assert result is True

    def test_scan_document(self, manager):
        """Test document scanning through manager."""
        settings = {
            "dpi": 150,
            "color_mode": "Color",
            "paper_size": "A4"
        }

        image = manager.scan_document("wia:test_scanner_1", settings)

        assert image is not None
        assert isinstance(image, Image.Image)
        assert image.size == (1240, 1754)  # A4 at 150 DPI

    @pytest.mark.asyncio
    async def test_scan_batch(self, manager):
        """Test batch scanning."""
        settings = {
            "dpi": 150,
            "color_mode": "Color",
            "paper_size": "A4"
        }

        images = await manager.scan_batch("wia:test_scanner_1", settings, count=3)

        assert len(images) == 3
        for image in images:
            assert isinstance(image, Image.Image)
            assert image.size == (1240, 1754)

    @pytest.mark.asyncio
    async def test_scan_batch_with_failure(self, manager):
        """Test batch scanning with scanner failure."""
        settings = {"dpi": 150, "color_mode": "Color"}

        # Test with non-existent scanner
        images = await manager.scan_batch("wia:nonexistent", settings, count=2)

        assert len(images) == 0  # Should stop on first failure

    def test_get_available_backends(self, manager):
        """Test getting available backends."""
        backends = manager.get_available_backends()

        assert "wia" in backends

    def test_manager_call_tracking(self, manager):
        """Test that manager tracks calls correctly."""
        initial_count = manager.call_count

        manager.discover_scanners()
        assert manager.call_count == initial_count + 1

        manager.get_scanner_info("wia:test_scanner_1")
        assert manager.call_count == initial_count + 2


class TestScannerIntegration:
    """Test integration between scanner components."""

    def test_backend_manager_integration(self, config):
        """Test that backend manager properly integrates scanner manager."""
        from src.ocr_mcp.core.backend_manager import BackendManager

        manager = BackendManager(config)

        # Should have scanner manager
        assert hasattr(manager, 'scanner_manager')
        assert manager.scanner_manager is not None

    def test_scanner_manager_availability(self):
        """Test scanner manager availability detection."""
        manager = MockScannerManager()

        # Should be available by default
        assert manager.is_available()

        # Test with backend unavailable
        manager.wia_backend._available = False
        assert not manager.is_available()

    def test_scanner_device_id_parsing(self):
        """Test device ID parsing logic."""
        # This tests the _parse_device_id method logic
        manager = MockScannerManager()

        # Test with backend prefix
        backend_name, device_id = "wia", "test_scanner"
        full_id = f"{backend_name}:{device_id}"

        # Simulate parsing (this would be in the real implementation)
        if ":" in full_id:
            parsed_backend, parsed_device = full_id.split(":", 1)
            assert parsed_backend == backend_name
            assert parsed_device == device_id

        # Test without prefix (fallback)
        fallback_id = "test_scanner"
        if ":" not in fallback_id:
            assert fallback_id == "test_scanner"

    def test_scan_settings_validation(self):
        """Test scan settings validation."""
        manager = MockScannerManager()

        # Valid settings
        valid_settings = {
            "dpi": 300,
            "color_mode": "Color",
            "paper_size": "A4",
            "brightness": 0,
            "contrast": 0,
            "use_adf": False,
            "duplex": False
        }

        result = manager.configure_scan("wia:test_scanner_1", valid_settings)
        assert result is True

        # Invalid DPI
        invalid_settings = valid_settings.copy()
        invalid_settings["dpi"] = -1

        result = manager.configure_scan("wia:test_scanner_1", invalid_settings)
        assert result is False

    def test_different_scanner_types(self):
        """Test handling different scanner types."""
        backend = MockWIABackend()

        scanners = backend.discover_scanners()

        # Should have different types
        flatbed = next(s for s in scanners if "Flatbed" in s["name"])
        feeder = next(s for s in scanners if "ADF" in s["name"])

        assert not flatbed["supports_adf"]
        assert not flatbed["supports_duplex"]

        assert feeder["supports_adf"]
        assert feeder["supports_duplex"]

    def test_scanner_properties_comprehensive(self):
        """Test comprehensive scanner properties."""
        backend = MockWIABackend()

        properties = backend.get_scanner_properties("wia:test_scanner_1")

        required_keys = [
            "supported_resolutions", "supported_color_modes",
            "supported_paper_sizes", "max_paper_width", "max_paper_height",
            "supports_adf", "supports_duplex", "supports_preview",
            "manufacturer", "model", "firmware_version"
        ]

        for key in required_keys:
            assert key in properties

        # Validate data types
        assert isinstance(properties["supported_resolutions"], list)
        assert isinstance(properties["supported_color_modes"], list)
        assert isinstance(properties["supports_adf"], bool)
        assert isinstance(properties["manufacturer"], str)






