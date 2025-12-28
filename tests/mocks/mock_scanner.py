"""
Mock Scanner Implementations

Comprehensive mock implementations for scanner hardware interfaces
to enable testing without requiring physical scanner hardware.
"""

import asyncio
from typing import Dict, Any, Optional, List
from PIL import Image


class MockWIABackend:
    """Mock WIA (Windows Image Acquisition) scanner backend."""

    def __init__(self):
        self._available = True
        self.call_count = 0
        self.last_call_args = None
        self.scanners = [
            {
                "device_id": "wia:test_scanner_1",
                "name": "Test Flatbed Scanner",
                "manufacturer": "Test Corp",
                "description": "High-quality flatbed scanner for testing",
                "device_type": "Flatbed",
                "supports_adf": False,
                "supports_duplex": False,
                "max_dpi": 1200
            },
            {
                "device_id": "wia:test_scanner_2",
                "name": "Test ADF Scanner",
                "manufacturer": "Advanced Test Corp",
                "description": "Automatic document feeder scanner",
                "device_type": "Feeder",
                "supports_adf": True,
                "supports_duplex": True,
                "max_dpi": 600
            }
        ]

    def is_available(self) -> bool:
        return self._available

    def discover_scanners(self) -> List[Dict[str, Any]]:
        """Mock scanner discovery."""
        self.call_count += 1
        return self.scanners.copy()

    def get_scanner_properties(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Mock scanner properties retrieval."""
        self.call_count += 1
        self.last_call_args = device_id

        scanner = next((s for s in self.scanners if s["device_id"] == device_id), None)
        if not scanner:
            return None

        # Return detailed properties
        return {
            "supported_resolutions": [75, 150, 200, 300, 600, 1200],
            "supported_color_modes": ["Color", "Grayscale", "BlackWhite"],
            "supported_paper_sizes": ["A4", "Letter", "Legal", "Custom"],
            "max_paper_width": 5100,  # A4 at 600 DPI
            "max_paper_height": 6600,  # A4 at 600 DPI
            "supports_adf": scanner["supports_adf"],
            "supports_duplex": scanner["supports_duplex"],
            "supports_preview": True,
            "manufacturer": scanner["manufacturer"],
            "model": scanner["name"],
            "firmware_version": "1.2.3"
        }

    def configure_scan(self, device_id: str, settings: Dict[str, Any]) -> bool:
        """Mock scan configuration."""
        self.call_count += 1
        self.last_call_args = (device_id, settings)

        # Validate settings
        if settings.get("dpi", 0) <= 0:
            return False
        if settings.get("color_mode") not in ["Color", "Grayscale", "BlackWhite"]:
            return False

        return True

    def scan_document(self, device_id: str, settings: Dict[str, Any]) -> Optional[Image.Image]:
        """Mock document scanning."""
        self.call_count += 1
        self.last_call_args = (device_id, settings)

        # Check if scanner exists
        scanner = next((s for s in self.scanners if s["device_id"] == device_id), None)
        if not scanner:
            return None

        # Simulate scanning delay
        import time
        time.sleep(0.1)

        # Create mock scanned image
        dpi = settings.get("dpi", 300)
        color_mode = settings.get("color_mode", "Color")

        # A4 at requested DPI
        width = int(8.27 * dpi)  # A4 width in inches
        height = int(11.69 * dpi)  # A4 height in inches

        if color_mode == "Color":
            mode = "RGB"
            color = (255, 255, 255)  # White background
        elif color_mode == "Grayscale":
            mode = "L"
            color = 255  # White
        else:  # BlackWhite
            mode = "1"
            color = 1  # White

        # Create image with some mock content
        image = Image.new(mode, (width, height), color)

        # Add some mock text-like content (simplified)
        if color_mode != "BlackWhite":
            # Draw some lines to simulate text
            from PIL import ImageDraw
            draw = ImageDraw.Draw(image)
            for y in range(100, height, 50):
                draw.line([(50, y), (width-50, y)], fill=(0, 0, 0), width=2)

        return image


class MockScannerManager:
    """Mock scanner manager for unified scanner interface."""

    def __init__(self):
        self.wia_backend = MockWIABackend()
        self._available = True
        self.call_count = 0

    def is_available(self) -> bool:
        return self._available and self.wia_backend.is_available()

    def discover_scanners(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Mock scanner discovery across all backends."""
        self.call_count += 1
        return self.wia_backend.discover_scanners()

    def get_scanner_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Mock scanner info retrieval."""
        self.call_count += 1
        scanners = self.wia_backend.discover_scanners()
        return next((s for s in scanners if s["device_id"] == device_id), None)

    def get_scanner_properties(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Mock scanner properties retrieval."""
        self.call_count += 1
        return self.wia_backend.get_scanner_properties(device_id)

    def configure_scan(self, device_id: str, settings: Dict[str, Any]) -> bool:
        """Mock scan configuration."""
        self.call_count += 1
        return self.wia_backend.configure_scan(device_id, settings)

    def scan_document(self, device_id: str, settings: Dict[str, Any]) -> Optional[Image.Image]:
        """Mock document scanning."""
        self.call_count += 1
        return self.wia_backend.scan_document(device_id, settings)

    async def scan_batch(
        self,
        device_id: str,
        settings: Dict[str, Any],
        count: int = 10,
        auto_process: bool = True
    ) -> List[Image.Image]:
        """Mock batch scanning."""
        self.call_count += 1

        images = []
        for i in range(count):
            image = self.scan_document(device_id, settings)
            if image:
                images.append(image)
            else:
                break  # Stop on first failure

            # Small delay between scans
            await asyncio.sleep(0.05)

        return images

    def get_available_backends(self) -> List[str]:
        """Mock available backends."""
        return ["wia"] if self.is_available() else []


# Factory functions
def create_mock_wia_backend() -> MockWIABackend:
    """Factory for WIA backend mock."""
    return MockWIABackend()


def create_mock_scanner_manager() -> MockScannerManager:
    """Factory for scanner manager mock."""
    return MockScannerManager()


# Test data generators
def generate_mock_scan_settings(
    dpi: int = 300,
    color_mode: str = "Color",
    paper_size: str = "A4",
    brightness: int = 0,
    contrast: int = 0,
    use_adf: bool = False,
    duplex: bool = False
) -> Dict[str, Any]:
    """Generate mock scan settings for testing."""
    return {
        "dpi": dpi,
        "color_mode": color_mode,
        "paper_size": paper_size,
        "brightness": brightness,
        "contrast": contrast,
        "use_adf": use_adf,
        "duplex": duplex
    }


def generate_mock_scanner_list(count: int = 2) -> List[Dict[str, Any]]:
    """Generate a list of mock scanners for testing."""
    scanners = []
    for i in range(count):
        scanners.append({
            "device_id": f"wia:test_scanner_{i+1}",
            "name": f"Test Scanner {i+1}",
            "manufacturer": f"Test Corp {i+1}",
            "description": f"Mock scanner {i+1} for testing",
            "device_type": "Flatbed" if i % 2 == 0 else "Feeder",
            "supports_adf": i % 2 == 1,
            "supports_duplex": i % 2 == 1,
            "max_dpi": 600 + (i * 300)
        })
    return scanners


def create_mock_scanned_image(
    width: int = 1000,
    height: int = 1500,
    mode: str = "RGB",
    add_content: bool = True
) -> Image.Image:
    """Create a mock scanned image for testing."""
    image = Image.new(mode, (width, height), (255, 255, 255))  # White background

    if add_content and mode != "1":  # Not for binary images
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)

        # Add some mock text-like lines
        for y in range(100, height, 50):
            draw.line([(50, y), (width-50, y)], fill=(0, 0, 0), width=2)

        # Add some mock content blocks
        for x in range(100, width, 200):
            for y in range(150, height, 100):
                draw.rectangle([x, y, x+150, y+30], fill=(200, 200, 200))

    return image






