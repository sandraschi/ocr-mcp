#!/usr/bin/env python3
"""
Create/refresh .venv-legacy-vlm-deepseek: an isolated venv pinned to
transformers==4.46.3 / torch==2.6.0 for the deepseek-v2 encoder lineage --
DeepSeek-OCR, DeepSeek-OCR-2, and Unlimited-OCR all vendor the same
trust_remote_code pattern (same seen_tokens/cache_position mismatch class of
bug as GOT-OCR under the main venv's transformers>=5.0) and share the same
infer() signature, so one venv + one runner script serves all three.

The main venv stays on transformers>=5.0 for backends that need it; this
sidecar venv is invoked via subprocess by deepseek_backend.py (and, once
wired up, deepseek_ocr2_backend.py / unlimited_ocr_backend.py), never
imported in-process.

Usage: python scripts/setup_legacy_vlm_deepseek_venv.py [--force]
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = REPO_ROOT / ".venv-legacy-vlm-deepseek"

PINNED_DEPS = [
    "torch==2.6.0",
    "torchvision==0.21.0",
    "transformers==4.46.3",
    "tokenizers==0.20.3",
    "einops",
    "addict",
    "easydict",
    "accelerate",
    "pillow",
    "tqdm",
    "numpy<2",  # torch 2.6 wheels still assume NumPy 1.x's C ABI on this platform
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
        env={"UV_HTTP_TIMEOUT": "300", **__import__("os").environ},
    )
    print(f"Legacy deepseek-v2-family VLM venv ready at {VENV_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
