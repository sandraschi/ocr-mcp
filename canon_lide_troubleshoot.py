#!/usr/bin/env python3
"""
Canon LiDE 300 Scanner Troubleshooting Script

This script helps diagnose and troubleshoot Canon LiDE 300 scanner connectivity issues.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ocr_mcp.backends.scanner.scanner_manager import ScannerManager
from ocr_mcp.tools._scanner import handle_scanner_op

def troubleshoot_canon_lide():
    """Comprehensive troubleshooting for Canon LiDE 300 scanner."""
    print("Canon LiDE 300 Scanner Troubleshooting")
    print("=" * 50)

    try:
        # Step 1: Check backend availability
        print("\n1. Checking scanner backend availability...")
        manager = ScannerManager()
        available = manager.is_available()
        print(f"   Backend available: {available}")

        if not available:
            print("   ERROR: Scanner backend not available!")
            print("   - Ensure you're running on Windows")
            print("   - Install comtypes: pip install comtypes")
            return

        # Step 2: Get backend diagnostics
        print("\n2. Getting backend diagnostics...")
        status = manager.get_backend_status()
        print(f"   Backend status: {status}")
        wia_available = status.get('wia', False)
        bridge_available = status.get('bridge', False)
        print(f"   WIA backend: {wia_available}")
        print(f"   Bridge backend: {bridge_available}")

        # Step 3: Discover scanners
        print("\n3. Discovering connected scanners...")
        scanners = manager.discover_scanners(force_refresh=True)
        print(f"   Found {len(scanners)} scanner(s)")

        canon_scanners = [s for s in scanners if 'canon' in s.manufacturer.lower() or 'canon' in s.name.lower()]
        if canon_scanners:
            print(f"   Found {len(canon_scanners)} Canon scanner(s):")
            for scanner in canon_scanners:
                print(f"     - {scanner.name} (ID: {scanner.device_id})")
                print(f"       Manufacturer: {scanner.manufacturer}")
                print(f"       Type: {scanner.device_type}")
                print(f"       Max DPI: {scanner.max_dpi}")
                print(f"       Supports ADF: {scanner.supports_adf}")
        else:
            print("   WARNING: No Canon scanners detected!")
            print("   - Ensure scanner is powered on")
            print("   - Check USB connection")
            print("   - Try different USB port")
            return

        # Step 4: Test scanner properties
        print("\n4. Testing scanner properties...")
        test_scanner = canon_scanners[0]
        properties = manager.get_scanner_properties(test_scanner.device_id)

        if properties:
            print("   Properties retrieved successfully:")
            print(f"     - Supported resolutions: {getattr(properties, 'supported_resolutions', [])}")
            print(f"     - Color modes: {getattr(properties, 'supported_color_modes', [])}")
            print(f"     - Max dimensions: {getattr(properties, 'max_paper_width', 0)}x{getattr(properties, 'max_paper_height', 0)}")
            print(f"     - Manufacturer: {getattr(properties, 'manufacturer', 'Unknown')}")
            print(f"     - Model: {getattr(properties, 'model', 'Unknown')}")
        else:
            print("   ERROR: Could not retrieve scanner properties!")
            print("   - Device may be busy or unresponsive")
            print("   - Try power cycling the scanner")

        # Step 5: Test configuration
        print("\n5. Testing scanner configuration...")
        config_result = manager.configure_scan(test_scanner.device_id, {
            'dpi': 300,
            'color_mode': 'Color',
            'paper_size': 'A4',
            'brightness': 0,
            'contrast': 0,
            'use_adf': False,
            'duplex': False
        })

        if config_result:
            print("   Configuration successful")
        else:
            print("   ERROR: Configuration failed!")
            print("   - Scanner may not support these settings")
            print("   - Device may be busy")

        # Step 6: Provide recommendations
        print("\n6. Troubleshooting Recommendations:")
        print("   - Power cycle the Canon LiDE 300 scanner")
        print("   - Ensure scanner is properly connected via USB")
        print("   - Close any other scanning applications")
        print("   - Update Canon scanner drivers from official website")
        print("   - Disable USB selective suspend in Power Options")
        print("   - Try scanning from Windows Fax and Scan first")

        print("\n7. Next Steps:")
        print("   - Try a test scan using the OCR-MCP web interface")
        print("   - Check Windows Device Manager for scanner status")
        print("   - Run 'diagnostics' operation in OCR-MCP for more details")

    except Exception as e:
        print(f"\nERROR during troubleshooting: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    troubleshoot_canon_lide()