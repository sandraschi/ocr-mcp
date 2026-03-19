import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from ocr_mcp.core.config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("download_models")


def download_models():
    """Download all OCR models to persistent storage."""
    logger.info(f"Starting model downloads to: {config.model_dir}")
    config.model_dir.mkdir(parents=True, exist_ok=True)

    # 1. Florence-2
    try:
        logger.info("Downloading Florence-2...")
        from huggingface_hub import snapshot_download

        model_name = "microsoft/Florence-2-base"
        cache_dir = config.model_dir / "florence"

        snapshot_download(repo_id=model_name, local_dir=cache_dir, local_dir_use_symlinks=False)
        logger.info("Florence-2 downloaded successfully.")
    except Exception as e:
        logger.error(f"Failed to download Florence-2: {e}")

    # 2. GOT-OCR 2.0
    try:
        logger.info("Downloading GOT-OCR 2.0...")
        from huggingface_hub import snapshot_download

        model_name = "stepfun-ai/GOT-OCR2_0"
        cache_dir = config.model_dir / "got_ocr"

        snapshot_download(repo_id=model_name, local_dir=cache_dir, local_dir_use_symlinks=False)
        logger.info("GOT-OCR 2.0 downloaded successfully.")
    except Exception as e:
        logger.error(f"Failed to download GOT-OCR 2.0: {e}")

    # 3. EasyOCR
    try:
        logger.info("Downloading EasyOCR models...")
        import easyocr

        model_dir = config.model_dir / "easyocr"
        model_dir.mkdir(parents=True, exist_ok=True)

        # This triggers download
        easyocr.Reader(["en"], gpu=False, model_storage_directory=str(model_dir), verbose=True)
        logger.info("EasyOCR models downloaded successfully.")
    except Exception as e:
        logger.error(f"Failed to download EasyOCR: {e}")


if __name__ == "__main__":
    download_models()
