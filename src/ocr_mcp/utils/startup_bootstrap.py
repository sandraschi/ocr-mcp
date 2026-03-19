"""
Single entry for OCR-MCP process startup: fix PyYAML dist-info, Tesseract, Poppler.

Call once after ``OCRConfig()`` and before ``BackendManager`` (or heavy imports).

Env:
- ``OCR_AUTO_BOOTSTRAP=0`` — skip PyYAML/Tesseract/Poppler/ML hints.
  Pip auto-install still runs if ``OCR_AUTO_INSTALL_DEPS=1``.
- ``OCR_AUTO_INSTALL_DEPS=1`` — pip/uv ML stack + optional Paddle (may restart process).
"""

from __future__ import annotations

import logging
import os

from ocr_mcp.core.config import OCRConfig

logger = logging.getLogger(__name__)


def run_ocr_startup_bootstrap(config: OCRConfig) -> None:
    """Run PyYAML repair, Tesseract (Windows), Poppler; optional pip installs; ML hints."""
    skip_core = os.getenv("OCR_AUTO_BOOTSTRAP", "1").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
    )

    if not skip_core:
        try:
            from ocr_mcp.utils.pyyaml_health import ensure_pyyaml_distribution_healthy

            ok, note = ensure_pyyaml_distribution_healthy(repair=True)
            if ok and note:
                logger.info("%s", note)
            elif not ok and note:
                logger.warning("%s", note)
        except Exception as e:
            logger.debug("PyYAML bootstrap: %s", e)

        try:
            from ocr_mcp.utils.tesseract_bootstrap import ensure_tesseract_windows

            ensure_tesseract_windows(config)
        except Exception as e:
            logger.debug("Tesseract bootstrap: %s", e)

        try:
            from ocr_mcp.utils.poppler_bootstrap import ensure_poppler_for_pdf

            ensure_poppler_for_pdf(config)
        except Exception as e:
            logger.debug("Poppler bootstrap: %s", e)

    if os.getenv("OCR_AUTO_INSTALL_DEPS", "").strip() == "1":
        try:
            from ocr_mcp.utils.ocr_pip_install import ensure_ocr_pip_dependencies

            ensure_ocr_pip_dependencies(log=logger)
        except Exception as e:
            logger.warning("OCR pip auto-install failed: %s", e)

    if not skip_core:
        try:
            from ocr_mcp.utils.ml_stack_hints import emit_ml_stack_hints

            emit_ml_stack_hints()
        except Exception as e:
            logger.debug("ML stack hints: %s", e)
