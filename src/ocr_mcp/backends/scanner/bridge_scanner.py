import base64
import io
import logging
import os
from dataclasses import asdict
from typing import Any

import requests
from PIL import Image

from .wia_scanner import ScannerInfo, ScannerProperties, ScanSettings

logger = logging.getLogger(__name__)

_DEFAULT_BRIDGE_URL = os.getenv("OCR_SCANNER_BRIDGE_URL", "http://127.0.0.1:15002")


class BridgeScannerBackend:
    """
    Scanner Backend that proxies requests to a remote Bridge Server.
    Used to access Windows Host scanners from within Docker container.

    The bridge URL is configurable via the OCR_SCANNER_BRIDGE_URL env var.
    Defaults to http://127.0.0.1:15002 for native Windows usage.
    Set to http://host.docker.internal:15002 when ocr-mcp runs inside Docker.
    """

    def __init__(self, bridge_url: str | None = None):
        self.bridge_url = (bridge_url or _DEFAULT_BRIDGE_URL).rstrip("/")
        self._available = False
        self._checked = False

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
        self._checked = True

    def is_available(self) -> bool:
        if not self._checked:
            self.check_availability()
            self._checked = True
        return self._available

    def discover_scanners(self) -> list[ScannerInfo]:
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

    def get_scanner_properties(self, device_id: str) -> ScannerProperties | None:
        try:
            resp = requests.get(f"{self.bridge_url}/scanners/{device_id}/properties", timeout=5)
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

    def scan_document(self, device_id: str, settings: ScanSettings) -> Any | None:
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
