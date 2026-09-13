"""
Unlimited-OCR Backend - July 2026, Baidu Inc.

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

import asyncio
import json
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
_LEGACY_VENV_DIR = Path(__file__).resolve().parents[3] / ".venv-legacy-vlm-deepseek"


class UnlimitedOCRBackend(OCRBackend):
    """Unlimited-OCR backend - July 2026, Baidu one-shot long-horizon parsing."""

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
        self._addict_ok = _iu.find_spec("addict") is not None
        self._easydict_ok = _iu.find_spec("easydict") is not None
        self._matplotlib_ok = _iu.find_spec("matplotlib") is not None

        if self._torch_ok and self._transformers_ok and self._pil_ok and self._addict_ok and self._matplotlib_ok:
            self._available = True
            if not self._einops_ok:
                logger.warning(
                    "Unlimited-OCR: einops not installed, may fail at runtime. pip install einops addict easydict matplotlib"
                )
        else:
            self._available = False
            missing = [
                p
                for p, ok in [
                    ("torch", self._torch_ok),
                    ("transformers", self._transformers_ok),
                    ("PIL", self._pil_ok),
                    ("addict", self._addict_ok),
                    ("easydict", self._easydict_ok),
                    ("matplotlib", self._matplotlib_ok),
                ]
                if not ok
            ]
            logger.warning(f"Unlimited-OCR missing deps: {missing}")

    def _legacy_venv_python(self) -> Path | None:
        """Path to the isolated transformers==4.46.3 venv, shared with
        DeepSeek-OCR and DeepSeek-OCR-2 (Unlimited-OCR is "Built on
        DeepSeek-OCR lineage" per its own model card, and vendors the
        identical infer() signature and hardcoded .cuda()/.to(bfloat16)
        pattern throughout generate() -- confirmed by grepping
        modeling_unlimitedocr.py: 14 hardcoded .cuda() calls). The README's
        stated transformers==4.57.1 doesn't change this -- the vendored
        forward()/generate() calls are what matter, not the config metadata.
        """
        candidate = _LEGACY_VENV_DIR / "Scripts" / "python.exe"
        return candidate if candidate.exists() else None

    async def _run_via_legacy_venv(self, python_exe: Path, image_path: str, prompt: str) -> str:
        """Run Unlimited-OCR inference in the isolated legacy-transformers venv."""
        runner = Path(__file__).resolve().with_name("_deepseek_ocr_legacy_runner.py")
        proc = await asyncio.create_subprocess_exec(
            str(python_exe),
            str(runner),
            self.model_name,
            image_path,
            prompt,
            str(self.cache_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        lines = stdout.decode("utf-8", errors="replace").strip().splitlines()
        if not lines:
            raise RuntimeError(
                f"legacy-vlm subprocess produced no output (exit {proc.returncode}): "
                f"{stderr.decode('utf-8', errors='replace')[-2000:]}"
            )
        payload = json.loads(lines[-1])
        if not payload.get("success"):
            raise RuntimeError(payload.get("error", "unknown legacy-vlm subprocess error"))
        return payload["text"]

    def _load_model(self):
        if self._model is not None:
            return
        if not self.is_available():
            raise RuntimeError("Unlimited-OCR dependencies not available")
        if self._legacy_venv_python() is not None:
            # Real loading happens per-call in the isolated subprocess.
            self._model = True
            self._tokenizer = True
            return

        try:
            from ..utils.startup_bootstrap import patch_transformers_compatibility

            patch_transformers_compatibility()

            import torch
            from transformers import AutoModel, AutoTokenizer

            self._device = "cuda" if torch.cuda.is_available() else "cpu"

            logger.warning(
                "Unlimited-OCR: .venv-legacy-vlm-deepseek not found, falling back to "
                "in-process load under the main venv's transformers -- likely to fail "
                "the same way GOT-OCR did before isolation. Run "
                "scripts/setup_legacy_vlm_deepseek_venv.py to fix."
            )
            t0 = time.time()

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                cache_dir=str(self.cache_dir),
            )

            self._model = AutoModel.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype=torch.bfloat16,  # infer() hardcodes image tensors to bfloat16
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

            input_path = image_path
            if region and len(region) == 4:
                img = Image.open(image_path).convert("RGB").crop(tuple(region))
                temp_cropped = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                img.save(temp_cropped, format="PNG")
                temp_cropped.close()
                input_path = temp_cropped.name

            prompt_text = "<image>document parsing."
            if mode in ("raw", "ocr"):
                prompt_text = "<image>Free OCR."

            try:
                legacy_python = self._legacy_venv_python()
                if legacy_python is None:
                    raise RuntimeError(
                        "Unlimited-OCR needs the isolated .venv-legacy-vlm-deepseek venv "
                        "(transformers==4.46.3). Run scripts/setup_legacy_vlm_deepseek_venv.py."
                    )
                text = await self._run_via_legacy_venv(legacy_python, input_path, prompt_text)
            finally:
                if region and len(region) == 4:
                    try:
                        os.unlink(input_path)
                    except OSError:
                        pass

            return {
                "success": True,
                "text": text.strip(),
                "backend": "unlimited-ocr",
                "model": self.model_name,
                "mode": mode,
                "processing_time": time.time() - t0,
                "confidence": 0.85,
                "metadata": {"device": "cpu (legacy-vlm venv)", "inference_mode": "gundam"},
            }

        except Exception as e:
            logger.error(f"Unlimited-OCR error: {e}")
            return {"success": False, "error": str(e), "backend": "unlimited-ocr"}

    def get_capabilities(self) -> dict[str, Any]:
        caps = super().get_capabilities()
        caps.update(
            {
                "name": "Unlimited-OCR",
                "description": "Baidu Unlimited-OCR - Jul 2026, one-shot long-horizon document parsing",
                "modes": ["text", "format", "ocr"],
                "output_formats": ["text", "markdown"],
                "gpu_support": True,
                "model_size": "~6GB (3B params)",
                "strengths": [
                    "Unbounded-length document parsing without image resolution limits",
                    "Two inference modes: gundam (cropped, 640px) and base (full, 1024px)",
                    "ParseBench 46.17 mean / 86.81 text content score",
                    "MIT license - fully open source",
                    "Built on DeepSeek-OCR lineage with Baidu's long-horizon improvements",
                    "Multi-page and PDF support via infer_multi",
                ],
                "install_note": "pip install einops addict easydict",
            }
        )
        return caps
