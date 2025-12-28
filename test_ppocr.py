#!/usr/bin/env python3
"""
Quick test script for PP-OCRv5 backend
"""
import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ocr_mcp.backends.ppocr_backend import PPOCRBackend
from ocr_mcp.core.config import OCRConfig

async def test_ppocr():
    """Test PP-OCRv5 backend"""
    print("Testing PP-OCRv5 backend...")

    # Create config
    config = OCRConfig(cache_dir=os.path.join(os.path.dirname(__file__), 'cache'))

    backend = PPOCRBackend(config.__dict__)

    # Check if available
    available = backend.is_available()
    print(f"PP-OCRv5 available: {available}")

    if not available:
        print("PP-OCRv5 backend not available - check installation")
        return

    # Try to process a simple image (we'll create a test image if needed)
    print("PP-OCRv5 backend is ready for OCR processing!")

if __name__ == "__main__":
    asyncio.run(test_ppocr())
