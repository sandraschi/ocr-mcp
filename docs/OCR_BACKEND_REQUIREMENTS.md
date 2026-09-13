# OCR backend requirements

Per-backend pip packages, system deps, and config. For **how the web FastAPI backend gets its Python deps** (same venv as the package, PyTorch, `uv sync`), see **[BACKEND_DEPS.md](BACKEND_DEPS.md)**.

**Pip auto-install:** Default **off**. Set **`OCR_AUTO_INSTALL_DEPS=1`** so **`run_ocr_startup_bootstrap`** (FastAPI backend + MCP server, via `ocr_mcp.utils.ocr_pip_install`) installs missing **torch**, **transformers**, **accelerate**, **huggingface-hub**, **pyyaml**, **einops**, **addict**, **easydict**, **diffusers**, then tries **paddlepaddle** / **paddleocr**. The process may **restart** (`os.execv`) after installs. CUDA vs CPU **torch** is whatever pip resolves — prefer **`uv sync`** from `pyproject.toml` for a known-good env.

## Auto-install / env matrix

| Variable | Default | What it does |
|----------|---------|----------------|
| `OCR_AUTO_BOOTSTRAP` | `1` | PyYAML dist-info repair, Tesseract (Windows), Poppler (Windows), one-shot **flash-attn** hint on CUDA |
| `OCR_AUTO_BOOTSTRAP` | `0` | Skips the above; **`OCR_AUTO_INSTALL_DEPS` still runs** if set |
| `OCR_AUTO_INSTALL_DEPS` | unset | When `1`, pip/uv ML stack + optional Paddle (may restart process) |
| `OCR_AUTO_INSTALL_TESSERACT` | `1` | Windows: winget/choco/scoop Tesseract |
| `OCR_AUTO_INSTALL_POPPLER` | `1` | Windows: winget Poppler when `pdftoppm` missing |
| `TESSERACT_CMD` | — | Full path to `tesseract` |
| `POPPLER_PATH` | — | Folder containing `pdftoppm` / `pdftoppm.exe` |
| `MISTRAL_API_KEY` | — | Enables **mistral-ocr** |
| `OCR_CORPUS_DIR` | — | Optional folder for **corpus_management** SQLite (`corpus.db`); default `{OCR_CACHE_DIR}/corpus` |

| Backend | Typical install | Auto pip (`OCR_AUTO_INSTALL_DEPS=1`) | Bootstrap / notes |
|---------|-----------------|----------------------------------------|-------------------|
| **paddleocr-vl** | `uv sync` | torch stack | PyYAML repair; **flash-attn** not auto-installed — log hint on GPU |
| **deepseek-ocr2** | `uv sync` | torch stack | Optional flash-attn per model card |
| **olmocr-2** | `uv sync` | torch stack | Large HF model |
| **dots-ocr** | `uv sync` | torch stack | |
| **pp-ocrv5** | paddle wheels | **paddlepaddle**, **paddleocr** (optional block) | Pick CPU/CUDA wheel manually if pip default wrong |
| **qwen-layered** | `uv sync` | torch + diffusers | |
| **mistral-ocr** | `httpx` only | — | **API key** only; no auto-install |
| **got-ocr** | `uv sync` | torch stack | |
| **tesseract** | `pytesseract` in pyproject | — | **Binary**: Windows auto via bootstrap |
| **easyocr** | `easyocr` in pyproject | — | **Models** download on first OCR (logged once) |

## PyYAML (all Hugging Face–based backends)

- **Package:** install **`pyyaml`** (PyPI name `PyYAML`). Do **not** install the separate stub package named **`yaml`** on PyPI — it shadows the real module and breaks `yaml.dump`.
- **Broken wheels:** Some PyYAML 6.x wheels can omit `site-packages/yaml/__init__.py`, which makes `import yaml` a namespace package without `dump`. From repo root run **`uv run python scripts/ensure_pyyaml_init.py`** (or use `web_sota/start.ps1`, which runs it after `uv sync`).
- **Broken dist-info:** If `pyyaml-*.dist-info` has no `METADATA`/`RECORD` (e.g. partial uninstall), `import yaml` may still work but **transformers** fails with `Unable to compare versions for pyyaml>=5.1: found=None`. Fix: **stop the backend** (Windows may lock `yaml/_yaml*.pyd`), then run **`uv pip install --force-reinstall pyyaml`**. The ensure script and backend startup attempt the same repair automatically.
- **Declared in:** `pyproject.toml` (`pyyaml>=6.0`).

## Summary table

