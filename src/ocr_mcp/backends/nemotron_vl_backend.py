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
Llama Nemotron Nano VL 8B Backend (NVIDIA, June 2025)
Built on Llama-3.1-8B-Instruct with C-RADIOv2-H vision encoder.
Best-in-class document intelligence: DocVQA 91.2%, ChartQA 86.3%, AI2D 85.0%.
HF: nvidia/Llama-3.1-Nemotron-Nano-VL-8B-V1

Uses AutoModel + AutoImageProcessor + .chat() API — different from standard
AutoModelForCausalLM + AutoProcessor used by other VLM backends.
Requires: transformers, accelerate, timm, einops, open-clip-torch.
"""

import logging
import time
from typing import Any

from ..core.backend_manager import OCRBackend
from ..core.config import OCRConfig

logger = logging.getLogger(__name__)

_NEMOTRON_OCR_PROMPT = (
    "Please extract all text from this document image. "
    "Output the text in reading order, preserving the layout as much as possible. "
    "For tables, use markdown table format. "
    "For charts and diagrams, describe them briefly then extract any visible text. "
    "Do not include any commentary, just the extracted text."
)

_NEMOTRON_TABLE_PROMPT = (
    "Extract all tables from this image. "
    "Output each table in markdown format. "
    "Include all headers, rows, and cell values exactly as they appear. "
    "Do not include any other text or commentary."
)


class NemotronVLBackend(OCRBackend):
    """Llama Nemotron Nano VL 8B — NVIDIA document intelligence VLM (June 2025)."""

    def __init__(self, config: OCRConfig):
        super().__init__("nemotron-vl", config)
        self._model = None
        self._tokenizer = None
        self._image_processor = None
        self.model_name = "nvidia/Llama-3.1-Nemotron-Nano-VL-8B-V1"
        self.cache_dir = config.model_dir / "nemotron-vl"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._device = None

        import importlib.util

        self._torch_ok = importlib.util.find_spec("torch") is not None
        self._transformers_ok = importlib.util.find_spec("transformers") is not None
        self._timm_ok = importlib.util.find_spec("timm") is not None
        self._open_clip_ok = importlib.util.find_spec("open_clip_torch") is not None

        if all([self._torch_ok, self._transformers_ok]):
            self._available = True
            if not self._timm_ok:
                logger.warning("Nemotron VL: 'timm' not installed — required for vision encoder")
            if not self._open_clip_ok:
                logger.warning("Nemotron VL: 'open-clip-torch' not installed — required for vision encoder")
        else:
            self._available = False
            logger.warning("Nemotron VL: torch or transformers not available")

    def _load_model(self):
        if self._model is not None:
            return
        if not self.is_available():
            raise RuntimeError("Nemotron VL dependencies not available")

        try:
            import torch
            from transformers import AutoImageProcessor, AutoModel, AutoTokenizer

            self._device = "cuda" if torch.cuda.is_available() else "cpu"

            logger.info(f"Loading Nemotron VL (8B) on {self._device}...")
            t0 = time.time()

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=str(self.cache_dir),
            )

            self._image_processor = AutoImageProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                device=self._device,
                cache_dir=str(self.cache_dir),
            )

            self._model = AutoModel.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                device_map="auto" if self._device == "cuda" else "cpu",
                cache_dir=str(self.cache_dir),
            )
            self._model.eval()

            logger.info(f"Nemotron VL loaded in {time.time() - t0:.1f}s")

        except Exception as e:
            logger.error(f"Failed to load Nemotron VL: {e}")
            raise RuntimeError(f"Nemotron VL load failed: {e}") from e

    async def process_image(
        self,
        image_path: str,
        mode: str = "text",
        output_format: str = "text",
        language: str | None = None,
        region: list[int] | None = None,
        custom_prompt: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Process image with Nemotron VL."""
        if not self.is_available():
            return {"success": False, "error": "Nemotron VL not available"}

        try:
            from PIL import Image

            self._load_model()
            t0 = time.time()

            img = Image.open(image_path).convert("RGB")
            if region and len(region) == 4:
                img = img.crop(tuple(region))

            image_features = self._image_processor([img])

            if mode == "table":
                prompt = custom_prompt or _NEMOTRON_TABLE_PROMPT
            else:
                prompt = custom_prompt or _NEMOTRON_OCR_PROMPT

            generation_config = dict(
                max_new_tokens=4096,
                do_sample=False,
                eos_token_id=self._tokenizer.eos_token_id,
            )

            text = self._model.chat(
                tokenizer=self._tokenizer,
                question=prompt,
                generation_config=generation_config,
                **image_features,
            )
            text_str = text.strip()
            alpha_chars = sum(1 for c in text_str if c.isalnum() or c in ".,;:!?-()[]{}'\" ")
            confidence = round(alpha_chars / max(len(text_str), 1), 4) if text_str else 0.0

            return {
                "success": True,
                "text": text_str,
                "backend": "nemotron-vl",
                "model": self.model_name,
                "mode": mode,
                "processing_time": time.time() - t0,
                "confidence": confidence,
                "confidence_source": "text_quality_heuristic",
                "confidence_note": ".chat() API does not expose logits",
                "metadata": {
                    "device": self._device,
                    "params": "8B",
                    "benchmarks": {
                        "docvqa": "91.2%",
                        "chartqa": "86.3%",
                        "ai2d": "85.0%",
                        "ocrbench": "839",
                        "infovqa": "77.4%",
                    },
                },
            }

        except Exception as e:
            logger.error(f"Nemotron VL error: {e}")
            return {"success": False, "error": str(e), "backend": "nemotron-vl"}

    def get_capabilities(self) -> dict[str, Any]:
        caps = super().get_capabilities()
        caps.update(
            {
                "name": "Llama Nemotron Nano VL 8B",
                "description": (
                    "NVIDIA Llama Nemotron Nano VL (Jun 2025) — "
                    "best-in-class document intelligence, OCR, and chart understanding"
                ),
                "modes": ["text", "table", "format"],
                "output_formats": ["text", "markdown"],
                "gpu_support": True,
                "model_size": "~16GB (8B params, bfloat16); ~5GB AWQ 4-bit",
                "strengths": [
                    "DocVQA 91.2% — best-in-class document Q&A",
                    "ChartQA 86.3% — top chart understanding",
                    "AI2D 85.0% — scientific diagram parsing",
                    "OCRBench 839 — strong general OCR",
                    "InfoVQA 77.4% — infographic understanding",
                    "Document intelligence specialist — forms, invoices, reports",
                    "Structured data extraction with layout preservation",
                    "Deployable on edge via AWQ 4-bit (Jetson Orin)",
                ],
                "limitations": [
                    "English only — no multilingual OCR",
                    "16K token context (input+output combined)",
                    "Single image only per call",
                    "Requires timm + open-clip-torch deps",
                    "NVIDIA Open Model License (not Apache)",
                ],
                "ideal_for": (
                    "Structured documents, invoices, forms, charts, scientific diagrams, reports with tables"
                ),
            }
        )
        return caps
