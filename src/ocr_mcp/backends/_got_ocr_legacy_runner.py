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
Standalone GOT-OCR2.0 runner for the isolated legacy-transformers venv.

stepfun-ai/GOT-OCR2_0's vendored trust_remote_code (modeling_GOT.py,
tokenization_qwen.py) targets transformers==4.37.2. Under the fleet's main
venv (transformers>=5.0, needed by paddleocr-vl/dots-ocr/etc.) it breaks in
three separate, escalating ways: a tokenizer None-injection bug, then a
Cache.seen_tokens removal, then a cache_position mismatch inside the vendored
forward() itself that risks silently wrong output rather than a clean crash.
Reproducing GOT-OCR's own stated environment in an isolated venv (see
scripts/setup_legacy_vlm_venv.py) sidesteps all three at once instead of
patching around each one.

Deliberately has NO import of the ocr_mcp package -- this runs under
.venv-legacy-vlm, which only has torch/transformers/tiktoken/verovio/etc.
installed, not the ocr-mcp project itself. Invoked by file path from
got_ocr_backend.py via subprocess, given the legacy venv's own python.exe.

Usage: python _got_ocr_legacy_runner.py <image_path> <ocr_type> <cache_dir>
Prints exactly one JSON object to stdout as the last line.
"""

import json
import sys


def main() -> None:
    image_path, ocr_type, cache_dir = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        import torch
        from transformers import AutoModel, AutoTokenizer

        # Vendored chat() hardcodes .cuda()/.half() with no CPU branch at all.
        torch.Tensor.cuda = lambda self, *a, **k: self
        torch.Tensor.half = lambda self, *a, **k: self

        def _from_pretrained_offline_fallback(cls, *a, **kw):
            # from_pretrained() does a network round-trip to check for updates
            # even when the cache is already complete; on this network a DNS
            # blip turns that into a hard failure instead of a graceful
            # fall-back to cache. Retry local-only before giving up.
            try:
                return cls.from_pretrained(*a, **kw)
            except Exception:
                return cls.from_pretrained(*a, local_files_only=True, **kw)

        model_name = "stepfun-ai/GOT-OCR2_0"
        tokenizer = _from_pretrained_offline_fallback(
            AutoTokenizer, model_name, trust_remote_code=True, cache_dir=cache_dir
        )
        model = _from_pretrained_offline_fallback(
            AutoModel,
            model_name,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            torch_dtype=torch.float32,
            cache_dir=cache_dir,
        )
        model = model.eval()

        text = model.chat(tokenizer, image_path, ocr_type=ocr_type)
        print(json.dumps({"success": True, "text": text}))
    except Exception as e:
        print(json.dumps({"success": False, "error": f"{type(e).__name__}: {e}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
