"""
PaddleOCR-VL-1.5 Backend
January 2026 SOTA: 94.5% accuracy on OmniDocBench v1.5.
0.9B params (NaViT encoder + ERNIE-4.5-0.3B LM). Runs fine on RTX 4090.
CRITICAL: requires flash-attn for reasonable VRAM usage (~3.3GB vs 40GB+).

HF model: PaddlePaddle/PaddleOCR-VL-1.5
Supports: text, tables, formulas, charts, seals, 109 languages.
First model with irregular box localization (tilted/folded docs).
"""

import logging
import time
from typing import Any

from ..core.backend_manager import OCRBackend
from ..core.config import OCRConfig

logger = logging.getLogger(__name__)


class PaddleOCRVLBackend(OCRBackend):
    """PaddleOCR-VL-1.5 backend — January 2026 SOTA for document parsing."""

    def __init__(self, config: OCRConfig):
        super().__init__("paddleocr-vl", config)
        self._model = None
        self._processor = None
        self.model_name = "PaddlePaddle/PaddleOCR-VL-1.5"
        self.cache_dir = config.model_dir / "paddleocr_vl"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._device = None

        import importlib.util
        self._torch_ok = importlib.util.find_spec("torch") is not None
        self._transformers_ok = importlib.util.find_spec("transformers") is not None
        self._pil_ok = importlib.util.find_spec("PIL") is not None

        if self._torch_ok and self._transformers_ok and self._pil_ok:
            self._available = True
            logger.info("PaddleOCR-VL-1.5 dependencies available")
        else:
            self._available = False
            missing = [
                p for p, ok in [
                    ("torch", self._torch_ok),
                    ("transformers", self._transformers_ok),
                    ("PIL", self._pil_ok),
                ] if not ok
            ]
            logger.warning(f"PaddleOCR-VL-1.5 missing: {missing}")

    def _check_flash_attn(self) -> bool:
        import importlib.util
        return importlib.util.find_spec("flash_attn") is not None

    def _load_model(self):
        if self._model is not None:
            return
        if not self.is_available():
            raise RuntimeError("PaddleOCR-VL-1.5 dependencies not available")

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoProcessor

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            has_flash = self._check_flash_attn()
            if not has_flash and self._device == "cuda":
                logger.warning(
                    "flash-attn not installed — PaddleOCR-VL-1.5 will use ~40GB VRAM. "
                    "Install: pip install flash-attn --no-build-isolation"
                )

            logger.info(f"Loading PaddleOCR-VL-1.5 on {self._device} (flash-attn={has_flash})...")
            t0 = time.time()

            self._processor = AutoProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                cache_dir=str(self.cache_dir),
            )

            attn_impl = "flash_attention_2" if has_flash and self._device == "cuda" else "eager"
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype=torch.bfloat16 if self._device == "cuda" else torch.float32,
                device_map="auto" if self._device == "cuda" else None,
                attn_implementation=attn_impl,
                cache_dir=str(self.cache_dir),
            )
            if self._device == "cpu":
                self._model = self._model.to("cpu")

            self._model.eval()
            logger.info(f"PaddleOCR-VL-1.5 ready in {time.time() - t0:.1f}s (attn={attn_impl})")

        except Exception as e:
            logger.error(f"Failed to load PaddleOCR-VL-1.5: {e}")
            raise RuntimeError(f"PaddleOCR-VL-1.5 load failed: {e}")

    _TASK_PROMPTS = {
        "text":    "Convert the document to markdown.",
        "table":   "Recognize the table and convert to markdown.",
        "formula": "Recognize the formula and convert to LaTeX.",
        "chart":   "Describe the chart.",
        "ocr":     "Free OCR.",
    }

    async def process_image(
        self,
        image_path: str,
        mode: str = "text",
        output_format: str = "text",
        language: str | None = None,
        region: list[int] | None = None,
        task: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Process image with PaddleOCR-VL-1.5."""
        if not self.is_available():
            return {"success": False, "error": "PaddleOCR-VL-1.5 not available"}

        try:
            import torch
            from PIL import Image

            self._load_model()
            t0 = time.time()

            img = Image.open(image_path).convert("RGB")
            if region and len(region) == 4:
                img = img.crop(tuple(region))

            prompt_key = task or mode
            prompt = self._TASK_PROMPTS.get(prompt_key, self._TASK_PROMPTS["text"])
            full_prompt = f"<image>\n{prompt}"

            inputs = self._processor(
                text=full_prompt,
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
            generated = output_ids[0][input_len:]
            text = self._processor.decode(generated, skip_special_tokens=True).strip()

            return {
                "success": True,
                "text": text,
                "backend": "paddleocr-vl",
                "model": self.model_name,
                "mode": mode,
                "task": prompt_key,
                "processing_time": time.time() - t0,
                "confidence": 0.945,
                "metadata": {
                    "device": self._device,
                    "flash_attn": self._check_flash_attn(),
                    "params": "0.9B",
                },
            }

        except Exception as e:
            logger.error(f"PaddleOCR-VL-1.5 error: {e}")
            return {"success": False, "error": str(e), "backend": "paddleocr-vl"}

    def get_capabilities(self) -> dict[str, Any]:
        caps = super().get_capabilities()
        caps.update({
            "name": "PaddleOCR-VL-1.5",
            "description": "Baidu PaddleOCR-VL-1.5 — Jan 2026 SOTA, 94.5% OmniDocBench",
            "modes": ["text", "table", "formula", "chart", "ocr"],
            "output_formats": ["text", "markdown", "latex"],
            "language_count": 109,
            "gpu_support": True,
            "model_size": "~1.8GB (0.9B params)",
            "strengths": [
                "SOTA 94.5% on OmniDocBench v1.5",
                "Irregular box localization (tilted/folded/scanned docs)",
                "Tables, formulas, charts, seals, ancient books",
                "109 languages incl. CJK, Arabic, Devanagari, Tibetan, Bengali",
                "~3.3GB VRAM with flash-attn on 4090",
            ],
        })
        return caps
