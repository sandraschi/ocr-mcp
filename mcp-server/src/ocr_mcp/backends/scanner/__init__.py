"""
Scanner Backends Package
"""

from .scanner_manager import ScannerManager, scanner_manager
from .wia_scanner import WIABackend, ScannerInfo, ScanSettings, ScannerProperties

__all__ = [
    "ScannerManager",
    "scanner_manager",
    "WIABackend",
    "ScannerInfo",
    "ScanSettings",
    "ScannerProperties"
]






