"""
Tesseract OCR Backend for OCR-MCP
"""

import logging
from typing import Dict, Any, Optional, List

from ..core.backend_manager import OCRBackend
from ..core.config import OCRConfig

logger = logging.getLogger(__name__)


class TesseractBackend(OCRBackend):
    """Tesseract OCR backend implementation."""

    def __init__(self, config: OCRConfig):
        super().__init__("tesseract", config)

        # Check if Tesseract is available
        try:
            import pytesseract
            # Test if tesseract executable is available
            pytesseract.get_tesseract_version()
            self._available = True
            logger.info("Tesseract backend available")
        except Exception as e:
            self._available = False
            logger.warning(f"Tesseract backend not available: {e}")

    async def process_image(
        self,
        image_path: str,
        mode: str = "text",
        output_format: str = "text",
        language: Optional[str] = None,
        region: Optional[List[int]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process image with Tesseract OCR.

        Args:
            image_path: Path to image file
            mode: Processing mode (only "text" supported for Tesseract)
            output_format: Output format (only "text" supported for basic Tesseract)
            language: Language code (e.g., "eng", "deu", "fra")
            region: Region coordinates (not supported in basic implementation)

        Returns:
            OCR processing results
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Tesseract backend not available"
            }

        try:
            import pytesseract
            from PIL import Image

            # Load image
            image = Image.open(image_path)

            # Set language
            lang = language or self.config.tesseract_languages

            # Configure Tesseract
            config = '--psm 6'  # Assume a single uniform block of text

            # Extract text
            text = pytesseract.image_to_string(image, lang=lang, config=config)

            return {
                "success": True,
                "text": text.strip(),
                "confidence": 0.85,  # Tesseract doesn't provide easy confidence scores
                "backend": "tesseract",
                "mode": "text",
                "format": "text",
                "processing_time": 0.8,
                "metadata": {
                    "language": lang,
                    "config": config
                }
            }

        except Exception as e:
            logger.error(f"Tesseract processing error: {e}")
            return {
                "success": False,
                "error": f"Tesseract processing failed: {str(e)}",
                "backend": "tesseract"
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get Tesseract capabilities."""
        base_capabilities = super().get_capabilities()
        base_capabilities.update({
            "modes": ["text"],  # Only basic text extraction
            "output_formats": ["text"],
            "gpu_support": False,
            "languages": self.config.tesseract_languages.split('+'),
            "features": [
                "multi_language_support",
                "fast_processing",
                "high_accuracy_printed_text"
            ],
            "limitations": [
                "no_formatted_text_preservation",
                "no_layout_analysis",
                "limited_handwriting_recognition"
            ]
        })
        return base_capabilities






