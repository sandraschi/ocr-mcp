"""
DOTS.OCR Backend Implementation
Integrates DOTS.OCR for document understanding and structured content extraction
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import torch
from PIL import Image

from ..core.backend_manager import OCRBackend
from ..core.config import OCRConfig

try:
    from transformers import AutoModelForCausalLM, AutoProcessor

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)


class DOTSBackend(OCRBackend):
    """DOTS.OCR backend for document structure analysis and content extraction"""

    def __init__(self, config: OCRConfig):
        super().__init__("dots-ocr", config)
        self.model = None
        self.processor = None
        self.device = getattr(config, "ocr_device", None) or (
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        self.model_name = "rednote-hilab/dots.ocr"
        self.cache_dir = Path(
            getattr(config, "ocr_cache_dir", None) or Path.home() / ".cache" / "ocr_mcp"
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def is_available(self) -> bool:
        """Check if DOTS.OCR is available"""
        if not TRANSFORMERS_AVAILABLE:
            return False

        try:
            from huggingface_hub import model_info

            model_info(self.model_name)
            return True
        except Exception as e:
            logger.warning(f"DOTS.OCR model check failed: {e}")
            return False

    async def load_model(self) -> bool:
        """Load the DOTS.OCR model"""
        if not TRANSFORMERS_AVAILABLE:
            logger.error("Transformers not available for DOTS.OCR")
            return False

        try:
            logger.info(f"Loading DOTS.OCR model on {self.device}")

            # Load processor and model
            self.processor = AutoProcessor.from_pretrained(
                self.model_name, cache_dir=str(self.cache_dir), trust_remote_code=True
            )

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                cache_dir=str(self.cache_dir),
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
            )

            if self.device == "cpu":
                self.model = self.model.to(self.device)

            logger.info("DOTS.OCR model loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load DOTS.OCR model: {e}")
            return False

    async def process_document(
        self,
        image_path: str,
        ocr_mode: str = "text",
        region: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Process document with DOTS.OCR"""

        if not self.model or not self.processor:
            raise RuntimeError("DOTS.OCR model not loaded")

        try:
            # Load and preprocess image
            image = Image.open(image_path).convert("RGB")

            # Apply region cropping if specified
            if region and len(region) == 4:
                x1, y1, x2, y2 = region
                image = image.crop((x1, y1, x2, y2))

            # Prepare task-specific prompt
            task_prompt = self._get_task_prompt(ocr_mode)

            # Process image
            inputs = self.processor(images=image, text=task_prompt, return_tensors="pt")

            if self.device == "cuda":
                inputs = {k: v.cuda() for k, v in inputs.items()}

            # Generate structured output
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=2048,
                    num_beams=3,
                    do_sample=False,
                    early_stopping=True,
                )

            # Decode and parse results
            raw_output = self.processor.decode(outputs[0], skip_special_tokens=True)
            result = self._parse_dots_output(raw_output, ocr_mode, image.size)

            return result

        except Exception as e:
            logger.error(f"DOTS.OCR processing failed: {e}")
            raise RuntimeError(f"OCR processing failed: {str(e)}")

    def _get_task_prompt(self, ocr_mode: str) -> str:
        """Get task-specific prompt for DOTS.OCR"""
        prompts = {
            "text": "Extract all text from this document.",
            "format": "Extract text with layout information from this document.",
            "fine-grained": "Extract text with precise region information from this document.",
        }
        return prompts.get(ocr_mode, prompts["text"])

    def _parse_dots_output(
        self, raw_output: str, ocr_mode: str, image_size: tuple
    ) -> Dict[str, Any]:
        """Parse DOTS.OCR structured output"""
        # DOTS.OCR provides rich structured output
        parsed = self._parse_json_output(raw_output)

        if ocr_mode == "text":
            return {
                "text": parsed.get("text", "").strip(),
                "backend": "dots",
                "confidence": parsed.get("confidence", 0.90),
                "regions": [],
            }
        elif ocr_mode == "format":
            return {
                "text": parsed.get("text", "").strip(),
                "backend": "dots",
                "confidence": parsed.get("confidence", 0.90),
                "structured": parsed.get("structure", {}),
                "regions": [],
            }
        else:  # fine-grained
            return {
                "text": parsed.get("text", "").strip(),
                "backend": "dots",
                "confidence": parsed.get("confidence", 0.90),
                "regions": parsed.get("regions", []),
                "structured": parsed.get("structure", {}),
            }

    def _parse_json_output(self, raw_output: str) -> Dict[str, Any]:
        """Parse JSON output from DOTS.OCR"""
        try:
            # Try to parse as JSON first
            return json.loads(raw_output)
        except json.JSONDecodeError:
            # Fallback to structured text parsing
            return self._parse_text_output(raw_output)

    def _parse_text_output(self, raw_output: str) -> Dict[str, Any]:
        """Fallback parsing for text-based output"""
        # This would implement custom parsing logic for DOTS.OCR text output
        return {
            "text": raw_output.strip(),
            "confidence": 0.90,
            "structure": {},
            "regions": [],
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get backend capabilities"""
        return {
            "name": "DOTS.OCR",
            "available": self.is_available(),
            "modes": ["text", "format", "fine-grained"],
            "languages": ["en", "zh", "multilingual"],
            "gpu_support": True,
            "strengths": [
                "document_structure",
                "table_extraction",
                "formula_recognition",
            ],
            "limitations": ["complex_setup", "resource_intensive"],
            "model_size": "~3GB",
        }
