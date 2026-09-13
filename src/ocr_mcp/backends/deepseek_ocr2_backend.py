"""
DeepSeek-OCR-2 Backend
January 2026. "Visual Causal Flow" architecture.
HF: deepseek-ai/DeepSeek-OCR-2
Requires: torch==2.6.0, transformers==4.46.3, einops, addict, easydict, flash-attn==2.7.3

Two inference modes:
  - "document": <image>\n<|grounding|>Convert the document to markdown.
  - "free":     <image>\nFree OCR.
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from PIL import Image

from ..core.backend_manager import OCRBackend
from ..core.config import OCRConfig

logger = logging.getLogger(__name__)

_LEGACY_VENV_DIR = Path(__file__).resolve().parents[3] / ".venv-legacy-vlm-deepseek"


class DeepSeekOCR2Backend(OCRBackend):
    """DeepSeek-OCR-2 backend - January 2026, Visual Causal Flow architecture."""

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

    def _legacy_venv_python(self) -> Path | None:
        """Path to the isolated transformers==4.46.3 venv's interpreter, shared
        with DeepSeek-OCR and Unlimited-OCR (same deepseek-v2 encoder lineage,
        same infer() signature). See deepseek_backend.py's
        _legacy_venv_python docstring for why: vendored infer() hardcodes
        .cuda() throughout generate() and targets an older transformers than
        the main venv carries for paddleocr-vl/dots-ocr/etc.
        """
        candidate = _LEGACY_VENV_DIR / "Scripts" / "python.exe"
        return candidate if candidate.exists() else None

    async def _run_via_legacy_venv(self, python_exe: Path, image_path: str, prompt: str) -> str:
        """Run DeepSeek-OCR-2 inference in the isolated legacy-transformers venv."""
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
            raise RuntimeError("DeepSeek-OCR-2 dependencies not available")
        if self._legacy_venv_python() is not None:
            # Real loading happens per-call in the isolated subprocess.
            self._model = True
            self._tokenizer = True
            return

        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            self._device = "cuda" if torch.cuda.is_available() else "cpu"

            logger.warning(
                "DeepSeek-OCR-2: .venv-legacy-vlm-deepseek not found, falling back to "
                "in-process load under the main venv's transformers -- likely to fail "
                "the same way GOT-OCR did before isolation. Run "
                "scripts/setup_legacy_vlm_deepseek_venv.py to fix."
            )
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                cache_dir=str(self.cache_dir),
            )
            self._model = AutoModel.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                use_safetensors=True,
                torch_dtype=torch.bfloat16,
                cache_dir=str(self.cache_dir),
            )
            self._model = self._model.eval().to(self._device)

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
            self._load_model()
            t0 = time.time()

            # DeepSeek-OCR-2 prompt styles per model card
            if mode in ("format", "text"):
                prompt = "<image>\n<|grounding|>Convert the document to markdown."
            else:
                prompt = "<image>\nFree OCR."

            crop_path = None
            target_path = image_path
            if region and len(region) == 4:
                img = Image.open(image_path).convert("RGB").crop(tuple(region))
                fd, crop_path = tempfile.mkstemp(suffix=".png")
                os.close(fd)
                img.save(crop_path)
                target_path = crop_path

            legacy_python = self._legacy_venv_python()
            if legacy_python is None:
                raise RuntimeError(
                    "DeepSeek-OCR-2 needs the isolated .venv-legacy-vlm-deepseek venv "
                    "(transformers==4.46.3). Run scripts/setup_legacy_vlm_deepseek_venv.py."
                )
            text = await self._run_via_legacy_venv(legacy_python, target_path, prompt)

            if crop_path:
                Path(crop_path).unlink(missing_ok=True)

            return {
                "success": True,
                "text": text.strip(),
                "backend": "deepseek-ocr2",
                "model": self.model_name,
                "mode": mode,
                "processing_time": time.time() - t0,
                "confidence": 1.0,
                "metadata": {"device": "cpu (legacy-vlm venv)"},
            }

        except Exception as e:
            logger.error(f"DeepSeek-OCR-2 error: {e}")
            return {"success": False, "error": str(e), "backend": "deepseek-ocr2"}

    def get_capabilities(self) -> dict[str, Any]:
        caps = super().get_capabilities()
        caps.update(
            {
                "name": "DeepSeek-OCR-2",
                "description": "DeepSeek-OCR-2 - Jan 2026, Visual Causal Flow architecture",
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
