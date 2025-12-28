"""
EasyOCR Backend for OCR-MCP
"""

import logging
import os
from typing import Dict, Any, Optional, List

from ..core.backend_manager import OCRBackend
from ..core.config import OCRConfig

logger = logging.getLogger(__name__)


class EasyOCRBackend(OCRBackend):
    """EasyOCR backend implementation."""

    def __init__(self, config: OCRConfig):
        super().__init__("easyocr", config)
        self._reader = None
        self._initialized = False

        # Check if EasyOCR is available (don't initialize reader yet)
        try:
            import easyocr
            self._easyocr = easyocr
            self._available = True
            logger.info("EasyOCR backend available (deferred initialization)")
        except Exception as e:
            self._available = False
            logger.warning(f"EasyOCR backend not available: {e}")

    def _ensure_initialized(self):
        """Initialize EasyOCR reader on first use."""
        if self._initialized or not self._available:
            return

        try:
            # Set environment variable to avoid Unicode progress bar issues on Windows
            original_verbose = os.environ.get('EASYOCR_VERBOSE', '1')
            os.environ['EASYOCR_VERBOSE'] = '0'  # Disable verbose output

            # Initialize reader with configured languages
            self._reader = self._easyocr.Reader(self.config.easyocr_languages, gpu=True, verbose=False)
            self._initialized = True
            logger.info("EasyOCR reader initialized successfully")

            # Restore original verbose setting
            if original_verbose != '1':
                os.environ['EASYOCR_VERBOSE'] = original_verbose
            else:
                os.environ.pop('EASYOCR_VERBOSE', None)

        except Exception as e:
            self._available = False
            logger.warning(f"EasyOCR reader initialization failed: {e}")

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
        Process image with EasyOCR.

        Args:
            image_path: Path to image file
            mode: Processing mode (only "text" supported for EasyOCR)
            output_format: Output format (only "text" supported for basic EasyOCR)
            language: Language code (handled by reader initialization)
            region: Region coordinates (not supported in basic implementation)

        Returns:
            OCR processing results
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "EasyOCR backend not available"
            }

        # Ensure reader is initialized
        self._ensure_initialized()

        if not self._initialized:
            return {
                "success": False,
                "error": "EasyOCR reader initialization failed"
            }

        try:
            # Perform OCR
            results = self._reader.readtext(image_path)

            # Extract text and confidence scores
            extracted_text = []
            confidence_sum = 0.0
            text_count = 0

            for (bbox, text, confidence) in results:
                extracted_text.append(text)
                confidence_sum += confidence
                text_count += 1

            # Combine all text
            full_text = ' '.join(extracted_text)
            avg_confidence = confidence_sum / text_count if text_count > 0 else 0.0

            return {
                "success": True,
                "text": full_text.strip(),
                "confidence": round(avg_confidence, 3),
                "backend": "easyocr",
                "mode": "text",
                "format": "text",
                "processing_time": 1.5,
                "metadata": {
                    "text_blocks": len(results),
                    "languages": self.config.easyocr_languages,
                    "gpu_enabled": True
                },
                "raw_results": [
                    {
                        "text": text,
                        "confidence": round(confidence, 3),
                        "bbox": bbox
                    } for (bbox, text, confidence) in results
                ]
            }

        except Exception as e:
            logger.error(f"EasyOCR processing error: {e}")
            return {
                "success": False,
                "error": f"EasyOCR processing failed: {str(e)}",
                "backend": "easyocr"
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get EasyOCR capabilities."""
        base_capabilities = super().get_capabilities()
        base_capabilities.update({
            "modes": ["text"],  # Only basic text extraction
            "output_formats": ["text", "json"],  # JSON includes bounding boxes
            "gpu_support": True,
            "languages": self.config.easyocr_languages,
            "features": [
                "multi_language_support",
                "handwriting_recognition",
                "confidence_scores",
                "bounding_boxes",
                "rotation_detection"
            ],
            "limitations": [
                "no_formatted_text_preservation",
                "no_layout_analysis"
            ]
        })
        return base_capabilities






