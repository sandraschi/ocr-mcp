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


asynasync def run_demo():
    logger.info("=" * 60)
    logger.info("      OCR-MCP REAL-WORLD DEMONSTRATION")
    logger.info("=" * 60)

    # Initialize configuration and manager
    config = OCRConfig()
    manager = BackendManager(config)

    sample_path = str(
        Path(__file__).parent.parent / "tests" / "fixtures" / "test_sample.png"
    )

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
            logger.info(f"Exception during {backend_name} execution: {str(e)}")

    logger.info("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(run_demo())
