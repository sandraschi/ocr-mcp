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
Standalone DeepSeek-OCR / DeepSeek-OCR-2 / Unlimited-OCR runner for the
isolated legacy-transformers venv (.venv-legacy-vlm-deepseek).

All three vendor the same deepseek-v2 encoder lineage, target
transformers==4.46.3 per their own README/config, and their infer() hardcodes
.cuda() calls throughout the generate() call itself (image + input_ids +
seq_mask), same class of problem as GOT-OCR -- see got_ocr_backend.py's
_no_cuda_required for the pattern this mirrors.

Deliberately has NO import of the ocr_mcp package -- invoked by file path via
subprocess, given .venv-legacy-vlm-deepseek's own python.exe.

Usage: python _deepseek_ocr_legacy_runner.py <model_id> <image_path> <prompt> <cache_dir>
Prints exactly one JSON object to stdout as the last line.
"""

import json
import sys
import tempfile


def main() -> None:
    model_id, image_path, prompt, cache_dir = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

    try:
        import torch
        from transformers import AutoModel, AutoTokenizer

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

        tokenizer = _from_pretrained_offline_fallback(
            AutoTokenizer, model_id, trust_remote_code=True, cache_dir=cache_dir
        )
        # infer() hardcodes image tensors to .to(torch.bfloat16) regardless of
        # device; the model itself must match or generate() hits a dtype
        # mismatch ("Input type BFloat16 and bias type float"). bfloat16 (unlike
        # fp16) has reasonable CPU kernel coverage, so this is safe off-GPU too.
        model = _from_pretrained_offline_fallback(
            AutoModel,
            model_id,
            trust_remote_code=True,
            use_safetensors=True,
            torch_dtype=torch.bfloat16,
            cache_dir=cache_dir,
        )
        model = model.eval()

        with tempfile.TemporaryDirectory() as out_dir:
            text = model.infer(
                tokenizer,
                prompt=prompt,
                image_file=image_path,
                output_path=out_dir,
                base_size=1024,
                image_size=640,
                crop_mode=True,
                eval_mode=True,
            )
        print(json.dumps({"success": True, "text": text}))
    except Exception as e:
        print(json.dumps({"success": False, "error": f"{type(e).__name__}: {e}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
