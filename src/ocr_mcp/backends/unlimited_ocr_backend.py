"""
Unlimited-OCR Backend — July 2026, Baidu Inc.

Extends DeepSeek-OCR's one-shot long-horizon parsing to handle
unbounded-length documents without image resolution limits.

HF model: baidu/Unlimited-OCR
arXiv: 2606.23050
License: MIT

Two inference modes:
  - "gundam": base_size=1024, image_size=640, crop_mode=True (single images)
  - "base":   base_size=1024, image_size=1024, crop_mode=False (multi-page/PDF)

Dependencies: torch>=2.10.0, transformers>=4.57.1, einops, addict, easydict
"""

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from ..core.backend_manager import OCRBackend
from ..core.config import OCRConfig

logger = logging.getLogger(__name__)

_HF_MODEL_ID = "baidu/Unlimited-OCR"


class UnlimitedOCRBackend(OCRBackend):
    """Unlimited-OCR backend — July 2026, Baidu one-shot long-horizon parsing."""

    def __init__(self, config: OCRConfig):
        super().__init__("unlimited-ocr", config)
        self._model = None
        self._tokenizer = None
        self.model_name = _HF_MODEL_ID
        self.cache_dir = config.model_dir / "unlimited_ocr"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._device = None

        import importlib.util as _iu

        self._torch_ok = _iu.find_spec("torch") is not None
        self._transformers_ok = _iu.find_spec("transformers") is not None
        self._einops_ok = _iu.find_spec("einops") is not None
        self._pil_ok = _iu.find_spec("PIL") is not None

        if self._torch_ok and self._transformers_ok and self._pil_ok:
            self._available = True
            if not self._einops_ok:
                logger.warning(
                    "Unlimited-OCR: einops not installed, may fail at runtime. pip install einops addict easydict"
                )
        else:
            self._available = False
            missing = [
                p
                for p, ok in [
                    ("torch", self._torch_ok),
                    ("transformers", self._transformers_ok),
                    ("PIL", self._pil_ok),
                ]
                if not ok
            ]
            logger.warning(f"Unlimited-OCR missing deps: {missing}")

    def _load_model(self):
        if self._model is not None:
            return
        if not self.is_available():
            raise RuntimeError("Unlimited-OCR dependencies not available")

        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.bfloat16 if self._device == "cuda" else torch.float32

            logger.info(f"Loading Unlimited-OCR on {self._device}...")
            t0 = time.time()

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                cache_dir=str(self.cache_dir),
            )

            self._model = AutoModel.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype=dtype,
                device_map="auto" if self._device == "cuda" else None,
                cache_dir=str(self.cache_dir),
            )
            if self._device == "cpu":
                self._model = self._model.to("cpu")

            self._model.eval()
            logger.info(f"Unlimited-OCR loaded in {time.time() - t0:.1f}s")

        except Exception as e:
            logger.error(f"Failed to load Unlimited-OCR: {e}")
            raise RuntimeError(f"Unlimited-OCR load failed: {e}")

    async def process_image(
        self,
        image_path: str,
        mode: str = "text",
        output_format: str = "text",
        language: str | None = None,
        region: list[int] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Process image with Unlimited-OCR.

        Uses "gundam" config for single images (crop_mode=True, 640px).
        Supports two prompt modes: "document parsing." (default) or raw OCR.
        """
        if not self.is_available():
            return {"success": False, "error": "Unlimited-OCR not available"}

        try:
            from PIL import Image

            self._load_model()
            t0 = time.time()

            img = Image.open(image_path).convert("RGB")
            if region and len(region) == 4:
                img = img.crop(tuple(region))
                temp_cropped = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                img.save(temp_cropped, format="PNG")
                temp_cropped.close()
                input_path = temp_cropped.name
            else:
                input_path = image_path

            prompt_text = "<image>document parsing."
            if mode in ("raw", "ocr"):
                prompt_text = "<image>Free OCR."

            tmp_dir_obj = tempfile.TemporaryDirectory(prefix="unlimited_ocr_")
            tmp_dir = tmp_dir_obj.name

            try:
                result = self._model.infer(
                    self._tokenizer,
                    prompt=prompt_text,
                    image_file=input_path,
                    output_path=tmp_dir,
                    base_size=1024,
                    image_size=640,
                    crop_mode=True,
                    max_length=32768,
                    no_repeat_ngram_size=35,
                    ngram_window=128,
                    save_results=True,
                )
            finally:
                if region and len(region) == 4:
                    try:
                        os.unlink(input_path)
                    except OSError:
                        pass

            text = self._read_output(tmp_dir, result)
            try:
                tmp_dir_obj.cleanup()
            except OSError:
                pass

            return {
                "success": True,
                "text": text,
                "backend": "unlimited-ocr",
                "model": self.model_name,
                "mode": mode,
                "processing_time": time.time() - t0,
                "confidence": 0.85,
                "metadata": {"device": self._device, "inference_mode": "gundam"},
            }

        except Exception as e:
            logger.error(f"Unlimited-OCR error: {e}")
            return {"success": False, "error": str(e), "backend": "unlimited-ocr"}

    def _read_output(self, output_dir: str, result: Any) -> str:
        """Read OCR output from files in the output directory."""
        dir_path = Path(output_dir)
        if not dir_path.is_dir():
            if isinstance(result, str) and result.strip():
                return result.strip()
            if isinstance(result, dict):
                for key in ("text", "result", "output", "content"):
                    val = result.get(key)
                    if isinstance(val, str) and val.strip():
                        return val.strip()
            return str(result) if result else ""

        candidates = sorted(dir_path.iterdir())
        for p in candidates:
            if p.suffix.lower() in (".txt", ".md", ".json", ".html"):
                try:
                    content = p.read_text(encoding="utf-8").strip()
                    if content:
                        return content
                except Exception:
                    continue

        for p in candidates:
            if p.is_file():
                try:
                    content = p.read_text(encoding="utf-8").strip()
                    if content:
                        return content
                except Exception:
                    continue

        return ""

    def get_capabilities(self) -> dict[str, Any]:
        caps = super().get_capabilities()
        caps.update(
            {
                "name": "Unlimited-OCR",
                "description": "Baidu Unlimited-OCR — Jul 2026, one-shot long-horizon document parsing",
                "modes": ["text", "format", "ocr"],
                "output_formats": ["text", "markdown"],
                "gpu_support": True,
                "model_size": "~6GB (3B params)",
                "strengths": [
                    "Unbounded-length document parsing without image resolution limits",
                    "Two inference modes: gundam (cropped, 640px) and base (full, 1024px)",
                    "ParseBench 46.17 mean / 86.81 text content score",
                    "MIT license — fully open source",
                    "Built on DeepSeek-OCR lineage with Baidu's long-horizon improvements",
                    "Multi-page and PDF support via infer_multi",
                ],
                "install_note": "pip install einops addict easydict",
            }
        )
        return caps
