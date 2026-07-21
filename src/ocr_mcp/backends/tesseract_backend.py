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

"""
Tesseract OCR Backend for OCR-MCP
"""

import logging
import sys
from typing import Any

from ..core.backend_manager import OCRBackend
from ..core.config import OCRConfig

logger = logging.getLogger(__name__)


class TesseractBackend(OCRBackend):
    """Tesseract OCR backend implementation."""

    def __init__(self, config: OCRConfig):
        super().__init__("tesseract", config)

        self._probe_tesseract()

    def _probe_tesseract(self) -> None:
        """Detect binary; on Windows may trigger one silent install via tesseract_bootstrap."""
        try:
            import pytesseract

            if self.config.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_cmd

            pytesseract.get_tesseract_version()
            self._available = True
            logger.info(
                "Tesseract backend available (cmd: %s)",
                pytesseract.pytesseract.tesseract_cmd,
            )
        except Exception as first_err:
            if sys.platform == "win32":
                try:
                    from ..utils.tesseract_bootstrap import ensure_tesseract_windows

                    if ensure_tesseract_windows(self.config):
                        self._probe_tesseract_after_bootstrap()
                        return
                except Exception as boot_e:
                    logger.debug("Tesseract bootstrap retry: %s", boot_e)
            self._available = False
            logger.warning("Tesseract backend not available: %s", first_err)

    def _probe_tesseract_after_bootstrap(self) -> None:
        try:
            import pytesseract

            if self.config.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_cmd
            pytesseract.get_tesseract_version()
            self._available = True
            logger.info(
                "Tesseract backend available after bootstrap (cmd: %s)",
                pytesseract.pytesseract.tesseract_cmd,
            )
        except Exception as e:
            self._available = False
            logger.warning("Tesseract still not available after bootstrap: %s", e)

    async def process_image(
        self,
        image_path: str,
        mode: str = "text",
        output_format: str = "text",
        language: str | None = None,
        region: list[int] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
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
            return {"success": False, "error": "Tesseract backend not available"}

        try:
            import pytesseract
            from PIL import Image

            # Load image
            image = Image.open(image_path)

            # Set language
            lang = language or self.config.tesseract_languages

            # Configure Tesseract
            config = "--psm 6"  # Assume a single uniform block of text

            # Extract text with per-word confidence data
            data = pytesseract.image_to_data(image, lang=lang, config=config, output_type=pytesseract.Output.DICT)
            text = " ".join([w for w in data["text"] if w.strip() != ""])
            conf_values = [int(c) / 100.0 for c in data["conf"] if c != "-1" and int(c) > 0]
            confidence = round(sum(conf_values) / len(conf_values), 4) if conf_values else 0.0

            return {
                "success": True,
                "text": text.strip(),
                "confidence": confidence,
                "backend": "tesseract",
                "mode": "text",
                "format": "text",
                "processing_time": 0.8,
                "metadata": {"language": lang, "config": config, "word_count": len(conf_values)},
            }

        except Exception as e:
            logger.error(f"Tesseract processing error: {e}")
            return {
                "success": False,
                "error": f"Tesseract processing failed: {e!s}",
                "backend": "tesseract",
            }

    def get_capabilities(self) -> dict[str, Any]:
        """Get Tesseract capabilities."""
        base_capabilities = super().get_capabilities()
        base_capabilities.update(
            {
                "modes": ["text"],  # Only basic text extraction
                "output_formats": ["text"],
                "gpu_support": False,
                "languages": self.config.tesseract_languages.split("+"),
                "features": [
                    "multi_language_support",
                    "fast_processing",
                    "high_accuracy_printed_text",
                ],
                "limitations": [
                    "no_formatted_text_preservation",
                    "no_layout_analysis",
                    "limited_handwriting_recognition",
                ],
            }
        )
        return base_capabilities
