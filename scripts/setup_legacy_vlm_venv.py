#!/usr/bin/env python3
"""
Create/refresh .venv-legacy-vlm: an isolated venv pinned to transformers==4.37.2
for trust_remote_code models whose vendored code predates the modern Cache API
and cache_position (GOT-OCR2.0 today; DeepSeek-OCR/-2 and Unlimited-OCR share
the same "seen_tokens" pattern and would likely need the same treatment).

The main venv stays on transformers>=5.0 for backends that need it
(paddleocr-vl, dots-ocr, olmocr-2, ...); this sidecar venv is invoked via
subprocess by got_ocr_backend.py, never imported in-process.

Usage: python scripts/setup_legacy_vlm_venv.py [--force]
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = REPO_ROOT / ".venv-legacy-vlm"

PINNED_DEPS = [
    "torch>=2.0,<2.3",
    "transformers==4.37.2",
    "torchvision",
    "tiktoken",
    "verovio",
    "pillow",
    "accelerate",
    "numpy<2",  # torch<2.3 wheels are built against NumPy 1.x's C ABI
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Delete and recreate an existing venv")
    args = parser.parse_args()

    if VENV_DIR.exists():
        if not args.force:
            print(f"{VENV_DIR} already exists (use --force to recreate). Skipping.")
            return 0
        shutil.rmtree(VENV_DIR)

    subprocess.run(["uv", "venv", str(VENV_DIR), "--python", "3.12"], check=True, cwd=REPO_ROOT)
    subprocess.run(
        ["uv", "pip", "install", "--python", str(VENV_DIR), *PINNED_DEPS],
        check=True,
        cwd=REPO_ROOT,
    )
    print(f"Legacy VLM venv ready at {VENV_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
