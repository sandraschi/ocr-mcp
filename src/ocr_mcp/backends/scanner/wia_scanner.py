"""
WIA (Windows Image Acquisition) Scanner Backend for OCR-MCP

Provides comprehensive scanner control for Windows using the native WIA API.
Supports flatbed scanners, ADF (Automatic Document Feeder), and various scan modes.
"""

import logging
import platform
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Check if we're on Windows
IS_WINDOWS = platform.system() == "Windows"

# Optional imports - handle gracefully if not on Windows
if IS_WINDOWS:
    try:
        import comtypes
        import comtypes.client as cc
        import pythoncom

        # WIA 2.0 Device Manager ID
        WIA_DEVICE_MANAGER_ID = "{E1C5D730-1228-487F-9675-91F3E1F5483E}"

        # Try to import WIA type library
        logger.info("Attempting to import WIA type library...")
        try:
            from comtypes.gen import WIA

            logger.info("Successfully imported WIA type library")
        except Exception as e:
            logger.warning(f"Initial WIA import failed: {e}. Attempting to generate wrapper...")
            # If not generated or failed to import, try to generate it
            try:
                # WIA 2.0 Type Library GUID
                WIA_LIB_ID = "{94A0E92D-43C0-494E-AC29-FD45948A5221}"
                comtypes.client.GetModule((WIA_LIB_ID, 1, 0))
                from comtypes.gen import WIA

                logger.info("Successfully generated and imported WIA type library")
            except Exception as e:
                logger.error(f"Could not load WIA type library: {e}")
                WIA = None
        WIALib = (
            WIA  # Alias for backward compatibility if needed, or remove if WIA is used directly
        )

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
    custom_width: int | None = None  # pixels
    custom_height: int | None = None  # pixels
    brightness: int = 0  # -1000 to 1000
    contrast: int = 0  # -1000 to 1000
    use_adf: bool = False
    duplex: bool = False


