"""Test script to verify OCR MCP server can import and initialize."""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    print("Testing imports...")
    from ocr_mcp.core.config import OCRConfig
    print("✓ Config imported")
    
    from ocr_mcp.core.backend_manager import BackendManager
    print("✓ BackendManager imported")
    
    from ocr_mcp.tools.ocr_tools import register_sota_tools
    print("✓ Tools imported")
    
    from ocr_mcp.server import app
    print("✓ Server app imported")
    
    print("\n✓ All imports successful!")
    print("Server should be able to start.")
    
except Exception as e:
    print(f"\n✗ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
