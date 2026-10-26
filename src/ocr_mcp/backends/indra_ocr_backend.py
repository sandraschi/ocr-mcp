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

"""
Indra OCR Backend - Datalab-to 1M-param CPU OCR.

Fast ONNX CPU engine (no torch/GPU): PDFs + images -> markdown/text/JSON
with layout blocks and reading order. ~15x Tesseract, ~76MB models.

Upstream: https://github.com/datalab-to/indra
HF weights: datalab-to/indra-ocr (OpenRAIL-M - see get_capabilities() license note)
Code license: Apache-2.0.

Python API used here (from upstream README):
    import indra_ocr
    conv = indra_ocr.load(threads=4, mode="auto", dpi=200, math=False)
    for i, page in conv.convert("paper.pdf"):
        page.markdown / page.text / page.blocks / page.lines / page.timings / page.source
"""

import asyncio
import importlib.util
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from ..core.backend_manager import OCRBackend
from ..core.config import OCRConfig

logger = logging.getLogger(__name__)


class IndraOCRBackend(OCRBackend):
    """Indra OCR backend - fast CPU OCR with layout blocks."""

    def __init__(self, config: OCRConfig):
        super().__init__("indra-ocr", config)
        self._converter = None
        self._converter_key: str | None = None
        self.model_name = "datalab-to/indra-ocr"
        self.cache_dir = config.model_dir / "indra_ocr"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if importlib.util.find_spec("indra_ocr") is not None:
            self._available = True
            logger.info("Indra OCR backend available (indra_ocr importable)")
        else:
            self._available = False
            logger.warning("Indra OCR backend not available: pip install indra-ocr")

    def _converter_options(self, **overrides: Any) -> dict[str, Any]:
        """Resolve load() kwargs from config + per-call overrides."""
        threads = int(overrides.get("threads", getattr(self.config, "indra_threads", 0) or 0) or 0)
        if threads <= 0:
            threads = max(1, (os.cpu_count() or 4) - 1)
        mode = str(overrides.get("indra_mode", getattr(self.config, "indra_mode", "auto") or "auto"))
        if mode not in ("auto", "ocr", "text"):
            mode = "auto"
        dpi = int(overrides.get("dpi", getattr(self.config, "indra_dpi", 200) or 200))
        math = bool(overrides.get("math", getattr(self.config, "indra_math", False)))
        return {"threads": threads, "mode": mode, "dpi": dpi, "math": math}

    def _ensure_converter(self, **overrides: Any):
        """Lazily build the indra_ocr converter (sync - call via to_thread)."""
        import indra_ocr

        opts = self._converter_options(**overrides)
        key = f"{opts['threads']}|{opts['mode']}|{opts['dpi']}|{opts['math']}"
        if self._converter is not None and self._converter_key == key:
            return self._converter

        model_dir = Path(getattr(self.config, "indra_model_dir", "") or "")
        load_kwargs: dict[str, Any] = {
            "threads": opts["threads"],
            "dpi": opts["dpi"],
            "mode": opts["mode"],
            "math": opts["math"],
        }
        # Use local copy when it looks complete, else let indra download from HF.
        if model_dir and (model_dir / "rec.onnx").exists():
            load_kwargs["path"] = str(model_dir)
        elif (self.cache_dir / "rec.onnx").exists():
            load_kwargs["path"] = str(self.cache_dir)

        logger.info(
            "Loading Indra OCR converter (threads=%s mode=%s dpi=%s math=%s)...",
            opts["threads"],
            opts["mode"],
            opts["dpi"],
            opts["math"],
        )
        t0 = time.time()
        self._converter = indra_ocr.load(**load_kwargs)
        self._converter_key = key
        logger.info("Indra OCR converter loaded in %.1fs", time.time() - t0)
        return self._converter

    async def load_model(self) -> bool:
        """Load the Indra converter (probe path uses this)."""
        if not self.is_available():
            logger.error("Indra OCR dependencies not available: pip install indra-ocr")
            return False
        try:
            await asyncio.to_thread(self._ensure_converter)
            return True
        except Exception as e:
            logger.error("Failed to load Indra OCR converter: %s", e)
            return False

    def _sync_convert(self, input_path: str, **overrides: Any) -> dict[str, Any]:
        """Blocking convert() - runs inside to_thread."""
        conv = self._ensure_converter(**overrides)
        max_pages = overrides.get("max_pages")
        convert_kwargs: dict[str, Any] = {}
        if max_pages is not None:
            convert_kwargs["max_pages"] = int(max_pages)

        texts: list[str] = []
        markdowns: list[str] = []
        all_blocks: list[dict[str, Any]] = []
        all_lines: list[dict[str, Any]] = []
        conf_sum = 0.0
        conf_n = 0
        sources: list[str] = []
        timings_ms = 0.0
        pages = 0

        for _i, page in conv.convert(input_path, **convert_kwargs):
            pages += 1
            texts.append(page.text or "")
            markdowns.append(page.markdown or "")
            sources.append(getattr(page, "source", "ocr"))
            try:
                timings_ms += float((getattr(page, "timings", {}) or {}).get("total_ms", 0) or 0)
            except (TypeError, ValueError):
                logger.debug("suppressed Exception in _sync_convert timings", exc_info=True)
            for b in getattr(page, "blocks", []) or []:
                if isinstance(b, dict):
                    all_blocks.append(
                        {
                            "label": b.get("label", "Text"),
                            "bbox": list(b.get("bbox", [])),
                            "text": b.get("text", ""),
                            "page": pages - 1,
                        }
                    )
            for ln in getattr(page, "lines", []) or []:
                box = list(getattr(ln, "box", []) or [])
                text = getattr(ln, "text", "") or ""
                try:
                    conf = float(getattr(ln, "conf", 0.0) or 0.0)
                except (TypeError, ValueError):
                    conf = 0.0
                if conf > 0:
                    conf_sum += conf
                    conf_n += 1
                all_lines.append({"bbox": box, "text": text, "confidence": conf, "page": pages - 1})

        full_text = "\n".join(t for t in texts if t).strip()
        full_markdown = "\n\n".join(m for m in markdowns if m).strip()
        avg_conf = round(conf_sum / conf_n, 4) if conf_n else 0.0
        return {
            "texts": texts,
            "markdown": full_markdown,
            "text": full_markdown or full_text,
            "raw_text": full_text,
            "blocks": all_blocks,
            "lines": all_lines,
            "confidence": avg_conf,
            "sources": sources,
            "pages": pages,
            "convert_timings_ms": timings_ms,
        }

    async def process_image(
        self,
        image_path: str,
        mode: str = "text",
        output_format: str = "text",
        language: str | None = None,
        region: list[int] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Process one image (or PDF - all pages concatenated) with Indra OCR."""
        if not self.is_available():
            return {"success": False, "error": "Indra OCR not available: pip install indra-ocr"}
        if language:
            logger.debug("Indra OCR auto-detects language, ignoring language=%s", language)

        input_path = image_path
        tmp_cropped: str | None = None
        try:
            if region and len(region) == 4 and not str(image_path).lower().endswith(".pdf"):
                from PIL import Image

                img = Image.open(image_path).convert("RGB").crop(tuple(region))
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                img.save(tmp, format="PNG")
                tmp.close()
                tmp_cropped = tmp.name
                input_path = tmp_cropped
            elif region:
                logger.warning("Indra OCR: region crop ignored for PDF input")

            t0 = time.time()
            data = await asyncio.to_thread(self._sync_convert, input_path, **kwargs)
            processing_time = time.time() - t0

            want_markdown = mode in ("format", "markdown") or output_format in ("markdown", "md")
            text_out = data["markdown"] if (want_markdown and data["markdown"]) else data["text"]
            if not text_out.strip():
                text_out = data["raw_text"]

            return {
                "success": True,
                "text": text_out.strip(),
                "markdown": data["markdown"],
                "confidence": data["confidence"],
                "backend": "indra-ocr",
                "model": self.model_name,
                "mode": mode,
                "format": "markdown" if want_markdown else "text",
                "processing_time": processing_time,
                "metadata": {
                    "pages": data["pages"],
                    "sources": data["sources"],
                    "convert_timings_ms": round(data["convert_timings_ms"], 1),
                    "blocks": len(data["blocks"]),
                    "lines": len(data["lines"]),
                },
                "blocks": data["blocks"],
                "raw_results": data["lines"],
            }
        except Exception as e:
            logger.error("Indra OCR processing error: %s", e)
            return {"success": False, "error": f"Indra OCR processing failed: {e!s}", "backend": "indra-ocr"}
        finally:
            if tmp_cropped:
                try:
                    os.unlink(tmp_cropped)
                except OSError:
                    logger.debug("suppressed OSError unlinking indra crop", exc_info=True)

    async def process_document(
        self,
        image_path: str,
        ocr_mode: str = "text",
        region: list[int] | None = None,
    ) -> dict[str, Any]:
        """Manager-compatible entry point (prefers process_document)."""
        res = await self.process_image(image_path, mode=ocr_mode, region=region)
        # Normalise to the process_document contract used by PP-OCR / GOT.
        if res.get("success"):
            res.setdefault("regions", [])
        return res

    def get_capabilities(self) -> dict[str, Any]:
        caps = super().get_capabilities()
        caps.update(
            {
                "name": "Indra OCR",
                "description": "Datalab-to Indra OCR - 1M-param CPU OCR, layout blocks + reading order",
                "modes": ["text", "format", "markdown"],
                "output_formats": ["text", "markdown", "json"],
                "gpu_support": False,
                "model_size": "~76MB",
                "languages": ["95 scripts: latin, cyrillic, greek, cjk, arabic, indic, thai, khmer..."],
                "strengths": [
                    "CPU-only, ONNX, no torch/GPU",
                    "15x Tesseract / 10x PP-OCR throughput",
                    "layout blocks + reading order + per-line boxes/confidence",
                    "rotated / tilted / dark-ground scans",
                    "digital-PDF text-layer hybrid (auto/ocr/text)",
                    "optional math-as-LaTeX (--math)",
                ],
                "limitations": [
                    "complex merged-cell tables",
                    "handwriting ~25% / degraded scans ~30%",
                    "math off by default",
                ],
                "license": "code Apache-2.0, weights OpenRAIL-M "
                "(free: research/personal/startups <$20M; no competitive API use)",
                "install_note": "pip install indra-ocr (models auto-download ~76MB from HF)",
            }
        )
        return caps