| Backend | Pip packages | System / env | Notes |
|---------|--------------|--------------|--------|
| **paddleocr-vl** | `transformers>=5.0.0`, `torch`, `accelerate`, `huggingface-hub`, **pyyaml**, PIL | — | `flash-attn` recommended on GPU (~3.3GB vs ~40GB VRAM) |
| **deepseek-ocr2** | `torch`, `torchvision`, `transformers`, `einops`, `addict`, `easydict`, PIL | — | Optional: `flash-attn==2.7.3`; doc suggests torch 2.6, transformers 4.46. Supersedes DeepSeek-OCR v1 (removed 2026-09-08 — same authors, newer architecture, no reason to keep both) |
| **olmocr-2** | `torch`, `transformers`, PIL | — | HF: allenai/olmOCR-2-7B-1025, ~7B params |
| **dots-ocr** | `torch`, `transformers`, `huggingface-hub`, PIL | — | HF: rednote-hilab/dots.ocr |
| **pp-ocrv5** | `paddlepaddle`, `paddleocr`, `numpy`, PIL | — | Optional; platform/CUDA variants for paddle |
| **qwen-layered** | `torch`, `diffusers`, `huggingface-hub`, PIL | — | HF: Qwen/Qwen-Image-Layered |
| **mistral-ocr** | `httpx` | `MISTRAL_API_KEY` or config `mistral_api_key` | API-only; no local model |
| **got-ocr** | isolated `.venv-legacy-vlm` (see below), or `torch`/`torchvision`/`transformers`/`tiktoken`/`verovio`/PIL in-process (broken on transformers>=5.0) | — | HF: stepfun-ai/GOT-OCR2_0, vendored code targets transformers==4.37.2 |
| **unlimited-ocr** | `torch`, `torchvision`, `transformers`, `einops`, `addict`, `easydict`, `matplotlib`, PIL | — | HF: baidu/Unlimited-OCR (same deepseek-v2 encoder family as deepseek-ocr2) |
| **tesseract** | `pytesseract`, PIL | Tesseract binary in PATH or `config.tesseract_cmd` | Languages: `config.tesseract_languages` (default eng) |
| **easyocr** | `easyocr`, PIL | — | First run downloads CRAFT/detector models |

PIL is provided by `pillow` (in pyproject). `httpx` is in pyproject. `pytesseract` and `easyocr` are in pyproject.

---

## got-ocr: isolated legacy-transformers venv

stepfun-ai/GOT-OCR2_0's `trust_remote_code` (`modeling_GOT.py`, `tokenization_qwen.py`) targets
`transformers==4.37.2`. Under the main venv's `transformers>=5.0` (needed by paddleocr-vl,
dots-ocr, etc.) it breaks three separate ways in sequence: a tokenizer `None`-injection bug
(`build_inputs_with_special_tokens` splicing in `cls_token_id`/`sep_token_id` that this
tokenizer never defines), `Cache.seen_tokens`/`get_max_length()` removal, and finally a
`cache_position` mismatch inside the vendored `forward()` itself -- the last one risks silently
wrong OCR output rather than a clean crash if patched incorrectly in-process.

Run **`python scripts/setup_legacy_vlm_venv.py`** once to create `.venv-legacy-vlm` (pinned
`transformers==4.37.2`, `torch<2.3`, `numpy<2`, `tiktoken`, `verovio`, `torchvision`,
`accelerate`). `got_ocr_backend.py` shells out to it via subprocess
(`_got_ocr_legacy_runner.py`) whenever it exists; without it, `process_image()` falls back to
the known-broken in-process path and logs a warning telling you to run the setup script.

## deepseek-ocr2 / unlimited-ocr: shared isolated venv

DeepSeek-OCR-2 and Unlimited-OCR ("Built on DeepSeek-OCR lineage" per its own model card) vendor
the same deepseek-v2 encoder, the same `seen_tokens` pattern, and the same
`infer(tokenizer, prompt=..., image_file=..., ...)` signature with `.cuda()` hardcoded ~14 times
throughout `generate()` and image tensors hardcoded to `.to(torch.bfloat16)`. Both needed more
than the got-ocr treatment: their pre-existing backend code called the wrong HF class
(`AutoModelForCausalLM` instead of `AutoModel`) and, for `deepseek_ocr2_backend.py`, invoked a
nonexistent tokenizer-as-processor API (`tokenizer(image, return_tensors="pt")`) that never
matched how these models actually work -- that code path had never run successfully.

(DeepSeek-OCR v1 had the identical bugs and needed the identical treatment, but was removed
2026-09-08 once DeepSeek-OCR-2 was confirmed working end-to-end -- same authors, newer
"Visual Causal Flow" architecture, no published reason to keep both registered.)

