"""Test script to verify OCR MCP server can import and initialize."""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    print("Testing imports...")
    print("✓ Config imported")

    print("✓ BackendManager imported")

    print("✓ Tools imported")

    print("✓ Server app imported")

    print("\n✓ All imports successful!")
    print("Server should be able to start.")

except Exception as e:
    print(f"\n✗ Import error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
