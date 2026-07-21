"""Scanner watcher service — auto-detect documents on flatbed.

Two detection modes:
  - preview: Poll low-res preview, detect content changes via image hash (universal).
  - button: Poll WIA for pending scan button events (scanner-dependent).

When triggered, performs full scan + OCR and stores result as a job.
"""

import asyncio
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageChops

    PIL_OK = True
except ImportError:
    PIL_OK = False

_SCANS_DIR = Path(os.environ.get("OCR_SCANS_DIR", "scans"))
_SCANS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class WatcherConfig:
    enabled: bool = False
    mode: str = "preview"  # "preview", "button", "both"
    interval_s: float = 3.0
    change_threshold: float = 0.05  # 5% pixel change = document detected
    backend: str = "unlimited-ocr"
    device_id: str = ""
    stabilize_frames: int = 2  # consecutive detections before trigger
    auto_ocr: bool = True


@dataclass
class WatcherStatus:
    running: bool = False
    mode: str = "preview"
    device_id: str = ""
    last_event: str = ""
    last_event_time: float = 0.0
    scans_triggered: int = 0
    preview_hash: str = ""


class ScannerWatcher:
    """Background watcher that polls scanner for auto-scan triggers."""

    def __init__(self, scan_fn: Callable | None = None, ocr_fn: Callable | None = None):
        self.config = WatcherConfig()
        self._task: asyncio.Task | None = None
        self._status = WatcherStatus()
        self._baseline_hash: str | None = None
        self._detection_count = 0
        self.scan_fn = scan_fn
        self.ocr_fn = ocr_fn

    def _dhash(self, image: Image.Image, hash_size: int = 8) -> str:
        """Compute a perceptual hash (dHash) for an image."""
        img = image.convert("L").resize((hash_size + 1, hash_size), Image.LANCZOS)
        diff = []
        for row in range(hash_size):
            for col in range(hash_size):
                left = img.getpixel((col, row))
                right = img.getpixel((col + 1, row))
                diff.append("1" if left > right else "0")
        return hex(int("".join(diff), 2))

    def _hash_distance(self, h1: str, h2: str) -> float:
        """Normalized Hamming distance between two hex hashes."""
        if not h1 or not h2:
            return 1.0
        b1 = bin(int(h1, 16))[2:].zfill(64)
        b2 = bin(int(h2, 16))[2:].zfill(64)
        return sum(1 for a, b in zip(b1, b2) if a != b) / max(len(b1), 1)

    async def _take_preview(self) -> Image.Image | None:
        """Take a low-res preview scan."""
        if not self.scan_fn:
            return None
        try:
            preview_settings = {
                "dpi": 75,
                "color_mode": "Grayscale",
                "scan_area": (0, 0, 300, 300),
            }
            result = self.scan_fn(self.config.device_id, preview_settings)
            if isinstance(result, Image.Image):
                return result
            if hasattr(result, "save"):
                return result
            return None
        except Exception as e:
            logger.debug("Preview scan failed: %s", e)
            return None

    async def _check_button_event(self) -> bool:
        """Check if the scanner button was pressed (WIA event polling)."""
        if not self.config.mode in ("button", "both"):
            return False
        try:
            from comtypes.client import CreateObject
            dev_mgr = CreateObject("{E1C5D730-1228-487F-9675-91F3E1F5483E}")
            for info in dev_mgr.DeviceInfos:
                if not self.config.device_id or str(info.DeviceID) == self.config.device_id:
                    try:
                        events = info.Events
                        if events and events.Count > 0:
                            for evt in events:
                                eid = str(evt.EventID)
                                if "C00" in eid or "Scan" in str(evt.Name):
                                    return True
                    except Exception:
                        pass
        except Exception as e:
            logger.debug("Button event check failed: %s", e)
        return False

    def _check_content_change(self, preview: Image.Image) -> float:
        """Compare preview to baseline, return change ratio."""
        current_hash = self._dhash(preview)
        self._status.preview_hash = current_hash
        if self._baseline_hash is None:
            self._baseline_hash = current_hash
            return 0.0
        return self._hash_distance(self._baseline_hash, current_hash)

    def reset_baseline(self):
        """Reset the baseline so next preview becomes the new baseline."""
        self._baseline_hash = None
        self._detection_count = 0

    async def _trigger_scan(self, source: str):
        """Execute a full scan + OCR when document is detected."""
        self._status.last_event = f"{source} trigger"
        self._status.last_event_time = time.time()
        self._status.scans_triggered += 1
        logger.info("Auto-scan triggered via %s on %s", source, self.config.device_id)

        if self.scan_fn:
            try:
                scan_settings = {"dpi": 300, "color_mode": "Color"}
                scan_result = self.scan_fn(self.config.device_id, scan_settings)
                if scan_result:
                    img_path = _SCANS_DIR / f"auto_scan_{uuid.uuid4().hex}.png"
                    if isinstance(scan_result, Image.Image):
                        scan_result.save(img_path)
                    elif hasattr(scan_result, "save"):
                        scan_result.save(img_path)
                    else:
                        logger.warning("Unexpected scan result type: %s", type(scan_result))
                        return

                    if self.ocr_fn and self.config.auto_ocr:
                        await self.ocr_fn(str(img_path), self.config.backend)
                    logger.info("Auto-scan saved: %s", img_path)
            except Exception as e:
                logger.error("Auto-scan failed: %s", e)

    async def _watch_loop(self):
        """Main polling loop."""
        self._baseline_hash = None
        self._detection_count = 0

        while self.config.enabled:
            try:
                triggered = False

                if self.config.mode in ("button", "both"):
                    if await self._check_button_event():
                        await self._trigger_scan("button")
                        triggered = True

                if not triggered and self.config.mode in ("preview", "both"):
                    preview = await self._take_preview()
                    if preview:
                        change = self._check_content_change(preview)
                        if change > self.config.change_threshold:
                            self._detection_count += 1
                            if self._detection_count >= self.config.stabilize_frames:
                                self._detection_count = 0
                                await self._trigger_scan("preview")
                                self.reset_baseline()
                        else:
                            self._detection_count = 0

                await asyncio.sleep(self.config.interval_s)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Watcher loop error: %s", e)
                await asyncio.sleep(self.config.interval_s)

    async def start(self, config: WatcherConfig):
        """Start the watcher with the given config."""
        if self._task and not self._task.done():
            await self.stop()
        self.config = config
        self.config.enabled = True
        self._status = WatcherStatus(
            running=True,
            mode=config.mode,
            device_id=config.device_id,
        )
        self._task = asyncio.create_task(self._watch_loop())
        logger.info("Scanner watcher started (mode=%s, interval=%.1fs)", config.mode, config.interval_s)

    async def stop(self):
        """Stop the watcher."""
        self.config.enabled = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._status.running = False
        logger.info("Scanner watcher stopped")

    def get_status(self) -> dict[str, Any]:
        """Get current watcher status."""
        return {
            "running": self._status.running,
            "mode": self._status.mode,
            "device_id": self._status.device_id,
            "last_event": self._status.last_event,
            "last_event_time": self._status.last_event_time,
            "scans_triggered": self._status.scans_triggered,
            "interval_s": self.config.interval_s,
            "change_threshold": self.config.change_threshold,
            "auto_ocr": self.config.auto_ocr,
            "backend": self.config.backend,
        }


_watcher_instance: ScannerWatcher | None = None


def get_watcher() -> ScannerWatcher:
    global _watcher_instance
    if _watcher_instance is None:
        _watcher_instance = ScannerWatcher()
    return _watcher_instance
