# OCR-MCP AI Models Documentation

*Last updated: 2026-05-14*

This document lists every OCR backend used by **OCR-MCP** (both the [web app](README.md#-installation) and the [MCP server](README.md#-installation)): what they are, accuracy/benchmarks, when to use them, and how to install or enable them. Backend names here match the `backend` parameter in tools and the web UI dropdown.

---

## Backend Summary

| Backend | Status | Params | VRAM | Benchmark | Best For |
|---------|--------|--------|------|-----------|----------|
| **PaddleOCR-VL-1.5** | ✅ SOTA | 0.9B | 3.3GB* | 94.5% OmniDocBench v1.5 | General documents, tables, formulas, scans |
| **MinerU2.5-Pro** | ✅ SOTA | 1.2B | ~4GB | SOTA multi-benchmark | Academic/technical docs, coarse-to-fine parsing |
| **Nemotron VL 8B** | ✅ New | 8B | ~16GB | DocVQA 91.2%, ChartQA 86.3% | Structured docs, invoices, forms, charts |
| **DeepSeek-OCR-2** | ✅ New | 3B | ~8GB | — (Jan 2026) | Structured markdown extraction |
| **olmOCR-2** | ✅ New | 7B | ~16GB | 82.4 olmOCR-Bench | Academic PDFs, math, multi-column |
| **Mistral OCR** | ✅ API | — | 0 | 94.9% claimed, 74% win rate | Cloud fallback, high accuracy |
| **Qwen2.5-VL** | ✅ Good | 7B | ~16GB | Strong on DocVQA | Complex layouts, VQA |
| **GOT-OCR 2.0** | ✅ Lean | 580M | ~2GB | Solid | Fast, mixed content, lean VRAM |
| **DeepSeek-OCR** | ✅ API | — | 0 | 92-95% | Cloud, enterprise docs |
| **DOTS.OCR** | ✅ OK | 3B | ~6GB | 87-90% tables | Table-heavy docs |
| **PP-OCRv5** | ✅ Legacy | ~100MB | low | 86-89% | High throughput, CJK |
| **EasyOCR** | ⚠️ Legacy | ~200MB | low | 82-87% | Handwriting, quick integration |
| **Tesseract** | ✅ Backstop | ~50MB | 0 | 78-85% | CPU-only fallback, always available |

*\* with `flash-attn` installed. Without it: ~40GB — do not run on GPU without flash-attn.*

**Auto-selection priority** (highest to lowest):
`paddleocr-vl → mistral-ocr → deepseek-ocr2 → mineru-2.5 → olmocr-2 → nemotron-vl → deepseek-ocr → qwen-layered → got-ocr → dots-ocr → pp-ocrv5 → easyocr → tesseract`

---

## SOTA Backends (2026)

### PaddleOCR-VL-1.5

**January 2026 — current SOTA for document parsing.**

Baidu's vision-language model combining a NaViT-style dynamic-resolution visual encoder with the lightweight ERNIE-4.5-0.3B language model. At 0.9B parameters it punches far above its weight class — outperforming 7B+ general LLMs on document benchmarks.

**Key features:**
- 94.5% accuracy on OmniDocBench v1.5 — top of all open-source models at release
- First model with *irregular box localization*: handles tilted, folded, screen-captured, and physically damaged documents
- Text, tables, formulas, charts, seals, rare characters, ancient books
- 109 languages including Chinese, Japanese, Arabic, Devanagari, Tibetan, Bengali
- ~3.3GB VRAM with flash-attn (mandatory); ~40GB without

**Installation note:**
```
pip install flash-attn --no-build-isolation
```
Without this, the model will OOM on a 24GB GPU. With it, leaves ~20GB free on the 4090.

**HF model:** `PaddlePaddle/PaddleOCR-VL-1.5`
**Backend name:** `paddleocr-vl`
**Aliases:** `paddleocr`, `paddle`, `paddleocr-vl-1.5`

---

### DeepSeek-OCR-2

**January 2026 — Visual Causal Flow architecture.**

DeepSeek's second-generation OCR model (arXiv:2601.20552). Builds on their OCR-1 with a new "Visual Causal Flow" approach that uses causal attention patterns to better track how visual context flows through document structure. Strong at producing clean structured markdown from complex source documents.

**Key features:**
- Visual Causal Flow for context-aware layout extraction
- Clean markdown output preserving document structure
- Two prompt modes: `<|grounding|>Convert the document to markdown.` (structured) and `Free OCR.` (raw text)
- 3B parameters, moderate VRAM

**Dependencies:**
```
pip install einops addict easydict
pip install flash-attn==2.7.3 --no-build-isolation
```

**HF model:** `deepseek-ai/DeepSeek-OCR-2`
**Backend name:** `deepseek-ocr2`
**Aliases:** `deepseek2`, `deepseek-ocr-2`

---

### MinerU2.5-Pro

**April 2026 — opendatalab coarse-to-fine document parsing VLM (62k+ GitHub stars).**

Developed by Shanghai AI Laboratory's OpenDataLab team. Uses a two-stage approach that decouples global layout analysis from local content recognition: the first stage performs layout analysis on downsampled images to identify structural elements, and the second stage performs targeted content recognition on native-resolution crops. This makes it both efficient and highly accurate.

**Key features:**
- Coarse-to-fine two-stage parsing strategy: layout first, then content
- 1.2B parameters, ~2.5GB VRAM — efficient for its accuracy class
- SOTA on multiple parsing benchmarks at time of release
- Excellent formula-to-LaTeX and table-to-HTML conversion
- 109-language OCR support through associated detection models
- Native PDF/DOCX/PPTX/XLSX support (via full mineru pipeline)
- 62.7k GitHub stars, Apache 2.0-based license

**Dependencies:**
```
pip install torch transformers
```
For full document pipeline (PDF/DOCX/PPTX/XLSX):
```
pip install mineru
```

**HF model:** `opendatalab/MinerU2.5-Pro-2604-1.2B`
**Backend name:** `mineru-2.5`
**Aliases:** `mineru`

---

### olmOCR-2

**October 2025 — Allen Institute for AI, built on Qwen2.5-VL-7B.**

Specialized for the hardest academic document parsing use cases: arXiv papers with multi-column layouts, math equations in various notations, complex tables in research papers, documents with headers/footers/sidebars. Uses GRPO reinforcement learning specifically tuned for equation and table accuracy. Scores 82.4 on olmOCR-Bench across 1,403 diverse PDF documents.

**Key features:**
- Best-in-class for scientific/academic documents
- Math equations in LaTeX notation
- Multi-column layout handling
- Fully open: data, code, and model weights
- Works with olmOCR toolkit for high-throughput batch processing (millions of docs via vLLM)

**HF model:** `allenai/olmOCR-2-7B-1025`
**Backend name:** `olmocr-2`
**Aliases:** `olmocr`, `olm`

---

## Established Backends

### Mistral OCR

**December 2025 — API-based, 94.9% claimed accuracy.**

Cloud API from Mistral AI. 74% win rate against their previous OCR 2 model in head-to-head comparisons. Produces markdown + HTML table output. Requires a Mistral API key. $1/1000 pages via batch API.

**Backend name:** `mistral-ocr`
**Requires:** `MISTRAL_API_KEY` environment variable

---

### Qwen2.5-VL (qwen-layered)

Alibaba's multimodal VLM, available in 2B/7B/72B. The 7B variant scores near GPT-4o on DocVQA and MathVista. Handles complex layouts, multi-language text including 90+ languages, and can process long documents. Still competitive with newer models for general VQA tasks combined with OCR.

**HF model:** `Qwen/Qwen2.5-VL-7B-Instruct`
**Backend name:** `qwen-layered`
**Alias:** `qwen`

---

### GOT-OCR 2.0

580M parameters, end-to-end unified architecture. Fast inference, lean VRAM (~2GB), good quality-per-resource ratio. Handles plain text, formatted text (markdown output), sheet music, math formulas, geometric shapes. Good fallback when you need something fast and the 0.9B PaddleOCR-VL is unavailable.

**HF model:** `stepfun-ai/GOT-OCR2_0`
**Backend name:** `got-ocr`
**Alias:** `got`

---

### DeepSeek-OCR (original)

The original DeepSeek-OCR cloud API backend. Still useful when DeepSeek-OCR-2 weights aren't downloaded yet, or for API-based processing.

**Backend name:** `deepseek-ocr`
**Alias:** `deepseek`

---

### DOTS.OCR

Specialized for document structure analysis, particularly table extraction. 3B parameters, document-specific architecture. Good for financial reports and structured tabular data. Less relevant now that PaddleOCR-VL-1.5 handles tables with better accuracy.

**HF model:** `rednote-hilab/dots.ocr`
**Backend name:** `dots-ocr`
**Alias:** `dots`

---

### Nemotron VL 8B (NVIDIA)

**June 2025 — best-in-class document intelligence VLM.**

NVIDIA's document-specialized vision-language model, built on Llama-3.1-8B-Instruct with a C-RADIOv2-H vision encoder. Trained on interleaved image-text data with commercial images across all three training stages. The strongest open model for structured document understanding — forms, invoices, charts, diagrams, and reports.

**Key features:**
- DocVQA 91.2% — top of all open VLMs for document question answering
- ChartQA 86.3% — best chart and graph understanding
- AI2D 85.0% — scientific diagram parsing
- OCRBench 839 — strong general OCR benchmark
- InfoVQA 77.4% — infographic and visual information extraction
- Multi-tile layout: up to 12 tiles at 512×512 px each, supporting aspect ratios up to 3072×1024
- 16K token context window
- Deployable on edge via AWQ 4-bit quantization (~5GB, Jetson Orin)

**Limitations:**
- **English only** — no multilingual OCR support
- NVIDIA Open Model License (not Apache 2.0)
- Requires additional dependencies: `timm`, `einops`, `open-clip-torch`
- Single image per call (no multi-image batching)
- Uses custom `.chat()` API — different from standard `AutoModelForCausalLM.generate()`

**Best for:**
- Invoices, receipts, and financial forms
- Contracts and legal documents with structured layouts
- Charts, graphs, and data visualizations with embedded text
- Scientific diagrams and technical illustrations
- Reports with mixed tables and text

**Not ideal for:**
- Multilingual documents (English only)
- Handwritten text (not trained for it)
- Batch/high-throughput processing (16GB VRAM, single-image)

**HF model:** `nvidia/Llama-3.1-Nemotron-Nano-VL-8B-V1`
**Backend name:** `nemotron-vl`
**Alias:** `nemotron`
**License:** [NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/)

**Installation:**
```
pip install timm einops open-clip-torch
```

**Comparison with other 7-8B VLMs:**

| Aspect | Nemotron VL 8B | olmOCR-2 (7B) | Qwen2.5-VL (7B) |
|--------|---------------|---------------|-----------------|
| DocVQA | **91.2%** | — | ~90% |
| ChartQA | **86.3%** | — | ~83% |
| AI2D | 85.0% | — | **87%** |
| OCRBench | 839 | — | **845** |
| Multilingual | No | **Yes** | **Yes** |
| VRAM (FP16) | ~16GB | ~16GB | ~16GB |
| Math/equations | Weak | **Strong** | Good |
| Structured docs | **Best** | Good | Good |

---

## Legacy Backends

### PP-OCRv5

Baidu's classic PaddleOCR pipeline (not to be confused with PaddleOCR-VL-1.5, which is an entirely different architecture). Fast CNN+Transformer hybrid. Very lightweight. Good for high-throughput batch jobs where accuracy requirements are modest, and for Chinese-English mixed text. CPU-capable.

**Backend name:** `pp-ocrv5`
**Alias:** `pp-ocr`

---

### EasyOCR

Deep learning OCR with CRAFT text detector. 80+ languages including Asian scripts. Has handwriting recognition. Known Windows Unicode issues in some configurations. Superseded in accuracy by all VLM-based models above, but still useful for quick GPU-accelerated jobs on simple content.

**Backend name:** `easyocr`

---

### Tesseract

The permanent backstop. Classic pipeline OCR, runs on CPU, zero VRAM, 100+ languages, always available. Accuracy 78-85% on clean printed text, degrades on complex layouts. Never removed — always the last fallback in auto-selection.

**Backend name:** `tesseract`

---

## Removed Backends

### ~~Florence-2~~ (removed 2026-02-27)

Microsoft Florence-2 is a general vision foundation model (object detection, image captioning, spatial grounding, segmentation). It has an `<OCR>` task prompt, but OCR is a minor capability, not its design goal. In practice the structured output methods were returning stubs and the confidence was hardcoded. Replaced by PaddleOCR-VL-1.5 which is purpose-built and benchmarked. The alias `florence` now redirects to `paddleocr-vl`.

---

## Model Selection Guide

| Situation | Recommended |
|-----------|-------------|
| General document scanning | `paddleocr-vl` |
| Tilted / folded / damaged document | `paddleocr-vl` (irregular box localization) |
| Scientific paper / arXiv PDF | `olmocr-2` or `mineru-2.5` |
| Document with math equations | `olmocr-2` or `mineru-2.5` |
| Need clean markdown output | `deepseek-ocr2` or `mineru-2.5` |
| Table-heavy document | `paddleocr-vl` (tables) or `dots-ocr` |
| Formula / LaTeX extraction | `paddleocr-vl` or `mineru-2.5` |
| Chart or diagram description | `paddleocr-vl` (chart task) |
| Chinese / CJK content | `paddleocr-vl` or `pp-ocrv5` |
| Arabic / Devanagari / rare scripts | `paddleocr-vl` |
| Maximum accuracy, no VRAM limit | `olmocr-2` (7B) or `mineru-2.5` (1.2B) |
| Minimum VRAM, still good quality | `got-ocr` (580M) or `mineru-2.5` (2.5GB) |
| CPU only, no GPU | `tesseract` |
| High volume batch | `pp-ocrv5` or `tesseract` |
| Cloud, no local model | `mistral-ocr` or `deepseek-ocr` |

---

## GPU Memory Requirements (RTX 4090, 24GB)

| Backend | VRAM | Fits on 4090? | Notes |
|---------|------|---------------|-------|
| PaddleOCR-VL-1.5 | 3.3GB | ✅ | Requires flash-attn |
| GOT-OCR 2.0 | ~2GB | ✅ | Very lean |
| MinerU2.5-Pro | ~2.5GB | ✅ | 1.2B params, efficient |
| DeepSeek-OCR-2 | ~8GB | ✅ | bfloat16 |
| DOTS.OCR | ~6GB | ✅ | |
| Qwen2.5-VL-7B | ~16GB | ✅ | bfloat16 |
| olmOCR-2 (7B) | ~16GB | ✅ | bfloat16 |
| Tesseract / PP-OCRv5 | 0 | ✅ | CPU only |
| PaddleOCR-VL-1.5 (no flash-attn) | ~40GB | ❌ OOM | Install flash-attn |

---

## Installing New Backends

```powershell
# PaddleOCR-VL-1.5 (critical dependency)
pip install flash-attn --no-build-isolation

# DeepSeek-OCR-2 dependencies
pip install einops addict easydict
pip install flash-attn==2.7.3 --no-build-isolation

# Models download automatically on first use via Hugging Face hub
# Cache location: configured in OCRConfig.model_dir
```

---

## Adding New Backends

To add a new OCR backend:

1. Create `src/ocr_mcp/backends/<name>_backend.py` extending `OCRBackend`
2. Implement `is_available()`, `_load_model()`, `process_image()`, `get_capabilities()`
3. Register in `src/ocr_mcp/core/backend_manager.py` `_initialize_backend_registry()`
4. Add to auto-selection `preference_order` at appropriate priority
5. Add alias to `backend_name_map`
6. Update this document and CHANGELOG.md

Key patterns from existing backends:
- Lazy model loading: check `self._model is not None` at start of `_load_model()`
- Always use `torch.inference_mode()` for generation
- Decode only generated tokens: `output_ids[0][input_ids.shape[1]:]`
- Return `{"success": True/False, "text": ..., "backend": name, "processing_time": ..., "confidence": ...}`

---

*Benchmarks sourced from: OmniDocBench v1.5, olmOCR-Bench, published model cards. Last updated 2026-02-27.*
