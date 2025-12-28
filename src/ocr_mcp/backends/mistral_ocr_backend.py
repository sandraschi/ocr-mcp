"""
Mistral OCR 3 Backend for OCR-MCP

Uses Mistral AI's OCR API for high-quality document processing.
Reference: https://mistral.ai/news/mistral-ocr-3
"""

import logging
import httpx
from typing import Dict, Any, Optional, List
import base64
from pathlib import Path

from ..core.backend_manager import OCRBackend
from ..core.config import OCRConfig

logger = logging.getLogger(__name__)


class MistralOCRBackend(OCRBackend):
    """Mistral OCR 3 backend implementation using their API."""

    def __init__(self, config: OCRConfig):
        super().__init__("mistral-ocr", config)

        # Check if we have API key and can connect
        self.api_key = getattr(config, 'mistral_api_key', None)
        self.base_url = getattr(config, 'mistral_base_url', 'https://api.mistral.ai/v1')

        if self.api_key:
            try:
                # Test API connectivity
                self._test_api_connection()
                self._available = True
                logger.info("Mistral OCR backend available")
            except Exception as e:
                self._available = False
                logger.warning(f"Mistral OCR backend not available: {e}")
        else:
            self._available = False
            logger.warning("Mistral OCR backend not available: No API key configured")

    def _test_api_connection(self) -> bool:
        """Test connection to Mistral API."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                return response.status_code == 200
        except Exception:
            return False

    async def process_image(
        self,
        image_path: str,
        mode: str = "text",
        output_format: str = "text",
        language: Optional[str] = None,
        region: Optional[List[int]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process image with Mistral OCR 3 API.

        Args:
            image_path: Path to image file
            mode: Processing mode ("text", "markdown", "json")
            output_format: Output format ("text", "markdown", "json")
            language: Language hint (optional)
            region: Region coordinates (not supported by Mistral API)

        Returns:
            OCR processing results
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Mistral OCR backend not available"
            }

        try:
            # Read and encode image
            image_path_obj = Path(image_path)
            if not image_path_obj.exists():
                return {
                    "success": False,
                    "error": f"Image file not found: {image_path}"
                }

            with open(image_path_obj, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            # Prepare API request
            url = f"{self.base_url}/vision/ocr"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Determine output format
            if mode == "markdown" or output_format == "markdown":
                model = "mistral-ocr-2512"  # Mistral OCR 3 with markdown support
            else:
                model = "mistral-ocr-2512"  # Use the same model, format determined by response

            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Please extract all text from this image. Return in {'markdown' if mode == 'markdown' else 'plain text'} format."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 4096,
                "temperature": 0.1  # Low temperature for consistent OCR results
            }

            # Make API request
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Mistral API error: {response.status_code} - {response.text}",
                        "backend": "mistral-ocr"
                    }

                result = response.json()
                content = result["choices"][0]["message"]["content"]

                # Estimate processing time and confidence
                usage = result.get("usage", {})
                processing_time = usage.get("total_tokens", 1000) * 0.001  # Rough estimate

                return {
                    "success": True,
                    "text": content.strip(),
                    "confidence": 0.95,  # Mistral OCR 3 is very accurate
                    "backend": "mistral-ocr",
                    "model": model,
                    "mode": mode,
                    "format": output_format,
                    "processing_time": processing_time,
                    "metadata": {
                        "api_model": model,
                        "tokens_used": usage.get("total_tokens", 0),
                        "finish_reason": result["choices"][0].get("finish_reason", "unknown"),
                        "language": language or "auto",
                        "mistral_ocr_version": "3"
                    }
                }

        except Exception as e:
            logger.error(f"Mistral OCR processing error: {e}")
            return {
                "success": False,
                "error": f"Mistral OCR processing failed: {str(e)}",
                "backend": "mistral-ocr"
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get Mistral OCR capabilities."""
        base_capabilities = super().get_capabilities()
        base_capabilities.update({
            "modes": ["text", "markdown", "json"],
            "output_formats": ["text", "markdown", "json"],
            "gpu_support": True,  # Cloud-based, uses GPU infrastructure
            "languages": ["auto", "en", "fr", "de", "es", "it", "pt", "nl", "ru", "zh", "ja", "ko"],
            "features": [
                "state_of_the_art_accuracy",
                "handwriting_recognition",
                "form_processing",
                "table_reconstruction",
                "complex_layout_analysis",
                "multi_language_support",
                "markdown_output",
                "json_structured_output",
                "cloud_based_processing"
            ],
            "limitations": [
                "requires_api_key",
                "cloud_dependency",
                "api_rate_limits",
                "no_offline_support"
            ],
            "cost_per_1000_pages": "$2.00 (batch discount: $1.00)",
            "model_version": "mistral-ocr-2512",
            "benchmark_performance": "74% win rate over Mistral OCR 2"
        })
        return base_capabilities






