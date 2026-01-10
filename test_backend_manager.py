import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

try:
    from ocr_mcp.core.backend_manager import BackendManager
    from ocr_mcp.core.config import OCRConfig

    logger.info("Initializing BackendManager...")
    config = OCRConfig()
    backend_manager = BackendManager(config)

    if backend_manager.scanner_manager:
        logger.info("ScannerManager found")
        if backend_manager.scanner_manager.is_available():
            logger.info("ScannerManager is available")

            logger.info("Discovering scanners via BackendManager...")
            scanners = backend_manager.scanner_manager.discover_scanners(
                force_refresh=True
            )
            logger.info(f"Found {len(scanners)} scanners")
            for scanner in scanners:
                logger.info(f" - {scanner.name} ({scanner.device_id})")
        else:
            logger.error("ScannerManager is NOT available")
    else:
        logger.error("ScannerManager is None")

except Exception as e:
    logger.exception(f"Test failed: {e}")
