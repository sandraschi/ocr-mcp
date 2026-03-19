"""
One-shot hints after PyYAML/bootstrap: transformers import, flash-attn for GPU VRAM.

Does not install packages (except via separate ``OCR_AUTO_INSTALL_DEPS`` flow).
"""

from __future__ import annotations

import importlib.util
import logging

logger = logging.getLogger(__name__)

_hints_emitted = False


def emit_ml_stack_hints() -> None:
    """Log at most once per process: GPU + missing flash-attn; transformers smoke."""
    global _hints_emitted
    if _hints_emitted:
        return
    _hints_emitted = True

    try:
        import torch

        if torch.cuda.is_available():
            if importlib.util.find_spec("flash_attn") is None:
                logger.info(
                    "GPU detected but flash-attn is not installed — large VLM backends (e.g. "
                    "paddleocr-vl) may need much more VRAM. Optional: pip install flash-attn "
                    "(see docs/OCR_BACKEND_REQUIREMENTS.md)."
                )
    except Exception:
        pass

    try:
        import transformers  # noqa: F401

        logger.debug("transformers import OK for ML OCR backends.")
    except Exception as e:
        logger.debug("transformers not importable (install torch/transformers or uv sync): %s", e)
