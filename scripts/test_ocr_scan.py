import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ocr_mcp.core.backend_manager import BackendManager
from ocr_mcp.core.config import OCRConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting OCR Pipeline Verification...")

    # Path to the scanned image
    image_path = Path("test_scan_result.png")
    if not image_path.exists():
        logger.error(f"Scan result not found at {image_path.absolute()}")
        return

    try:
        # Initialize Backend Manager
        config = OCRConfig()
        backend_manager = BackendManager(config)

        available = backend_manager.get_available_backends()
        logger.info(f"Available OCR backends: {available}")

        if not available:
            logger.error("No OCR backends available!")
            return

        # Try backends in order of preference
        backends_to_try = ["tesseract", "pp-ocrv5", "easyocr", "florence-2"]
        # Add any other available backends that aren't in our preference list
        for b in available:
            if b not in backends_to_try:
                backends_to_try.append(b)

        success = False
        for backend in backends_to_try:
            if backend not in available:
                continue

            logger.info(f"Attempting OCR with backend: {backend}")
            try:
                # Process the image
                result = await backend_manager.process_with_backend(
                    backend_name=backend, image_path=str(image_path.absolute()), mode="text"
                )

                if result.get("success"):
                    logger.info(f"SUCCESS: OCR processing completed with {backend}.")
                    text = result.get("text", "")
                    logger.info(
                        f"Extracted Text Snippet (first 500 chars):\n{'-' * 40}\n{text[:500]}\n{'-' * 40}"
                    )

                    # Save OCR result to text file
                    output_path = Path("test_ocr_result.txt")
                    output_path.write_text(text, encoding="utf-8")
                    logger.info(f"Full OCR result saved to {output_path.absolute()}")
                    success = True
                    break
                else:
                    logger.warning(
                        f"OCR with {backend} FAILED: {result.get('error', 'Unknown error')}"
                    )
            except Exception as e:
                logger.warning(f"Error using backend {backend}: {e}")

        if not success:
            logger.error("All OCR backends failed or were skipped.")

    except Exception as e:
        logger.error(f"Error during OCR pipeline test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