Run **`python scripts/setup_legacy_vlm_deepseek_venv.py`** once to create
`.venv-legacy-vlm-deepseek` (pinned `transformers==4.46.3`, `torch==2.6.0`, `torchvision==0.21.0`,
`tokenizers==0.20.3`, `einops`, `addict`, `easydict`, `numpy<2`). Both backends shell out to
the same runner (`_deepseek_ocr_legacy_runner.py`, parameterized by `model_id`) via subprocess
whenever it exists, loading the model in `bfloat16` (matching the hardcoded image dtype) and
neutralizing `.cuda()`/`.half()` the same way got-ocr's runner does. Without the venv, each
backend falls back to the known-broken in-process path and logs a warning.

Note: Unlimited-OCR's own README states `transformers==4.57.1`/`torch==2.10.0` (newer than
DeepSeek-OCR-2's) -- that's config metadata, not a hard requirement; the vendored `.cuda()` calls
in `generate()` are what actually break things, and those are identical across both, so the one
shared 4.46.3 venv works for both.

**HF download gotcha:** at least one of these weight downloads landed a file with the *correct*
total byte size but a zero-filled safetensors header (`Error while deserializing header: invalid
JSON in header: EOF...`) -- a resume-related corruption, not a code bug. If you hit this, delete
the blob under `~/.cache/ocr-mcp/models/<model>/models--.../blobs/<hash>` and re-download from
scratch (`huggingface_hub.snapshot_download` or `curl -C -` against the `resolve/main/...` URL,
verifying the final byte count against the `X-Linked-Size` response header) rather than trying to
patch the partial file.

---

## Required for ML backends (normally via `uv sync`)

These are project dependencies in `pyproject.toml`; run **`uv sync`** from the repo root. With **`OCR_AUTO_INSTALL_DEPS=1`**, the backend may attempt to install missing pieces at runtime (same list conceptually):

- **transformers** ≥ 5.0.0 — PaddleOCR-VL-1.5, DeepSeek, olmOCR-2, GOT-OCR, DOTS.OCR
- **torch** — all local ML backends
- **accelerate** — transformers ecosystem
- **huggingface-hub** — model downloads
- **pyyaml** — config / model code paths (PaddleOCR-VL, etc.)
- **einops** — DeepSeek-OCR-2
- **addict** — DeepSeek-OCR-2
- **easydict** — DeepSeek-OCR-2
- **diffusers** — Qwen-layered

## Optional (PP-OCRv5)

- **paddlepaddle** — PP-OCRv5 (use correct CUDA/CPU variant for your OS)
- **paddleocr** — PP-OCRv5

## API / config-only

- **mistral-ocr**: no extra pip beyond `httpx`. Set **`MISTRAL_API_KEY`** / **`MISTRAL_BASE_URL`** in the environment, or use the **web UI → Settings → Mistral OCR API** (persists for the **FastAPI backend process** via `POST /api/settings/mistral`; does not change the MCP stdio server unless you set env there too). Validate a key from the UI with **Test API key** or **`POST /api/settings/mistral/test`** (calls **`GET …/models`**).

## System

- **Startup bootstrap** (`ocr_mcp.utils.startup_bootstrap.run_ocr_startup_bootstrap`): Called from the **FastAPI backend** and **MCP server** immediately after `OCRConfig()`. Runs **PyYAML** repair (METADATA / force-reinstall), **Tesseract** (Windows silent install), **Poppler** (Windows silent winget when `pdftoppm` missing). Disable all with **`OCR_AUTO_BOOTSTRAP=0`**.
- **tesseract**: Python deps are `pytesseract` + Pillow (in pyproject). You still need the **Tesseract binary**. On **Windows**, bootstrap tries **winget** / **Chocolatey** / **Scoop** once per process. Set **`OCR_AUTO_INSTALL_TESSERACT=0`** to skip install attempts. On macOS/Linux, install the OS package or set **`TESSERACT_CMD`**. Optional: `config.tesseract_languages` for non-English tessdata.
- **poppler** (PDF → images via **pdf2image**): Set **`POPPLER_PATH`** to the folder containing **`pdftoppm`** / **`pdftoppm.exe`**, or rely on `PATH`. On **Windows**, bootstrap may run **`winget install oschwartz10612.Poppler`**. Set **`OCR_AUTO_INSTALL_POPPLER=0`** to skip winget. `convert_pdf_to_images` passes `config.poppler_path` into pdf2image.

## Version notes

- **PaddleOCR-VL-1.5**: requires **transformers ≥ 5.0.0**; config shim for `text_config` is applied in code.
- **DeepSeek-OCR-2**: model card suggests torch 2.6, transformers 4.46, flash-attn 2.7.3; we only enforce transformers ≥ 5 and einops/addict/easydict.
- **PP-OCRv5**: PaddlePaddle has separate CUDA/CPU pip packages; install the one that matches your environment.
