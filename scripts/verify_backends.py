import logging
logger = logging.getLogger(__name__)
import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(os.getcwd()) / "src"))

from ocr_mcp.core.backend_manager import BackendManager
from ocr_mcp.core.config import OCRConfig


asynasync def check_backends():
    config = OCRConfig()
    manager = BackendManager(config)

    logger.info(f"Checking backends for project root: {os.getcwd()}")
    available_names = manager.get_available_backends()

    logger.info("\nBackend Availability Status:")
    logger.info("-" * 50)
    for name in available_names:
        try:
            backend = manager.get_backend(name)
            if backend:
                is_avail = backend.is_available()
                status = "available" if is_avail else "not_available"
                # Use ASCII for Windows compatibility
                check_mark = "[V]" if is_avail else "[X]"
                logger.info(f"{check_mark} {name:20} : {status}")
            else:
                logger.info(f"[X] {name:20} : instance_not_found")
        except Exception as e:
            logger.info(f"[X] {name:20} : error during check: {e}")

    logger.info("-" * 50)


if __name__ == "__main__":
    asyncio.run(check_backends())
