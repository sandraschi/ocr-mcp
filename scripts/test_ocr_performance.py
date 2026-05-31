# MIT License
#
# Copyright (c) 2025 OCR-MCP Project
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
#
#
#
#

import logging

logger = logging.getLogger(__name__)
import asyncio
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(os.getcwd()) / "src"))

from ocr_mcp.core.backend_manager import BackendManager
from ocr_mcp.core.config import OCRConfig


async def test_ocr_backends():
    config = OCRConfig()
    manager = BackendManager(config)

    image_path = "tests/fixtures/test_sample.png"
    if not os.path.exists(image_path):
        logger.info(f"Error: Test image not found at {image_path}")
        return

    # Backends to test
    backends_to_test = ["tesseract", "easyocr", "pp-ocrv5", "mistral-ocr", "got-ocr"]

    logger.info("Starting OCR Multi-Backend Test")
    logger.info(f"Source Image: {os.path.abspath(image_path)}")
    logger.info("-" * 60)

    for backend in backends_to_test:
        logger.info(f"\n[Testing Backend: {backend}]")
        try:
            start_time = time.time()
            result = await manager.process_with_backend(backend_name=backend, image_path=image_path, mode="text")
            duration = time.time() - start_time

            # Print extraction results
            text = result.get("text", "").strip()
            logger.info("Status: SUCCESS")
            logger.info(f"Processing Time: {duration:.2f}s")
            logger.info("Extracted Text (first 200 chars):")
            logger.info(">" * 20)
            logger.info(text[:200] + ("..." if len(text) > 200 else ""))
            logger.info(">" * 20)

        except Exception as e:
            logger.info("Status: FAILED")
            logger.info(f"Error: {e}")

    logger.info("-" * 60)
    logger.info("OCR Multi-Backend Test Completed")


if __name__ == "__main__":
    asyncio.run(test_ocr_backends())
