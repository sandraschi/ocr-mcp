import logging
logger = logging.getLogger(__name__)
import asyncio
import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(os.getcwd()) / "src"))

from ocr_mcp.core.backend_manager import BackendManager
from ocr_mcp.core.config import OCRConfig


asynasync def test_ocr_backends():
    config = OCRConfig()
    manager = BackendManager(config)

    image_path = "tests/fixtures/test_sample.png"
    if not os.path.exists(image_path):
        logger.info(f"Error: Test image not found at {image_path}")
        return

    # Backends to test
    backends_to_test = ["tesseract", "easyocr", "pp-ocrv5", "mistral-ocr", "got-ocr"]

    logger.info(f"Starting OCR Multi-Backend Test")
    logger.info(f"Source Image: {os.path.abspath(image_path)}")
    logger.info("-" * 60)

    for backend in backends_to_test:
        logger.info(f"\n[Testing Backend: {backend}]")
        try:
            start_time = time.time()
            result = await manager.process_with_backend(
                backend_name=backend, image_path=image_path, mode="text"
            )
            duration = time.time() - start_time

            # Print extraction results
            text = result.get("text", "").strip()
            logger.info(f"Status: SUCCESS")
            logger.info(f"Processing Time: {duration:.2f}s")
            logger.info("Extracted Text (first 200 chars):")
            logger.info(">" * 20)
            logger.info(text[:200] + ("..." if len(text) > 200 else ""))
            logger.info(">" * 20)

        except Exception as e:
            logger.info(f"Status: FAILED")
            logger.info(f"Error: {e}")

    logger.info("-" * 60)
    logger.info("OCR Multi-Backend Test Completed")


if __name__ == "__main__":
    asyncio.run(test_ocr_backends())
