import logging
import time
from typing import Any

from ..core.backend_manager import OCRBackend
from ..core.config import OCRConfig

logger = logging.getLogger(__name__)


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

    def _load_model(self):
        """Load model and tokenizer lazily."""
        if self._model is not None:
            return

        if not self.is_available():
            raise RuntimeError("GOT-OCR dependencies not available")

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            logger.info(f"Loading GOT-OCR2.0 model from {self.model_name}...")
            start_time = time.time()

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, trust_remote_code=True, cache_dir=str(self.cache_dir)
            )

            # Determine device and dtype
            device = self.config.device
            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"

            dtype = torch.bfloat16 if device == "cuda" else torch.float32

            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                device_map=device,
                use_safetensors=True,
                torch_dtype=dtype,
                cache_dir=str(self.cache_dir),
            )

            self._model.eval()
            logger.info(f"GOT-OCR2.0 model loaded in {time.time() - start_time:.2f}s on {device}")

        except Exception as e:
            logger.error(f"Failed to load GOT-OCR2.0 model: {e}")
            raise RuntimeError(f"Failed to load GOT-OCR2.0 model: {e}")

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
            self._load_model()

            start_time = time.time()

            # Map mode to ocr_type
            ocr_type = "ocr"
            if mode == "format":
                ocr_type = "format"

            # Add box info for fine-grained if region provided
            # GOT-OCR API typically handles box as specific argument or via ocr_type='ocr' + box
            # For simplicity in this v1, we focus on full image 'ocr' and 'format'
            # If region is provided, we might interpret it handling logic (crop or prompt)

            # Run inference
            # model.chat(tokenizer, image_file, ocr_type='ocr', ocr_box=None, ocr_color=None)
            res = self._model.chat(self._tokenizer, image_path, ocr_type=ocr_type)

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
                    "device": str(self._model.device if self._model else "unknown"),
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
                "error": f"GOT-OCR2.0 processing failed: {str(e)}",
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
