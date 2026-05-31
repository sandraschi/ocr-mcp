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
sys.path.append(str(Path(__file__).parent.parent / "src"))

from ocr_mcp.core.backend_manager import BackendManager
from ocr_mcp.core.config import OCRConfig


async def run_demo():
    logger.info("=" * 60)
    logger.info("      OCR-MCP REAL-WORLD DEMONSTRATION")
    logger.info("=" * 60)

    # Initialize configuration and manager
    config = OCRConfig()
    manager = BackendManager(config)

    sample_path = str(Path(__file__).parent.parent / "tests" / "fixtures" / "test_sample.png")

    if not os.path.exists(sample_path):
        logger.info(f"ERROR: Sample file not found at {sample_path}")
        return

    # Backends to demonstrate
    backends = ["mistral-ocr", "tesseract"]

    for backend_name in backends:
        logger.info(f"\n>>> Processing with: {backend_name}")

        start_time = time.time()
        try:
            result = await manager.process_with_backend(
                backend_name=backend_name, image_path=sample_path, mode="standard"
            )
            elapsed = time.time() - start_time

            if result.get("success"):
                logger.info(f"Status: SUCCESS (took {elapsed:.2f}s)")
                text = result.get("text", "")
                logger.info("-" * 40)
                logger.info(text[:1000] + ("..." if len(text) > 1000 else ""))
                logger.info("-" * 40)
            else:
                logger.info(f"Status: FAILED - {result.get('error')}")
        except Exception as e:
            logger.info(f"Exception during {backend_name} execution: {e!s}")

    logger.info("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(run_demo())
