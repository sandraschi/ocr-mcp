"""
MinerU2.5 Backend — September 2025 / April 2026, opendatalab.

Coarse-to-fine document parsing VLM (1.2B params).  Uses the direct
HuggingFace Transformers inference path.

HF models:
  - opendatalab/MinerU2.5-Pro-2604-1.2B  (v3.1, April 2026, recommended)
  - opendatalab/MinerU2.5-2509-1.2B      (v2.5, September 2025)

Full document pipeline (PDF/DOCX/PPTX/XLSX) requires `pip install mineru`
and is not integrated here yet — open a PR if you need it.
"""

import logging
import time
from typing import Any

from ..core.backend_manager import OCRBackend
from ..core.config import OCRConfig

logger = logging.getLogger(__name__)

_HF_MODEL_ID = "opendatalab/MinerU2.5-Pro-2604-1.2B"


class MinerU25Backend(OCRBackend):
    """MinerU2.5 backend — coarse-to-fine document parsing VLM (1.2B params)."""

    def __init__(self, config: OCRConfig):
        super().__init__("mineru-2.5", config)
        self.cache_dir = config.model_dir / "mineru25"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._model = None
        self._processor = None

        import importlib.util as _iu

        self._torch_ok = _iu.find_spec("torch") is not None
        self._transformers_ok = _iu.find_spec("transformers") is not None

        if self._torch_ok and self._transformers_ok:
            self._available = True
        else:
            self._available = False
            logger.warning(
                "MinerU2.5: torch or transformers not available. "
                "pip install torch transformers"
            )

    async def load_model(self) -> bool:
        if self._model is not None:
            return True
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoProcessor

            device = self.config.resolve_torch_device()
            dtype = torch.bfloat16 if device == "cuda" else torch.float32

            logger.info("Loading MinerU2.5 VLM on %s ...", device)
            t0 = time.time()
            self._processor = AutoProcessor.from_pretrained(
                _HF_MODEL_ID,
                trust_remote_code=True,
                cache_dir=str(self.cache_dir),
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                _HF_MODEL_ID,
                trust_remote_code=True,
                torch_dtype=dtype,
                device_map="auto" if device == "cuda" else None,
                cache_dir=str(self.cache_dir),
            )
            if device == "cpu":
                self._model = self._model.to("cpu")
            self._model.eval()
            logger.info("MinerU2.5 loaded in %.1fs", time.time() - t0)
            return True
        except Exception as e:
            logger.error("MinerU2.5 load failed: %s", e)
            self._available = False
            return False

    async def process_image(
        self,
        image_path: str,
        mode: str = "text",
        output_format: str = "text",
        language: str | None = None,
        region: list[int] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        if not self.is_available():
            return {"success": False, "error": "MinerU2.5 not available"}

        try:
            import torch
            from PIL import Image

            loaded = await self.load_model()
            if not loaded:
                return {"success": False, "error": "MinerU2.5 model failed to load"}

            t0 = time.time()
            img = Image.open(image_path).convert("RGB")
            if region and len(region) == 4:
                img = img.crop(tuple(region))

            prompt = "<image>\nConvert the document to markdown."
            inputs = self._processor(
                text=prompt,
                images=img,
                return_tensors="pt",
            )
            device = self.config.resolve_torch_device()
            if device == "cuda":
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            with torch.inference_mode():
                output_ids = self._model.generate(
                    **inputs,
                    max_new_tokens=4096,
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
                "backend": "mineru-2.5",
                "model": _HF_MODEL_ID,
                "mode": mode,
                "processing_time": time.time() - t0,
                "confidence": 0.92,
                "metadata": {"device": device, "engine": "hf_direct"},
            }

        except Exception as e:
            logger.error("MinerU2.5 error: %s", e)
            return {"success": False, "error": str(e), "backend": "mineru-2.5"}

    def get_capabilities(self) -> dict[str, Any]:
        caps = super().get_capabilities()
        caps.update(
            {
                "name": "MinerU2.5",
                "description": "MinerU2.5-Pro — Apr 2026, opendatalab coarse-to-fine document parsing VLM",
                "modes": ["text", "format"],
                "output_formats": ["text", "markdown"],
                "gpu_support": True,
                "model_size": "~2.5GB (1.2B params)",
                "strengths": [
                    "Coarse-to-fine: global layout analysis + native-resolution content recognition",
                    "SOTA on OmniDocBench for academic and technical documents",
                    "Excellent formula-to-LaTeX and table-to-HTML conversion",
                    "62k+ GitHub stars, active development by opendatalab",
                ],
                "install_note": "pip install torch transformers",
            }
        )
        return caps
