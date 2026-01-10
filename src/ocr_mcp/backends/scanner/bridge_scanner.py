import logging
import requests
import base64
import io
from typing import List, Optional, Any
from PIL import Image
from dataclasses import asdict

from .wia_scanner import ScannerInfo, ScannerProperties, ScanSettings

logger = logging.getLogger(__name__)


class BridgeScannerBackend:
    """
    Scanner Backend that proxies requests to a remote Bridge Server.
    Used to access Windows Host scanners from within Docker container.
    """

    def __init__(self, bridge_url: str = "http://host.docker.internal:15002"):
        self.bridge_url = bridge_url.rstrip("/")
        self._available = False
        self.check_availability()

    def check_availability(self):
        try:
            resp = requests.get(f"{self.bridge_url}/", timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                self._available = data.get("backend_available", False)
            else:
                self._available = False
        except Exception:
            self._available = False

    def is_available(self) -> bool:
        # Check periodically or assume available if it was once?
        # For now, let's re-check lazy to avoid startup blocking, or just return last state?
        # Let's do a quick check if we think it's down, otherwise trust it?
        # Better: just return existing state, but maybe have a refresh method?
        # Simple approach: actively check on discover is better.
        # But 'is_available' is called often.
        # Let's perform a lightweight check here or just return True if configured?
        # We will try to ping if not previously available.
        if not self._available:
            self.check_availability()
        return self._available

    def discover_scanners(self) -> List[ScannerInfo]:
        if not self.is_available():
            return []

        try:
            resp = requests.get(f"{self.bridge_url}/scanners", timeout=5)
            if resp.status_code != 200:
                logger.error(f"Bridge discover failed: {resp.text}")
                return []

            data = resp.json()
            scanners = []
            for item in data:
                # Reconstruct ScannerInfo objects
                scanners.append(ScannerInfo(**item))
            return scanners
        except Exception as e:
            logger.error(f"Bridge discover error: {e}")
            return []

    def get_scanner_properties(self, device_id: str) -> Optional[ScannerProperties]:
        try:
            resp = requests.get(
                f"{self.bridge_url}/scanners/{device_id}/properties", timeout=5
            )
            if resp.status_code == 200:
                return ScannerProperties(**resp.json())
        except Exception as e:
            logger.error(f"Bridge properties error: {e}")
        return None

    def configure_scan(self, device_id: str, settings: ScanSettings) -> bool:
        # The bridge handles config at scan time mostly, but we can validate via API if needed.
        # For this simple bridge, we pass settings at scan time.
        # We assume True if bridge is up.
        return self.is_available()

    def scan_document(self, device_id: str, settings: ScanSettings) -> Optional[Any]:
        if not self.is_available():
            return None

        try:
            payload = {"device_id": device_id, "settings": asdict(settings)}

            # Long timeout for scanning
            resp = requests.post(f"{self.bridge_url}/scan", json=payload, timeout=60)

            if resp.status_code != 200:
                logger.error(f"Bridge scan failed: {resp.text}")
                return None

            result = resp.json()
            if result.get("success") and result.get("image_data"):
                img_bytes = base64.b64decode(result["image_data"])
                return Image.open(io.BytesIO(img_bytes))

        except Exception as e:
            logger.error(f"Bridge scan error: {e}")

        return None
