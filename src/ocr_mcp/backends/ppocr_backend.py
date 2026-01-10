"""
PP-OCRv5 Backend Implementation
Integrates PaddlePaddle PP-OCRv5 for industrial-grade OCR processing
"""

import logging
from typing import Dict, Any, Optional, List
from PIL import Image
import numpy as np

from ..core.backend_manager import OCRBackend
from ..core.config import OCRConfig

try:
    import paddle
    import paddleocr

    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

logger = logging.getLogger(__name__)


class PPOCRBackend(OCRBackend):
    """PP-OCRv5 backend for high-performance industrial OCR"""

    def __init__(self, config: OCRConfig):
        super().__init__("pp-ocrv5", config)
        self.ocr = None
        self.device = getattr(config, "ocr_device", "cpu") or "cpu"
        self.lang = "en"  # Default lang, can be made configurable
        self.use_gpu = self.device == "cuda" and paddle.device.cuda.device_count() > 0

    def is_available(self) -> bool:
        """Check if PP-OCRv5 is available"""
        if not PADDLE_AVAILABLE:
            return False

        try:
            # Try to initialize OCR
            paddleocr.PaddleOCR(lang=self.lang)
            return True
        except Exception as e:
            logger.warning(f"PP-OCRv5 availability check failed: {e}")
            return False

    async def load_model(self) -> bool:
        """Load the PP-OCRv5 model"""
        if not PADDLE_AVAILABLE:
            logger.error("PaddlePaddle not available for PP-OCRv5")
            return False

        try:
            logger.info(
                f"Loading PP-OCRv5 model (GPU: {self.use_gpu}, Lang: {self.lang})"
            )

            # Initialize PaddleOCR
            self.ocr = paddleocr.PaddleOCR(
                use_gpu=self.use_gpu,
                lang=self.lang,
                show_log=False,
                use_angle_cls=True,  # Text direction detection
                use_space_char=True,  # Space character recognition
            )

            if self.ocr is None:
                logger.error("PaddleOCR initialization returned None")
                return False

            logger.info("PP-OCRv5 model loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load PP-OCRv5 model: {e}")
            return False

    async def process_document(
        self,
        image_path: str,
        ocr_mode: str = "text",
        region: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Process document with PP-OCRv5"""

        if not self.ocr:
            raise RuntimeError("PP-OCRv5 model not loaded")

        try:
            # Load image
            image = Image.open(image_path).convert("RGB")

            # Apply region cropping if specified
            if region and len(region) == 4:
                x1, y1, x2, y2 = region
                image = image.crop((x1, y1, x2, y2))

            # Convert to numpy array
            img_array = np.array(image)

            # Run OCR
            results = self.ocr.ocr(img_array, cls=True)

            # Process results
            processed_results = self._process_ppocr_results(
                results, ocr_mode, image.size
            )

            return processed_results

        except Exception as e:
            logger.error(f"PP-OCRv5 processing failed: {e}")
            raise RuntimeError(f"OCR processing failed: {str(e)}")

    def _process_ppocr_results(
        self, results: List, ocr_mode: str, image_size: tuple
    ) -> Dict[str, Any]:
        """Process PP-OCRv5 results into standardized format"""
        if not results or not results[0]:
            return {"text": "", "backend": "ppocr", "confidence": 0.0, "regions": []}

        # Extract text and regions
        text_parts = []
        regions = []
        total_confidence = 0
        region_count = 0

        for line in results[0]:
            bbox, (text, confidence) = line
            text_parts.append(text)
            total_confidence += confidence
            region_count += 1

            regions.append(
                {
                    "bbox": [int(coord) for coord in bbox],
                    "text": text,
                    "confidence": float(confidence),
                }
            )

        # Combine text
        full_text = " ".join(text_parts)
        avg_confidence = total_confidence / region_count if region_count > 0 else 0

        if ocr_mode == "text":
            return {
                "text": full_text,
                "backend": "ppocr",
                "confidence": float(avg_confidence),
                "regions": [],
            }
        elif ocr_mode == "format":
            return {
                "text": full_text,
                "backend": "ppocr",
                "confidence": float(avg_confidence),
                "structured": self._create_structured_output(regions),
                "regions": [],
            }
        else:  # fine-grained
            return {
                "text": full_text,
                "backend": "ppocr",
                "confidence": float(avg_confidence),
                "regions": regions,
                "structured": {},
            }

    def _create_structured_output(
        self, regions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create structured output from PP-OCRv5 regions"""
        # Group regions by lines and paragraphs
        if not regions:
            return {"paragraphs": [], "lines": []}

        # Sort by vertical position (top to bottom)
        sorted_regions = sorted(regions, key=lambda r: r["bbox"][1])

        lines = []
        current_line = []
        current_y = sorted_regions[0]["bbox"][1]

        for region in sorted_regions:
            # Group regions on similar Y coordinates as lines
            if abs(region["bbox"][1] - current_y) < 10:  # Same line threshold
                current_line.append(region)
            else:
                if current_line:
                    lines.append(current_line)
                current_line = [region]
                current_y = region["bbox"][1]

        if current_line:
            lines.append(current_line)

        return {
            "paragraphs": [" ".join([r["text"] for r in line]) for line in lines],
            "lines": lines,
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get backend capabilities"""
        return {
            "name": "PP-OCRv5",
            "available": self.is_available(),
            "modes": ["text", "format", "fine-grained"],
            "languages": ["en", "ch", "japan", "korean", "multilingual"],
            "gpu_support": True,
            "strengths": ["speed", "accuracy", "industrial_use", "cpu_efficient"],
            "limitations": ["gpu_optional", "language_specific"],
            "model_size": "~100MB",
        }
