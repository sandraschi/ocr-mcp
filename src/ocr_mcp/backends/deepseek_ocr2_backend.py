"""
DeepSeek-OCR-2 Backend
January 2026. "Visual Causal Flow" architecture.
HF: deepseek-ai/DeepSeek-OCR-2
Requires: torch==2.6.0, transformers==4.46.3, einops, addict, easydict, flash-attn==2.7.3

Two inference modes:
  - "document": <image>\n<|grounding|>Convert the document to markdown.
  - "free":     <image>\nFree OCR.
"""

import logging
import time
from typing import Any

from ..core.backend_manager import OCRBackend
from ..core.config import OCRConfig

logger = logging.getLogger(__name__)


class DeepSeekOCR2Backend(OCRBackend):
    """DeepSeek-OCR-2 backend — January 2026, Visual Causal Flow architecture."""

    def __init__(self, config: OCRConfig):
        super().__init__("deepseek-ocr2", config)
        self._model = None
        self._tokenizer = None
        self.model_name = "deepseek-ai/DeepSeek-OCR-2"
        self.cache_dir = config.model_dir / "deepseek_ocr2"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._device = None

        import importlib.util

        self._torch_ok = importlib.util.find_spec("torch") is not None
        self._transformers_ok = importlib.util.find_spec("transformers") is not None
        self._einops_ok = importlib.util.find_spec("einops") is not None

        if self._torch_ok and self._transformers_ok:
            self._available = True
            if not self._einops_ok:
                logger.warning(
                    "DeepSeek-OCR-2: einops not installed, may fail at runtime. pip install einops addict easydict"
                )
        else:
            self._available = False
            logger.warning("DeepSeek-OCR-2: torch or transformers not available")

    def _load_model(self):
        if self._model is not None:
            return
        if not self.is_available():
            raise RuntimeError("DeepSeek-OCR-2 dependencies not available")

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.bfloat16 if self._device == "cuda" else torch.float32

            logger.info(f"Loading DeepSeek-OCR-2 on {self._device}...")
            t0 = time.time()

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                cache_dir=str(self.cache_dir),
            )

            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype=dtype,
                device_map="auto" if self._device == "cuda" else None,
                cache_dir=str(self.cache_dir),
            )
            if self._device == "cpu":
                self._model = self._model.to("cpu")

            self._model.eval()
            logger.info(f"DeepSeek-OCR-2 loaded in {time.time() - t0:.1f}s")

        except Exception as e:
            logger.error(f"Failed to load DeepSeek-OCR-2: {e}")
            raise RuntimeError(f"DeepSeek-OCR-2 load failed: {e}")

    async def process_image(
        self,
        image_path: str,
        mode: str = "text",
        output_format: str = "text",
        language: str | None = None,
        region: list[int] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Process image with DeepSeek-OCR-2."""
        if not self.is_available():
            return {"success": False, "error": "DeepSeek-OCR-2 not available"}

        try:
            import torch
            from PIL import Image

            self._load_model()
            t0 = time.time()

            img = Image.open(image_path).convert("RGB")
            if region and len(region) == 4:
                img = img.crop(tuple(region))

            # DeepSeek-OCR-2 prompt styles per model card
            if mode in ("format", "text"):
                # Structured markdown extraction
                prompt = "<image>\n<|grounding|>Convert the document to markdown."
            else:
                # Raw text extraction
                prompt = "<image>\nFree OCR."

            inputs = self._tokenizer(
                prompt,
                images=img,
                return_tensors="pt",
            )
            if self._device == "cuda":
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            with torch.inference_mode():
                output_ids = self._model.generate(
                    **inputs,
                    max_new_tokens=4096,
                    do_sample=False,
                    use_cache=True,
                )

            input_len = inputs["input_ids"].shape[1]
            text = self._tokenizer.decode(
                output_ids[0][input_len:],
                skip_special_tokens=True,
            ).strip()

            return {
                "success": True,
                "text": text,
                "backend": "deepseek-ocr2",
                "model": self.model_name,
                "mode": mode,
                "processing_time": time.time() - t0,
                "confidence": 0.93,
                "metadata": {"device": self._device},
            }

        except Exception as e:
            logger.error(f"DeepSeek-OCR-2 error: {e}")
            return {"success": False, "error": str(e), "backend": "deepseek-ocr2"}

    def get_capabilities(self) -> dict[str, Any]:
        caps = super().get_capabilities()
        caps.update(
            {
                "name": "DeepSeek-OCR-2",
                "description": "DeepSeek-OCR-2 — Jan 2026, Visual Causal Flow architecture",
                "modes": ["text", "format", "ocr"],
                "output_formats": ["text", "markdown"],
                "gpu_support": True,
                "model_size": "~6GB (3B params)",
                "strengths": [
                    "Visual Causal Flow for context-aware extraction",
                    "Strong on mixed text/layout documents",
                    "DeepSeek quality applied to OCR specialization",
                    "Markdown output with layout preservation",
                ],
                "install_note": "pip install einops addict easydict flash-attn==2.7.3 --no-build-isolation",
            }
        )
        return caps