@dataclass
class ScannerProperties:
    """Detailed scanner capabilities."""

    supported_resolutions: list[int]
    supported_color_modes: list[str]
    supported_paper_sizes: list[str]
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
    Enhanced for Canon LiDE scanner compatibility.
    """

    def __init__(self):
        self._wia_manager = None
        self._devices = {}
        self._device_connections = {}  # Track active connections
        self._com_initialized = False
        self._initialized = False

        if not IS_WINDOWS:
            logger.warning("WIA scanner backend only available on Windows")
            return

        if not WIA_AVAILABLE:
            logger.warning("WIA dependencies not available")
            return

        try:
            # Initialize COM with proper apartment threading
            # Canon scanners often require STA (Single Threaded Apartment)
            try:
                pythoncom.CoInitializeEx(0)  # COINIT_MULTITHREADED
                self._com_initialized = True
                logger.debug("COM initialized successfully")
            except Exception as e:
                logger.warning(f"COM initialization failed: {e}")
                # Try alternative initialization
                try:
                    pythoncom.CoInitialize()
                    self._com_initialized = True
                    logger.debug("COM initialized with fallback method")
                except Exception as e2:
                    logger.error(f"All COM initialization attempts failed: {e2}")
                    return

            # Create WIA manager with error handling
            try:
                self._wia_manager = cc.CreateObject("WIA.DeviceManager")
                self._initialized = True
                logger.info("WIA scanner backend initialized successfully")
            except Exception as e:
                logger.error(f"Failed to create WIA DeviceManager: {e}")
                self._cleanup_com()
                return

        except Exception as e:
            logger.error(f"Failed to initialize WIA backend: {e}")
            self._cleanup_com()
            self._initialized = False

    def _cleanup_com(self):
        """Clean up COM resources properly."""
        try:
            if self._com_initialized:
                pythoncom.CoUninitialize()
                self._com_initialized = False
                logger.debug("COM uninitialized successfully")
        except Exception as e:
            logger.warning(f"COM cleanup failed: {e}")

    def _ensure_com_context(self):
        """Ensure COM is initialized for the current thread."""
        try:
            # Check if COM is already initialized for this thread
            pythoncom.CoInitializeEx(0)  # COINIT_MULTITHREADED
        except Exception:
            try:
                pythoncom.CoInitialize()
            except Exception:
                # Already initialized
                pass

    def is_available(self) -> bool:
        """Check if WIA backend is available and functional."""
        return self._initialized and IS_WINDOWS and WIA_AVAILABLE

    def discover_scanners(self) -> list[ScannerInfo]:
        """
        Discover all connected scanners via WIA.

        Returns:
            List of ScannerInfo objects for each discovered scanner
        """
        if not self.is_available():
            return []

        scanners = []
        self._ensure_com_context()

        try:
            # Clear existing connections to prevent conflicts
            self._cleanup_device_connections()

            # Enumerate WIA devices with better error handling
            device_infos = self._wia_manager.DeviceInfos
            logger.info(f"WIA reports {device_infos.Count} devices")

            for i in range(1, device_infos.Count + 1):  # WIA collections are 1-based
                try:
                    device_info = device_infos[i]
                    logger.debug(f"Attempting to connect to device {i}: {device_info.DeviceID}")

                    # Try to connect with retry logic for busy devices
                    device = self._connect_device_with_retry(device_info)
                    if device:
                        # Extract device information
                        scanner_info = self._extract_scanner_info(device)
                        if scanner_info:
                            scanners.append(scanner_info)
                            # Store device connection for later use
                            self._devices[scanner_info.device_id] = device
                            self._device_connections[scanner_info.device_id] = True
                            logger.info(f"Successfully connected to: {scanner_info.name}")
                        else:
                            # Clean up failed connection
                            self._release_device(device)
                    else:
                        logger.warning(f"Failed to connect to device {i}")

                except Exception as e:
                    logger.warning(f"Failed to process device {i}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Scanner discovery failed: {e}")

        logger.info(f"Successfully discovered {len(scanners)} scanners")
        return scanners

    def _connect_device_with_retry(self, device_info, max_retries: int = 3) -> Any | None:
        """Connect to a WIA device with retry logic for busy devices."""
        for attempt in range(max_retries):
            try:
                device = device_info.Connect()
                return device
            except Exception as e:
                error_code = getattr(e, 'hr', 0)
                if error_code == -2145320955:  # WIA_ERROR_BUSY (0x8021006B)
                    if attempt < max_retries - 1:
                        logger.warning(f"Device busy, retrying in 2 seconds (attempt {attempt + 1}/{max_retries})")
                        import time
                        time.sleep(2)
                        continue
                    else:
                        logger.error(f"Device busy after {max_retries} attempts")
                else:
                    logger.warning(f"Failed to connect to device (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        continue
                break
        return None

    def _release_device(self, device):
        """Release a device connection properly."""
        try:
            # Explicitly release COM objects
            if device:
                import pythoncom
                pythoncom.CoUninitialize()
        except Exception as e:
            logger.debug(f"Device cleanup warning: {e}")

    def _cleanup_device_connections(self):
        """Clean up all device connections."""
        for device_id in list(self._device_connections.keys()):
            if device_id in self._devices:
                try:
                    self._release_device(self._devices[device_id])
                except Exception as e:
                    logger.debug(f"Cleanup warning for {device_id}: {e}")
                del self._devices[device_id]
        self._device_connections.clear()

    def _extract_scanner_info(self, device) -> ScannerInfo | None:
        """Extract scanner information from WIA device object."""
        try:
            properties = device.Properties

            # Basic device info
            device_id = str(device.DeviceID)
            name = self._get_property_value(properties, "Name") or "Unknown Scanner"
            manufacturer = self._get_property_value(properties, "Manufacturer") or "Unknown"
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
                horiz_res = self._get_property_value(properties, "Horizontal Resolution")
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

    def get_scanner_properties(self, device_id: str) -> ScannerProperties | None:
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

            manufacturer = self._get_property_value(properties, "Manufacturer") or "Unknown"
            model = self._get_property_value(properties, "Model") or "Unknown"
            firmware_version = self._get_property_value(properties, "Firmware Version") or "Unknown"

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

    def scan_document(self, device_id: str, settings: ScanSettings) -> Any | None:
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

        self._ensure_com_context()

        device = self._devices.get(device_id)
        scan_success = False
        max_scan_attempts = 3

        for attempt in range(max_scan_attempts):
            try:
                logger.info(f"Scan attempt {attempt + 1}/{max_scan_attempts} on {device_id}")

                # Get fresh device connection for each attempt
                if not device or attempt > 0:
                    device = self._get_fresh_device_connection(device_id)
                    if not device:
                        logger.error(f"Cannot establish connection to {device_id}")
                        return None

                # Configure scanner with robust error handling
                if not self._configure_scan_robust(device, device_id, settings):
                    logger.warning(f"Configuration failed for {device_id}, attempt {attempt + 1}")
                    if attempt < max_scan_attempts - 1:
                        self._release_device(device)
                        import time
                        time.sleep(1)
                        continue
                    return None

                # Perform the actual scan
                image = self._perform_scan(device, device_id)
                if image:
                    scan_success = True
                    logger.info(f"Scan completed successfully on {device_id}")
                    return image
                else:
                    logger.warning(f"Scan returned no image for {device_id}, attempt {attempt + 1}")
                    if attempt < max_scan_attempts - 1:
                        self._release_device(device)
                        import time
                        time.sleep(1)
                        continue

            except Exception as e:
                error_code = getattr(e, 'hr', 0)
                logger.warning(f"Scan attempt {attempt + 1} failed: {e} (Error code: {error_code})")

                # Check for specific Canon scanner errors
                if error_code == -2145320955:  # WIA_ERROR_BUSY
                    logger.info("Device busy, will retry with fresh connection")
                elif error_code == -2145320954:  # WIA_ERROR_DEVICE_COMMUNICATION
                    logger.warning("Device communication error - may need power cycle")

                if attempt < max_scan_attempts - 1:
                    # Clean up and retry
                    if device:
                        self._release_device(device)
                    import time
                    time.sleep(2)  # Longer delay for retry
                    continue
                else:
                    logger.error(f"All scan attempts failed for {device_id}")
                    return None

        return None

    def _get_fresh_device_connection(self, device_id: str) -> Any | None:
        """Get a fresh device connection, handling busy states."""
        try:
            for device_info in self._wia_manager.DeviceInfos:
                if str(device_info.DeviceID) == device_id or str(device_info.DeviceID) == device_id.replace('wia:', ''):
                    return self._connect_device_with_retry(device_info)
        except Exception as e:
            logger.error(f"Failed to get fresh connection for {device_id}: {e}")
        return None

    def _configure_scan_robust(self, device, device_id: str, settings: ScanSettings) -> bool:
        """Configure scan with robust error handling for Canon scanners."""
        try:
            # Get scan item
            items = getattr(device, "Items", None)
            if not items or len(items) == 0:
                logger.error(f"No scan items available for scanner {device_id}")
                return False

            item = items[0]
            properties = item.Properties

            # Configure with error handling for each property
            config_success = True

            # Resolution (critical for Canon scanners)
            if not self._set_property_safe(properties, "Horizontal Resolution", settings.dpi):
                logger.warning(f"Failed to set horizontal resolution for {device_id}")
                config_success = False
            if not self._set_property_safe(properties, "Vertical Resolution", settings.dpi):
                logger.warning(f"Failed to set vertical resolution for {device_id}")
                config_success = False

            # Color mode
            color_mode_map = {
                "Color": 1,      # WIA_PHOTO_COLOR
                "Grayscale": 2,  # WIA_PHOTO_GRAYSCALE
                "BlackWhite": 4, # WIA_PHOTO_BLACKWHITE
            }
            color_value = color_mode_map.get(settings.color_mode, 1)
            if not self._set_property_safe(properties, "Current Intent", color_value):
                logger.warning(f"Failed to set color mode for {device_id}")

            # Optional properties (don't fail if not supported)
            self._set_property_safe(properties, "Brightness", settings.brightness)
            self._set_property_safe(properties, "Contrast", settings.contrast)

            # Paper size and other settings are often not supported by Canon scanners
            # so we don't treat failures as critical

            return config_success

        except Exception as e:
            logger.error(f"Configuration failed for {device_id}: {e}")
            return False

    def _set_property_safe(self, properties, property_name: str, value: Any) -> bool:
        """Set a WIA property safely, returning success status."""
        try:
            for prop in properties:
                if prop.Name == property_name:
                    prop.Value = value
                    logger.debug(f"Set {property_name} to {value}")
                    return True
        except Exception as e:
            logger.debug(f"Failed to set {property_name}: {e}")
        return False

    def _perform_scan(self, device, device_id: str) -> Any | None:
        """Perform the actual scan operation."""
        try:
            # Get scan item
            items = getattr(device, "Items", None)
            if not items or len(items) == 0:
                logger.error(f"No scan items available for scanner {device_id}")
                return None

            item = items[0]

            # Perform the scan with timeout handling
            logger.info(f"Starting scan on {device_id}")
            image_file = item.Transfer()

            # Convert WIA image to PIL Image
            import io
            from PIL import Image

            # WIA returns image data, convert to PIL
            if hasattr(image_file, "FileData"):
                # Handle WIA ImageFile format
                image_data = image_file.FileData.getvalue()
                image = Image.open(io.BytesIO(image_data))
                logger.info(f"Scan successful: {image.size} pixels")
                return image
            else:
                logger.error("Unsupported WIA image format")
                return None

        except Exception as e:
            logger.error(f"Scan operation failed for {device_id}: {e}")
            return None

    def _get_property_value(self, properties, property_name: str) -> Any:
        """Get a property value from WIA properties collection."""
        try:
            for prop in properties:
                if prop.Name == property_name:
                    return prop.Value
        except Exception:
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

    def get_diagnostics(self, device_id: str | None = None) -> dict[str, Any]:
        """
        Get diagnostic information about scanners and WIA status.

        Args:
            device_id: Optional specific device to diagnose

        Returns:
            Dictionary with diagnostic information
        """
        diagnostics = {
            "wia_available": WIA_AVAILABLE,
            "com_initialized": self._com_initialized,
            "backend_initialized": self._initialized,
            "windows_platform": IS_WINDOWS,
            "pythoncom_available": pythoncom is not None,
            "comtypes_available": comtypes is not None,
        }

        if self.is_available():
            try:
                device_count = self._wia_manager.DeviceInfos.Count
                diagnostics["device_count"] = device_count
                diagnostics["discovered_devices"] = list(self._devices.keys())

                if device_id and device_id in self._devices:
                    device = self._devices[device_id]
                    device_info = {
                        "connected": True,
                        "device_id": device_id,
                    }
                    try:
                        properties = device.Properties
                        device_info["properties_count"] = len(properties) if properties else 0
                    except Exception as e:
                        device_info["properties_error"] = str(e)

                    diagnostics["device_info"] = device_info
                elif device_id:
                    diagnostics["device_info"] = {"connected": False, "device_id": device_id}

            except Exception as e:
                diagnostics["enumeration_error"] = str(e)
        else:
            diagnostics["error"] = "WIA backend not available"

        return diagnostics

    def __del__(self):
        """Cleanup COM resources and device connections."""
        self._cleanup_device_connections()
        self._cleanup_com()
