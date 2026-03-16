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

        # WIA 2.0 Format GUIDs
        WIA_FORMAT_BMP = "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}"
        WIA_FORMAT_PNG = "{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}"
        WIA_FORMAT_JPEG = "{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}"
        WIA_FORMAT_TIFF = "{B96B3CB1-0728-11D3-9D7B-0000F81EF32E}"

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

        # We set _initialized to True if we are on Windows and dependencies are present.
        # Actual DeviceManager is created lazily to handle thread/COM apartment issues.
        self._initialized = True
        logger.info("WIA scanner backend initialized (lazy mode)")

    def _get_manager(self):
        """Get or create the WIA DeviceManager for the current thread context."""
        if not self.is_available():
            return None

        self._ensure_com_context()

        # Always create a new manager or check if it's usable in this thread
        # In multi-threaded environments (like FastAPI/uvicorn), creating it
        # per-call or per-thread is safer than sharing a single instance.
        try:
            return cc.CreateObject("WIA.DeviceManager")
        except Exception as e:
            logger.error(f"Failed to create WIA DeviceManager in current thread: {e}")
            return None

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
            # Try STA first as many Canon scanners prefer it
            pythoncom.CoInitialize()
            self._com_initialized = True
        except Exception:
            try:
                # Fallback to MTA if STA fails (e.g. already set to MTA)
                pythoncom.CoInitializeEx(0)
                self._com_initialized = True
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
        manager = self._get_manager()
        if not manager:
            return []

        new_devices = {}
        try:
            # Enumerate first without releasing previous connections (releasing before enumerate can make WIA report 0 devices).
            device_infos = manager.DeviceInfos
            logger.info(f"WIA reports {device_infos.Count} devices")

            for i in range(1, device_infos.Count + 1):  # WIA collections are 1-based
                try:
                    device_info = device_infos[i]
                    logger.debug(f"Attempting to connect to device {i}: {device_info.DeviceID}")

                    device = self._connect_device_with_retry(device_info)
                    if device:
                        scanner_info = self._extract_scanner_info(device)
                        if scanner_info:
                            scanners.append(scanner_info)
                            new_devices[scanner_info.device_id] = device
                            logger.info(f"Successfully connected to: {scanner_info.name}")
                        else:
                            self._release_device(device)
                    else:
                        logger.warning(f"Failed to connect to device {i}")

                except Exception as e:
                    logger.warning(f"Failed to process device {i}: {e}")
                    continue

            # Release only old connections that are no longer in the new set; then adopt new_devices.
            for device_id in list(self._devices.keys()):
                if device_id not in new_devices:
                    try:
                        self._release_device(self._devices[device_id])
                    except Exception as e:
                        logger.debug(f"Cleanup warning for {device_id}: {e}")
                    del self._devices[device_id]
            self._devices.update(new_devices)
            self._device_connections = {did: True for did in new_devices}

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
                error_code = getattr(e, "hr", 0)
                if error_code == -2145320955:  # WIA_ERROR_BUSY (0x8021006B)
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Device busy, retrying in 2 seconds "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
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
        """Release a device connection. Do NOT CoUninitialize - that tears down COM for the whole thread and breaks subsequent discovery."""
        try:
            if device and hasattr(device, "Release"):
                device.Release()
        except Exception as e:
            logger.debug(f"Device release warning: {e}")

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
                manager = self._get_manager()
                if manager:
                    for device_info in manager.DeviceInfos:
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
            item = self._get_scan_item(device, device_id, settings.use_adf)
            if not item:
                logger.error(f"No scan item available for scanner {device_id}")
                return False

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
                error_code = getattr(e, "hr", 0)
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
            manager = self._get_manager()
            if not manager:
                return None
            for device_info in manager.DeviceInfos:
                if str(device_info.DeviceID) == device_id or str(
                    device_info.DeviceID
                ) == device_id.replace("wia:", ""):
                    return self._connect_device_with_retry(device_info)
        except Exception as e:
            logger.error(f"Failed to get fresh connection for {device_id}: {e}")
        return None

    def _get_scan_item(self, device, device_id: str, use_adf: bool):
        """
        Return the WIA scan item (flatbed or feeder) for the given device.
        When use_adf is True and the device has multiple items, selects the feeder;
        otherwise selects the flatbed. Many WIA drivers expose flatbed as first item,
        feeder as second.
        """
        items = getattr(device, "Items", None)
        if not items or items.Count == 0:
            return None
        count = getattr(items, "Count", None) or len(items)
        if count == 1:
            try:
                return items[0]
            except Exception:
                try:
                    return items[1]
                except Exception:
                    return None
        # Multiple items: try category if available, else use conventional order
        try:
            for i in range(count):
                try:
                    it = items[i]
                except Exception:
                    try:
                        it = items[i + 1]
                    except Exception:
                        continue
                props = getattr(it, "Properties", None)
                if not props:
                    continue
                cat = self._get_property_value(props, "Item Category")
                if not cat:
                    cat = self._get_property_value(props, "Category")
                cat_str = str(cat).lower() if cat else ""
                if use_adf and ("feeder" in cat_str or "adf" in cat_str):
                    logger.debug(f"Selected feeder item by category for {device_id}")
                    return it
                if not use_adf and ("flatbed" in cat_str or "platen" in cat_str):
                    logger.debug(f"Selected flatbed item by category for {device_id}")
                    return it
        except Exception as e:
            logger.debug(f"Category-based item selection failed: {e}")
        # Fallback: conventional index (0 = flatbed, 1 = feeder for many drivers)
        for idx in ([1, 0] if use_adf else [0, 1]):
            try:
                item = items[idx]
                logger.debug(f"Using scan item index {idx} (use_adf={use_adf}) for {device_id}")
                return item
            except Exception:
                try:
                    item = items[idx + 1]
                    logger.debug(f"Using scan item index {idx + 1} (use_adf={use_adf}) for {device_id}")
                    return item
                except Exception:
                    continue
        return None

    def _configure_scan_robust(self, device, device_id: str, settings: ScanSettings) -> bool:
        """Configure scan with robust error handling for Canon scanners."""
        try:
            item = self._get_scan_item(device, device_id, settings.use_adf)
            if not item:
                logger.error(f"No scan item available for scanner {device_id}")
                return False
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
                "Color": 1,  # WIA_PHOTO_COLOR
                "Grayscale": 2,  # WIA_PHOTO_GRAYSCALE
                "BlackWhite": 4,  # WIA_PHOTO_BLACKWHITE
            }
            color_value = color_mode_map.get(settings.color_mode, 1)
            if not self._set_property_safe(properties, "Current Intent", color_value):
                logger.warning(f"Failed to set color mode for {device_id}")

            # Optional properties (don't fail if not supported)
            self._set_property_safe(properties, "Brightness", settings.brightness)
            self._set_property_safe(properties, "Contrast", settings.contrast)

            # Set output format to BMP (most compatible for Transfer method)
            if not self._set_property_safe(properties, "Format", WIA_FORMAT_BMP):
                logger.warning(f"Failed to set BMP format for {device_id}, continuing with default")

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
            if not items or items.Count == 0:
                logger.error(f"No scan items available for scanner {device_id}")
                return None

            # WIA collections are often 1-based
            try:
                item = items[1]
            except Exception:
                try:
                    item = items[0]
                except Exception:
                    logger.error(f"Could not access scan item for scanner {device_id}")
                    return None

            # Perform the scan with timeout handling
            logger.info(f"Starting scan transfer on {device_id}...")
            try:
                # item.Transfer() returns an ImageFile object
                image_file = item.Transfer()
            except Exception as e:
                logger.error(f"WIA Transfer call failed: {e}")
                return None

            if not image_file:
                logger.error("WIA Transfer returned None")
                return None

            # Convert WIA image to PIL Image
            import io
            from PIL import Image

            # WIA returns image data, convert to PIL
            try:
                if hasattr(image_file, "FileData"):
                    # WIA.ImageFile.FileData is a Vector object
                    logger.info("Extracting image data from WIA ImageFile...")
                    file_data = image_file.FileData

                    image_data = None
                    # Try various ways to get the bytes from the Vector
                    logger.info(f"Introspecting WIA Vector (type: {type(file_data)})")

                    # Direct attempt at BinaryData as it's the most standard
                    try:
                        image_data = file_data.BinaryData
                        if image_data and isinstance(image_data, (bytes, bytearray)):
                            logger.info(
                                "Successfully extracted image data from BinaryData property"
                            )
                        else:
                            if image_data:
                                logger.warning(
                                    f"BinaryData property returned {type(image_data)}, not bytes"
                                )
                                image_data = bytes(image_data)
                    except Exception as e:
                        logger.debug(f"Failed to access BinaryData property: {e}")

                    if image_data is None:
                        # try getvalue
                        try:
                            image_data = file_data.getvalue()
                            logger.info("Successfully extracted image data using getvalue()")
                        except Exception:
                            pass

                    if image_data is None or not isinstance(image_data, (bytes, bytearray)):
                        # Final attempt: try to convert Vector to bytes directly
                        try:
                            # If file_data is a comtypes Vector, we might needs to iterate
                            image_data = bytes(file_data)
                            logger.info("Successfully converted Vector to bytes directly")
                        except Exception:
                            logger.error(
                                f"All data extraction methods failed for Vector. "
                                f"Type: {type(file_data)}"
                            )
                            # Introspect attributes for debugging
                            attrs = [a for a in dir(file_data) if not a.startswith("_")]
                            logger.debug(f"Vector attributes: {attrs}")
                            return None

                    if not isinstance(image_data, (bytes, bytearray)):
                        logger.error(
                            f"Extraction failed: final result is {type(image_data)}, not bytes"
                        )
                        return None

                    image = Image.open(io.BytesIO(image_data))
                    logger.info(f"Scan successful: {image.size} pixels, format={image.format}")
                    return image
                else:
                    logger.error(f"Unsupported WIA object returned: {type(image_file)}")
                    return None
            except Exception as e:
                logger.error(f"Failed to process WIA image data: {e}")
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
                manager = self._get_manager()
                if manager:
                    device_count = manager.DeviceInfos.Count
                    diagnostics["device_count"] = device_count
                    diagnostics["discovered_devices"] = list(self._devices.keys())
                else:
                    diagnostics["error"] = "Failed to create DeviceManager for diagnostics"

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
