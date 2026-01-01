"""
WIA (Windows Image Acquisition) Scanner Backend for OCR-MCP

Provides comprehensive scanner control for Windows using the native WIA API.
Supports flatbed scanners, ADF (Automatic Document Feeder), and various scan modes.
"""

import logging
import platform
from typing import Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Check if we're on Windows
IS_WINDOWS = platform.system() == "Windows"

# Optional imports - handle gracefully if not on Windows
if IS_WINDOWS:
    try:
        import comtypes
        import comtypes.client as cc
        import pythoncom

        # Try to generate WIA type library if missing
        try:
            from comtypes.gen import WIALib
        except ImportError:
            try:
                logger.info("Generating WIA type library...")
                # WIA 2.0 GUID
                cc.GetModule("{94A0E92D-43C0-494E-AC29-FD45948A5221}")
                from comtypes.gen import WIALib
            except Exception as e:
                logger.warning(f"Could not generate WIA type library: {e}")
                WIALib = None

        # Test WIA availability by trying to create DeviceManager
        try:
            try:
                pythoncom.CoInitialize()
            except Exception:
                # Already initialized
                pass
            test_dm = cc.CreateObject("WIA.DeviceManager")
            WIA_AVAILABLE = True
            logger.info("WIA is available and working")
        except Exception as e:
            logger.warning(f"WIA not available: {e}")
            WIA_AVAILABLE = False

    except ImportError as e:
        logger.warning(f"WIA dependencies not available: {e}")
        WIA_AVAILABLE = False
        comtypes = None
        cc = None
        pythoncom = None
else:
    WIA_AVAILABLE = False
    comtypes = None
    cc = None
    pythoncom = None


@dataclass
class ScannerInfo:
    """Information about a scanner device."""

    device_id: str
    name: str
    manufacturer: str
    description: str
    device_type: str  # "Flatbed", "Feeder", "Duplex"
    supports_adf: bool = False
    supports_duplex: bool = False
    max_dpi: int = 600


@dataclass
class ScanSettings:
    """Scanner configuration settings."""

    dpi: int = 300
    color_mode: str = "Color"  # "Color", "Grayscale", "BlackWhite"
    paper_size: str = "A4"  # "A4", "Letter", "Legal", "Custom"
    custom_width: Optional[int] = None  # pixels
    custom_height: Optional[int] = None  # pixels
    brightness: int = 0  # -1000 to 1000
    contrast: int = 0  # -1000 to 1000
    use_adf: bool = False
    duplex: bool = False


@dataclass
class ScannerProperties:
    """Detailed scanner capabilities."""

    supported_resolutions: List[int]
    supported_color_modes: List[str]
    supported_paper_sizes: List[str]
    max_paper_width: int  # pixels at max DPI
    max_paper_height: int  # pixels at max DPI
    supports_adf: bool
    supports_duplex: bool
    supports_preview: bool
    manufacturer: str
    model: str
    firmware_version: str


