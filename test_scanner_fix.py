#!/usr/bin/env python3
"""
Test script to verify scanner fixes for Canon LiDE 300
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ocr_mcp.backends.scanner.scanner_manager import ScannerManager

def test_scanner_diagnostics():
    """Test scanner diagnostics functionality."""
    print("Testing OCR-MCP Scanner Diagnostics")
    print("=" * 50)

    try:
        # Create scanner manager
        manager = ScannerManager()

        # Test backend availability
        print(f"Scanner backend available: {manager.is_available()}")

        # Get backend status
        status = manager.get_backend_status()
        print(f"Backend status: {status}")

        # Test scanner discovery
        print("\nDiscovering scanners...")
        scanners = manager.discover_scanners(force_refresh=True)
        print(f"Found {len(scanners)} scanners")

        for scanner in scanners:
            print(f"  - {scanner.name} ({scanner.device_id}) - {scanner.manufacturer}")

            # Get diagnostics for this scanner
            diagnostics = manager.get_scanner_diagnostics(scanner.device_id)
            if diagnostics:
                print(f"    Diagnostics: {diagnostics}")
            else:
                print("    No diagnostics available")

        print("\nScanner diagnostics test completed successfully!")

    except Exception as e:
        print(f"Scanner diagnostics test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scanner_diagnostics()