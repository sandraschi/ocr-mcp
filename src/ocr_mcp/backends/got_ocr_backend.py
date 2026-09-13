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

import asyncio
import contextlib
import json
import logging
import time
from pathlib import Path
from typing import Any

from ..core.backend_manager import OCRBackend
from ..core.config import OCRConfig

logger = logging.getLogger(__name__)

_LEGACY_VENV_DIR = Path(__file__).resolve().parents[3] / ".venv-legacy-vlm"


@contextlib.contextmanager
def _no_cuda_required():
    """Neutralize GOT-OCR's vendored ``model.chat()``, which hardcodes
    ``.cuda()``/``.half()`` on every tensor it builds (image + input_ids)
    with no CPU branch at all. Scoped to this call only, restored after.
    """
    import torch

    orig_cuda, orig_half = torch.Tensor.cuda, torch.Tensor.half
    torch.Tensor.cuda = lambda self, *a, **k: self
    torch.Tensor.half = lambda self, *a, **k: self
    try:
        yield
    finally:
        torch.Tensor.cuda = orig_cuda
        torch.Tensor.half = orig_half


class GOTOCRBackend(OCRBackend):
    """GOT-OCR2.0 backend implementation."""

    def __init__(self, config: OCRConfig):
        super().__init__("got-ocr", config)
        self._model = None
        self._tokenizer = None
        self.model_name = "stepfun-ai/GOT-OCR2_0"
        self.cache_dir = config.model_dir / "got_ocr"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Check if dependencies are available
        import importlib.util

        self.torch_available = importlib.util.find_spec("torch") is not None
        self.transformers_available = importlib.util.find_spec("transformers") is not None

        if self.torch_available and self.transformers_available:
            self._available = True
            logger.info("GOT-OCR2.0 dependencies available")
        else:
            self._available = False
            logger.warning("GOT-OCR2.0 dependencies not available")

    def _legacy_venv_python(self) -> Path | None:
        """Path to the isolated transformers==4.37.2 venv's interpreter, if set
        up via ``scripts/setup_legacy_vlm_venv.py``. GOT-OCR's vendored code
        (tokenizer + Cache.seen_tokens + cache_position handling in its own
        forward()) only works against the transformers version it shipped
        with -- see module docstring on ``_no_cuda_required`` and
        ``_got_ocr_legacy_runner.py`` for the chain of incompatibilities this
        sidesteps. Returns None if the sidecar venv hasn't been created.
        """
        candidate = _LEGACY_VENV_DIR / "Scripts" / "python.exe"
        return candidate if candidate.exists() else None

    async def _run_via_legacy_venv(self, python_exe: Path, image_path: str, ocr_type: str) -> str:
        """Run GOT-OCR2.0 inference in the isolated legacy-transformers venv."""
        runner = Path(__file__).resolve().with_name("_got_ocr_legacy_runner.py")
        proc = await asyncio.create_subprocess_exec(
            str(python_exe),
            str(runner),
            image_path,
            ocr_type,
            str(self.cache_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        last_line = stdout.decode("utf-8", errors="replace").strip().splitlines()
        if not last_line:
            raise RuntimeError(
                f"legacy-vlm subprocess produced no output (exit {proc.returncode}): "
                f"{stderr.decode('utf-8', errors='replace')[-2000:]}"
            )
        payload = json.loads(last_line[-1])
        if not payload.get("success"):
            raise RuntimeError(payload.get("error", "unknown legacy-vlm subprocess error"))
        return payload["text"]

    def _load_model(self):
        """Load model and tokenizer lazily.

        GOT-OCR2.0 (stepfun-ai/GOT-OCR2_0) ships a custom ``GOTConfig`` /
        ``modeling_GOT.py`` via ``trust_remote_code``. It must be loaded with
        ``AutoModel`` (generic auto-dispatch), NOT ``AutoModelForCausalLM``
        which fails with::

            Unrecognized configuration class ...GOTConfig... for this kind of
            AutoModel: AutoModelForCausalLM.

        Newer transformers (>=4.48) also ships a native ``GotOcr2Config`` /
        ``GotOcr2ForConditionalGeneration`` mapping, so we try generic
        ``AutoModel`` first and fall back to the native class.
        """
        if self._model is not None:
            return

        if not self.is_available():
            raise RuntimeError("GOT-OCR dependencies not available")

        try:
            from ..utils.startup_bootstrap import patch_transformers_compatibility

            patch_transformers_compatibility()

            import torch
            from transformers import AutoModel, AutoTokenizer

            logger.info(f"Loading GOT-OCR2.0 model from {self.model_name}...")
            start_time = time.time()

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, trust_remote_code=True, cache_dir=str(self.cache_dir)
            )
            # QWenTokenizer (vendored, targets transformers==4.37.2) never defines
            # cls/sep tokens -- it bakes BOS/EOS into the prompt text itself via
            # literal <|im_start|>/<|im_end|>. Modern transformers' default
            # build_inputs_with_special_tokens() unconditionally splices in
            # [cls_token_id] + ids + [sep_token_id], which are None here, so
            # tokenizer(prompt) -> pad() blows up with "type of None unknown".
            # Neutralize it to the no-op passthrough this tokenizer expects.
            self._tokenizer.build_inputs_with_special_tokens = lambda token_ids_0, token_ids_1=None: (
                token_ids_0 if token_ids_1 is None else token_ids_0 + token_ids_1
            )

            # Determine device and dtype
            device = self.config.device
            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"

            dtype = torch.bfloat16 if device == "cuda" else torch.float32

            # device_map="cuda"/"cpu" is invalid -- accelerate expects
            # "auto"/"cuda:0"/None. On CUDA use "auto" (shard + offload),
            # on CPU load plain then .to("cpu") to avoid accelerate quirks.
            load_kwargs: dict[str, Any] = {
                "trust_remote_code": True,
                "cache_dir": str(self.cache_dir),
            }
            try:
                import accelerate  # noqa: F401 -- just probing availability

                has_accelerate = True
            except Exception:
                has_accelerate = False

            if device == "cuda" and has_accelerate:
                load_kwargs.update(
                    {
                        "device_map": "auto",
                        "torch_dtype": dtype,
                        "low_cpu_mem_usage": True,
                        "use_safetensors": True,
                    }
                )
            else:
                load_kwargs.update({"torch_dtype": dtype, "low_cpu_mem_usage": True})
                # use_safetensors only when the checkpoint actually ships them;
                # let from_pretrained decide on CPU path (avoids hard failure).

            try:
                self._model = AutoModel.from_pretrained(self.model_name, **load_kwargs)
            except Exception as e:
                logger.warning(f"Generic AutoModel load failed ({e}), trying native GotOcr2 class...")
                native_cls = None
                try:
                    from transformers import GotOcr2ForConditionalGeneration

                    native_cls = GotOcr2ForConditionalGeneration
                except Exception:
                    try:
                        from transformers.models.got_ocr2.modeling_got_ocr2 import (
                            GotOcr2ForConditionalGeneration as _Native,
                        )

                        native_cls = _Native
                    except Exception:
                        native_cls = None
                if native_cls is not None:
                    # Native class uses the stock config (no remote code).
                    native_kwargs = dict(load_kwargs)
                    native_kwargs.pop("trust_remote_code", None)
                    self._model = native_cls.from_pretrained(self.model_name, **native_kwargs)
                else:
                    raise

            if device != "cuda" or not has_accelerate:
                try:
                    self._model = self._model.to(device)
                except Exception:
                    logger.debug("suppressed Exception in _load_model", exc_info=True)

            self._model.eval()
            logger.info(f"GOT-OCR2.0 model loaded in {time.time() - start_time:.2f}s on {device}")

        except Exception as e:
            msg = str(e)
            hint = ""
            if "Unrecognized configuration class" in msg or "GOTConfig" in msg:
                import transformers as _tf

                hint = (
                    f" (transformers={getattr(_tf, '__version__', '?')}; "
                    "GOT-OCR2_0 needs trust_remote_code + generic AutoModel. "
                    "Upgrade with: uv pip install -U transformers accelerate safetensors)"
                )
            logger.error(f"Failed to load GOT-OCR2.0 model: {e}{hint}")
            raise RuntimeError(f"Failed to load GOT-OCR2.0 model: {e}{hint}")

    async def process_image(
        self,
        image_path: str,
        mode: str = "text",
        output_format: str = "text",
        language: str | None = None,
        region: list[int] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Process image with GOT-OCR2.0.
        """
        if not self.is_available():
            return {"success": False, "error": "GOT-OCR2.0 backend not available"}

        try:
            start_time = time.time()

            # Map mode to ocr_type
            ocr_type = "ocr"
            if mode == "format":
                ocr_type = "format"

            # Add box info for fine-grained if region provided
            # GOT-OCR API typically handles box as specific argument or via ocr_type='ocr' + box
            # For simplicity in this v1, we focus on full image 'ocr' and 'format'
            # If region is provided, we might interpret it handling logic (crop or prompt)

            legacy_python = self._legacy_venv_python()
            if legacy_python is not None:
                # Preferred path: GOT-OCR's vendored code needs transformers==4.37.2,
                # see _legacy_venv_python's docstring. Isolated venv, no in-process load.
                res = await self._run_via_legacy_venv(legacy_python, image_path, ocr_type)
                device_str = "cpu (legacy-vlm venv)"
            else:
                logger.warning(
                    "GOT-OCR2.0: .venv-legacy-vlm not found, falling back to in-process "
                    "load under the main venv's transformers -- this is known to fail "
                    "(cache_position mismatch inside GOT-OCR's vendored forward()). "
                    "Run scripts/setup_legacy_vlm_venv.py to fix."
                )
                self._load_model()
                # model.chat(tokenizer, image_file, ocr_type='ocr', ocr_box=None, ocr_color=None)
                device = str(getattr(self._model, "device", "cpu"))
                if device.startswith("cuda"):
                    res = self._model.chat(self._tokenizer, image_path, ocr_type=ocr_type)
                else:
                    with _no_cuda_required():
                        res = self._model.chat(self._tokenizer, image_path, ocr_type=ocr_type)
                device_str = device

            processing_time = time.time() - start_time

            result = {
                "success": True,
                "text": res,
                "confidence": 1.0,  # GOT-OCR doesn't always return confidence in simple chat mode
                "backend": "got-ocr",
                "mode": mode,
                "format": output_format,
                "processing_time": processing_time,
                "metadata": {
                    "model": self.model_name,
                    "model_size": self.config.got_ocr_model_size,
                    "device": device_str,
                },
            }

            # Add HTML formatting if requested
            if output_format == "html":
                # If mode is format, result is likely markdown/latex, wrap it
                result["html"] = self._generate_html(res)

            return result

        except Exception as e:
            logger.error(f"GOT-OCR2.0 processing error: {e}")
            return {
                "success": False,
                "error": f"GOT-OCR2.0 processing failed: {e!s}",
                "backend": "got-ocr",
            }

    def _generate_html(self, text: str) -> str:
        """Generate HTML representation of OCR results."""
        # Simple wrapper for now, assuming text might contain markdown
        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>GOT-OCR2.0 Result</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                .content {{ background: #f9f9f9; padding: 20px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="content">
                {text.replace(chr(10), "<br>")}
            </div>
        </body>
        </html>
        """
        return html_template

    def get_capabilities(self) -> dict[str, Any]:
        """Get GOT-OCR2.0 capabilities."""
        base_capabilities = super().get_capabilities()
        base_capabilities.update(
            {
                "modes": ["text", "format"],
                "output_formats": ["text", "html"],
                "gpu_support": True,
                "model_size": self.config.got_ocr_model_size,
                "languages": ["auto"],
                "features": ["formatted_text_preservation", "layout_analysis", "markdown_output"],
            }
        )
        return base_capabilities
