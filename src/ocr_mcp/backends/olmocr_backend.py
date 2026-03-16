"""
olmOCR-2 Backend (Allen Institute for AI, October 2025)
Built on Qwen2.5-VL-7B-Instruct. 82.4 on olmOCR-Bench.
Best for academic/scientific PDFs: arXiv papers, math equations, multi-column layouts.
HF: allenai/olmOCR-2-7B-1025

Works with the standard olmOCR toolkit for batch/vLLM processing,
or directly via transformers (used here for integration simplicity).
"""

import logging
import time
from typing import Any

from ..core.backend_manager import OCRBackend
from ..core.config import OCRConfig

logger = logging.getLogger(__name__)

# Default system prompt from olmOCR-2 model card
_OLMOCR_SYSTEM = (
    "Below is an image of a document page. "
    "Please extract all the text from this image. "
    "Output the text in reading order, preserving the layout as much as possible. "
    "For tables, use markdown table format. "
    "For equations and formulas, use LaTeX notation. "
    "Do not include any commentary, just the extracted text."
)


class OlmOCR2Backend(OCRBackend):
    """olmOCR-2 backend — October 2025, best for academic/scientific documents."""

    def __init__(self, config: OCRConfig):
        super().__init__("olmocr-2", config)
        self._model = None
        self._processor = None
        self.model_name = "allenai/olmOCR-2-7B-1025"
        self.cache_dir = config.model_dir / "olmocr2"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._device = None

        import importlib.util
        self._torch_ok = importlib.util.find_spec("torch") is not None
        self._transformers_ok = importlib.util.find_spec("transformers") is not None

        if self._torch_ok and self._transformers_ok:
            self._available = True
            logger.info("olmOCR-2 dependencies available")
        else:
            self._available = False
            logger.warning("olmOCR-2: torch or transformers not available")

    def _load_model(self):
        if self._model is not None:
            return
        if not self.is_available():
            raise RuntimeError("olmOCR-2 dependencies not available")

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoProcessor

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.bfloat16 if self._device == "cuda" else torch.float32

            logger.info(f"Loading olmOCR-2 (7B) on {self._device}...")
            t0 = time.time()

            self._processor = AutoProcessor.from_pretrained(
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
            logger.info(f"olmOCR-2 loaded in {time.time() - t0:.1f}s")

        except Exception as e:
            logger.error(f"Failed to load olmOCR-2: {e}")
            raise RuntimeError(f"olmOCR-2 load failed: {e}")

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
        """Process image with olmOCR-2."""
        if not self.is_available():
            return {"success": False, "error": "olmOCR-2 not available"}

        try:
            import torch
            from PIL import Image

            self._load_model()
            t0 = time.time()

            img = Image.open(image_path).convert("RGB")
            if region and len(region) == 4:
                img = img.crop(tuple(region))

            system_prompt = custom_prompt or _OLMOCR_SYSTEM

            # olmOCR-2 uses Qwen2.5-VL chat format
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": img},
                        {"type": "text", "text": system_prompt},
                    ],
                }
            ]

            text_input = self._processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

            inputs = self._processor(
                text=[text_input],
                images=[img],
                return_tensors="pt",
                padding=True,
            )
            if self._device == "cuda":
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            with torch.inference_mode():
                output_ids = self._model.generate(
                    **inputs,
                    max_new_tokens=8192,
                    do_sample=False,
                    use_cache=True,
                )

            input_len = inputs["input_ids"].shape[1]
            text = self._processor.decode(
                output_ids[0][input_len:],
                skip_special_tokens=True,
            ).strip()

            return {
                "success": True,
                "text": text,
                "backend": "olmocr-2",
                "model": self.model_name,
                "mode": mode,
                "processing_time": time.time() - t0,
                "confidence": 0.90,  # 82.4 on olmOCR-Bench
                "metadata": {"device": self._device, "params": "7B"},
            }

        except Exception as e:
            logger.error(f"olmOCR-2 error: {e}")
            return {"success": False, "error": str(e), "backend": "olmocr-2"}

    def get_capabilities(self) -> dict[str, Any]:
        caps = super().get_capabilities()
        caps.update({
            "name": "olmOCR-2",
            "description": "Allen AI olmOCR-2 (Oct 2025) — best for academic PDFs, math, multi-column",
            "modes": ["text", "format"],
            "output_formats": ["text", "markdown", "latex"],
            "gpu_support": True,
            "model_size": "~14GB (7B params, bfloat16)",
            "strengths": [
                "82.4 on olmOCR-Bench",
                "arXiv/scientific papers with math equations",
                "Multi-column academic layouts",
                "Complex tables in research documents",
                "GRPO RL training for equation accuracy",
            ],
            "ideal_for": "Scientific papers, academic PDFs, documents with math",
        })
        return caps