class WIABackend:
    """
    WIA Scanner Backend for Windows.

    Provides comprehensive scanner control using Windows Image Acquisition API.
    """

    def __init__(self):
        self._wia_manager = None
        self._devices = {}
        self._initialized = False

        if not IS_WINDOWS:
            logger.warning("WIA scanner backend only available on Windows")
            return

        if not WIA_AVAILABLE:
            logger.warning("WIA dependencies not available")
            return

        try:
            # Initialize COM
            try:
                pythoncom.CoInitialize()
            except Exception:
                pass

            # Create WIA manager
            self._wia_manager = cc.CreateObject("WIA.DeviceManager")
            self._initialized = True
            logger.info("WIA scanner backend initialized")

        except Exception as e:
            logger.error(f"Failed to initialize WIA backend: {e}")
            self._initialized = False

    def is_available(self) -> bool:
        """Check if WIA backend is available and functional."""
        return self._initialized and IS_WINDOWS and WIA_AVAILABLE

    def discover_scanners(self) -> List[ScannerInfo]:
        """
        Discover all connected scanners via WIA.

        Returns:
            List of ScannerInfo objects for each discovered scanner
        """
        if not self.is_available():
            return []

        scanners = []
        try:
            # Enumerate WIA devices
            for device_info in self._wia_manager.DeviceInfos:
                try:
                    device = device_info.Connect()

                    # Extract device information
                    scanner_info = self._extract_scanner_info(device)
                    if scanner_info:
                        scanners.append(scanner_info)
                        self._devices[scanner_info.device_id] = device

                except Exception as e:
                    logger.warning(f"Failed to connect to scanner: {e}")
                    continue

        except Exception as e:
            logger.error(f"Scanner discovery failed: {e}")

        logger.info(f"Discovered {len(scanners)} scanners")
        return scanners

    def _extract_scanner_info(self, device) -> Optional[ScannerInfo]:
        """Extract scanner information from WIA device object."""
        try:
            properties = device.Properties

            # Basic device info
            device_id = str(device.DeviceID)
            name = self._get_property_value(properties, "Name") or "Unknown Scanner"
            manufacturer = (
                self._get_property_value(properties, "Manufacturer") or "Unknown"
            )
            description = self._get_property_value(properties, "Description") or name

            # Device type and capabilities
            device_type = "Flatbed"  # Default
            supports_adf = False
            supports_duplex = False

            # Check for document handling capabilities
            try:
                # Use Items property for WIA 2.0
                items = getattr(device, "Items", None)
                if items and len(items) > 0:
                    # Check if device supports ADF
                    supports_adf = True
                    device_type = "Feeder"
            except Exception as e:
                logger.debug(f"Failed to check ADF capabilities: {e}")
                pass

            # Get maximum DPI
            max_dpi = 600  # Default
            try:
                # Try to get horizontal resolution
                horiz_res = self._get_property_value(
                    properties, "Horizontal Resolution"
                )
                if horiz_res:
                    max_dpi = max(max_dpi, int(horiz_res))
            except Exception:
                pass

            return ScannerInfo(
                device_id=device_id,
                name=name,
                manufacturer=manufacturer,
                description=description,
                device_type=device_type,
                supports_adf=supports_adf,
                supports_duplex=supports_duplex,
                max_dpi=max_dpi,
            )

        except Exception as e:
            logger.error(f"Failed to extract scanner info: {e}")
            return None

    def get_scanner_properties(self, device_id: str) -> Optional[ScannerProperties]:
        """
        Get detailed properties and capabilities of a scanner.

        Args:
            device_id: The scanner device ID

        Returns:
            ScannerProperties object or None if scanner not found
        """
        if not self.is_available():
            return None

        device = self._devices.get(device_id)
        if not device:
            # Try to find and connect to the device
            try:
                for device_info in self._wia_manager.DeviceInfos:
                    if str(device_info.DeviceID) == device_id:
                        device = device_info.Connect()
                        break
            except Exception as e:
                logger.error(f"Failed to connect to scanner {device_id}: {e}")
                return None

        if not device:
            return None

        try:
            properties = device.Properties

            # Extract comprehensive properties
            supported_resolutions = [75, 150, 200, 300, 600]  # Common defaults
            supported_color_modes = ["Color", "Grayscale", "BlackWhite"]
            supported_paper_sizes = ["A4", "Letter", "Legal"]

            manufacturer = (
                self._get_property_value(properties, "Manufacturer") or "Unknown"
            )
            model = self._get_property_value(properties, "Model") or "Unknown"
            firmware_version = (
                self._get_property_value(properties, "Firmware Version") or "Unknown"
            )

            # Try to get actual capabilities
            supports_adf = False
            supports_duplex = False
            try:
                # Get supported resolutions from device
                item_list = getattr(device, "Items", None)
                if item_list and len(item_list) > 0:
                    props = item_list[0].Properties
                    horiz_res = self._get_property_value(props, "Horizontal Resolution")
                    if horiz_res:
                        supported_resolutions = [int(horiz_res)]

                    # Try to detect ADF
                    supports_adf = True
            except Exception:
                pass

            return ScannerProperties(
                supported_resolutions=supported_resolutions,
                supported_color_modes=supported_color_modes,
                supported_paper_sizes=supported_paper_sizes,
                max_paper_width=5100,  # A4 at 600 DPI
                max_paper_height=6600,  # A4 at 600 DPI
                supports_adf=supports_adf,
                supports_duplex=supports_duplex,
                supports_preview=True,
                manufacturer=manufacturer,
                model=model,
                firmware_version=firmware_version,
            )

        except Exception as e:
            logger.error(f"Failed to get scanner properties for {device_id}: {e}")
            return None

    def configure_scan(self, device_id: str, settings: ScanSettings) -> bool:
        """
        Configure scanner parameters for upcoming scan.

        Args:
            device_id: The scanner device ID
            settings: ScanSettings object with configuration

        Returns:
            True if configuration successful, False otherwise
        """
        if not self.is_available():
            return False

        device = self._devices.get(device_id)
        if not device:
            return False

        try:
            # Get the scan item (usually the flatbed or feeder)
            # WIA 2.0 uses Items collection
            items = getattr(device, "Items", None)
            if not items or len(items) == 0:
                logger.error(f"No scan items available for scanner {device_id}")
                return False

            item = items[0]  # Use first available item
            properties = item.Properties

            # Configure resolution
            self._set_property_value(properties, "Horizontal Resolution", settings.dpi)
            self._set_property_value(properties, "Vertical Resolution", settings.dpi)

            # Configure color mode
            color_mode_map = {
                "Color": 1,  # WIA_PHOTO_COLOR
                "Grayscale": 2,  # WIA_PHOTO_GRAYSCALE
                "BlackWhite": 4,  # WIA_PHOTO_BLACKWHITE
            }
            color_value = color_mode_map.get(settings.color_mode, 1)
            self._set_property_value(properties, "Current Intent", color_value)

            # Configure brightness and contrast
            self._set_property_value(properties, "Brightness", settings.brightness)
            self._set_property_value(properties, "Contrast", settings.contrast)

            logger.info(
                f"Scanner {device_id} configured: {settings.dpi} DPI, {settings.color_mode}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to configure scanner {device_id}: {e}")
            return False

    def scan_document(self, device_id: str, settings: ScanSettings) -> Optional[Any]:
        """
        Perform a document scan with the specified settings.

        Args:
            device_id: The scanner device ID
            settings: ScanSettings object

        Returns:
            PIL Image object if successful, None otherwise
        """
        if not self.is_available():
            return None

        # Ensure COM is initialized for this thread
        try:
            pythoncom.CoInitialize()
        except Exception:
            pass

        device = self._devices.get(device_id)
        if not device:
            # Try to reconnect
            try:
                for device_info in self._wia_manager.DeviceInfos:
                    if str(device_info.DeviceID) == device_id:
                        device = device_info.Connect()
                        self._devices[device_id] = device
                        break
            except Exception as e:
                logger.error(
                    f"Failed to reconnect to scanner {device_id} for scan: {e}"
                )
                return None

        if not device:
            logger.error(f"Scanner {device_id} not found")
            return None

        try:
            # Configure scanner first
            if not self.configure_scan(device_id, settings):
                # Try one more time with a fresh connection if it failed with busy
                try:
                    logger.info("Retrying scan with fresh connection...")
                    for device_info in self._wia_manager.DeviceInfos:
                        if str(device_info.DeviceID) == device_id:
                            device = device_info.Connect()
                            self._devices[device_id] = device
                            if not self.configure_scan(device_id, settings):
                                return None
                            break
                except:
                    return None

            # Get scan item
            items = getattr(device, "Items", None)
            if not items or len(items) == 0:
                logger.error(f"No scan items available for scanner {device_id}")
                return None

            item = items[0]

            # Perform the scan
            logger.info(f"Starting scan on {device_id}")
            image_file = item.Transfer()

            # Convert WIA image to PIL Image
            from PIL import Image
            import io

            # WIA returns image data, convert to PIL
            if hasattr(image_file, "FileData"):
                # Handle WIA ImageFile format
                image_data = image_file.FileData.getvalue()
                image = Image.open(io.BytesIO(image_data))
            else:
                logger.error("Unsupported WIA image format")
                return None

            logger.info(f"Scan completed successfully on {device_id}")
            return image

        except Exception as e:
            logger.error(f"Scan failed on {device_id}: {e}")
            return None

    def _get_property_value(self, properties, property_name: str) -> Any:
        """Get a property value from WIA properties collection."""
        try:
            for prop in properties:
                if prop.Name == property_name:
                    return prop.Value
        except:
            pass
        return None

    def _set_property_value(self, properties, property_name: str, value: Any) -> bool:
        """Set a property value in WIA properties collection."""
        try:
            for prop in properties:
                if prop.Name == property_name:
                    prop.Value = value
                    return True
        except Exception as e:
            logger.warning(f"Failed to set property {property_name}: {e}")
        return False

    def __del__(self):
        """Cleanup COM resources."""
        if hasattr(self, "_wia_manager") and self._wia_manager:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
