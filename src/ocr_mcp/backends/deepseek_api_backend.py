"""DeepSeek cloud OCR. Not the local DeepSeek-OCR-2 weights.

POST https://api.deepseek.com/v1/tools/ocr
multipart: purpose + file

The service returns page text and stops. It does not store the file and it
does not pass the file to a chat model. Word and PowerPoint files with no
pictures have their text extracted. Other files are recognized page by page.

Pricing (published): $0.225 per 1,000 pages. Limits: 100 MiB, 1,000 pages,
180 seconds from the start of the upload.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import httpx

from ..core.backend_manager import OCRBackend
from ..core.config import OCRConfig

logger = logging.getLogger(__name__)

OCR_URL = "https://api.deepseek.com/v1/tools/ocr"
MAX_BYTES = 100 * 1024 * 1024
PAGE_USD = 0.000225
PURPOSES = ("text_recognition", "rich_layout_recognition")


def parse_ocr_body(body: str) -> dict[str, Any]:
    """Parse an OCR response. Leading newlines are keepalive bytes, not JSON."""
    payload = json.loads(body.lstrip())
    if isinstance(payload, dict) and payload.get("error"):
        raise ValueError(str(payload["error"]))
    pages = payload.get("pages") if isinstance(payload, dict) else None
    if not isinstance(pages, list):
        raise ValueError("OCR reply has no pages")
    parts: list[str] = []
    truncated: list[int] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        index = int(page.get("index") or 0)
        text = str(page.get("text") or "").strip()
        reason = str(page.get("finish_reason") or "stop")
        if reason == "length":
            truncated.append(index)
            text = f"{text}\n[page truncated]"
        parts.append(f"--- page {index + 1} ---\n{text}")
    page_count = int(payload.get("page_count") or len(parts))
    return {
        "text": "\n\n".join(parts).strip(),
        "page_count": page_count,
        "truncated_pages": truncated,
        "purpose": str(payload.get("purpose") or ""),
        "id": str(payload.get("id") or ""),
    }


class DeepSeekApiOcrBackend(OCRBackend):
    """Cloud OCR via the DeepSeek tools API. Requires DEEPSEEK_API_KEY."""

    def __init__(self, config: OCRConfig):
        super().__init__("deepseek-api", config)
        key = getattr(config, "deepseek_api_key", None)
        self.api_key = key.strip() if isinstance(key, str) and key.strip() else None
        self._available = self.api_key is not None
        if self._available:
            logger.info("DeepSeek API OCR backend available")
        else:
            logger.debug("DeepSeek API OCR: no API key (set DEEPSEEK_API_KEY)")

    async def process_image(
        self,
        image_path: str,
        mode: str = "text",
        output_format: str = "text",
        language: str | None = None,
        region: list[int] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if not self.is_available():
            return {
                "success": False,
                "error": "DeepSeek API OCR needs DEEPSEEK_API_KEY",
                "backend": "deepseek-api",
            }
        path = Path(image_path)
        if not path.is_file():
            return {
                "success": False,
                "error": f"File not found: {image_path}",
                "backend": "deepseek-api",
            }
        size = path.stat().st_size
        if size > MAX_BYTES:
            return {
                "success": False,
                "error": f"File is {size} bytes. DeepSeek OCR accepts at most 100 MiB.",
                "backend": "deepseek-api",
            }
        purpose = str(kwargs.get("purpose") or getattr(self.config, "deepseek_ocr_purpose", "text_recognition"))
        if purpose not in PURPOSES:
            purpose = "text_recognition"
        try:
            data = path.read_bytes()
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    OCR_URL,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data={"purpose": purpose},
                    files={"file": (path.name, data, "application/octet-stream")},
                )
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"DeepSeek OCR HTTP {response.status_code}: {response.text[:500]}",
                    "backend": "deepseek-api",
                }
            parsed = parse_ocr_body(response.text)
        except Exception as exc:
            logger.error("DeepSeek API OCR failed: %s", exc)
            return {
                "success": False,
                "error": f"DeepSeek API OCR failed: {exc}",
                "backend": "deepseek-api",
            }
        text = parsed["text"]
        if not text:
            return {
                "success": False,
                "error": "DeepSeek OCR returned no page text",
                "backend": "deepseek-api",
            }
        alpha = sum(1 for c in text if c.isalnum() or c in ".,;:!?-()[]{}'\" ")
        confidence = round(alpha / max(len(text), 1), 4)
        pages = int(parsed["page_count"])
        return {
            "success": True,
            "text": text,
            "confidence": confidence,
            "confidence_source": "text_quality_heuristic",
            "confidence_note": "Cloud OCR returns raw page text. This number is not a model score.",
            "backend": "deepseek-api",
            "model": "deepseek-ocr-api",
            "mode": mode,
            "format": output_format,
            "metadata": {
                "purpose": purpose,
                "pages": pages,
                "truncated_pages": parsed["truncated_pages"],
                "ocr_id": parsed["id"],
                "bytes": size,
                "estimated_usd": round(pages * PAGE_USD, 6),
                "language_hint_ignored": language,
                "region_ignored": region is not None,
            },
        }

    def get_capabilities(self) -> dict[str, Any]:
        caps = super().get_capabilities()
        caps.update(
            {
                "modes": ["text"],
                "output_formats": ["text"],
                "gpu_support": False,
                "languages": ["auto"],
                "features": [
                    "cloud_ocr",
                    "pdf",
                    "word",
                    "powerpoint",
                    "images",
                    "page_text",
                ],
                "limitations": [
                    "requires_api_key",
                    "document_leaves_the_machine",
                    "no_bounding_boxes",
                    "no_tables",
                    "no_form_fields",
                    "raw_text_no_cleanup",
                    "100_mib",
                    "1000_pages",
                    "180_seconds",
                ],
                "cost_per_1000_pages": "$0.225",
                "endpoint": OCR_URL,
                "offline": False,
            }
        )
        return caps
