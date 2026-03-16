# OCR models and engines

Summary of supported backends. Full specs and benchmarks: [AI_MODELS.md](../AI_MODELS.md).

## Backends (10+)

| Model | Text OCR | Tables | Formulas | Handwriting | Multi-lang | VRAM | Speed |
|-------|----------|--------|----------|-------------|------------|------|-------|
| **PaddleOCR-VL-1.5** | ✅ | ✅ | ✅ | ✅ | 109 langs | 3.3GB* | Fast |
| **DeepSeek-OCR-2** | ✅ | ✅ | ✅ | ⚠️ | ✅ | ~8GB | Medium |
| **olmOCR-2** | ✅ | ✅ | ✅ | ⚠️ | ✅ | ~16GB | Slow |
| Mistral OCR | ✅ | ✅ | ✅ | ✅ | ✅ | 0 (API) | Fast |
| Qwen2.5-VL | ✅ | ✅ | ✅ | ✅ | ✅ | ~16GB | Slow |
| GOT-OCR 2.0 | ✅ | ✅ | ✅ | ✅ | ✅ | ~2GB | Medium |
| DOTS.OCR | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ~6GB | Fast |
| PP-OCRv5 | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | low | Very Fast |
| EasyOCR | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | low | Medium |
| Tesseract | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | 0 | Very Fast |

*\* PaddleOCR-VL-1.5 requires `flash-attn` for 3.3GB; without it ~40GB (OOM on 24GB GPU)*

**Links:** [PaddleOCR-VL-1.5](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.5) · [DeepSeek-OCR-2](https://huggingface.co/deepseek-ai/DeepSeek-OCR-2) · [olmOCR-2](https://huggingface.co/allenai/olmOCR-2-7B-1025) · [Mistral OCR](https://mistral.ai) · [Qwen2.5-VL](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct) · [GOT-OCR 2.0](https://github.com/Ucas-HaoranWei/GOT-OCR2.0) · [DOTS.OCR](https://huggingface.co/rednote-hilab/dots.ocr) · [PP-OCRv5](https://huggingface.co/PaddlePaddle/PP-OCRv5) · [EasyOCR](https://github.com/JaidedAI/EasyOCR) · [Tesseract](https://github.com/tesseract-ocr/tesseract)

## Capabilities

- **Plain / formatted / fine-grained OCR** — text, layout, regions
- **Multi-crop OCR** — complex layouts by region
- **Document understanding** — tables, formulas, layout analysis
- **Auto-backend selection** — by document type, complexity, language, performance

## Hardware

- **Minimal (Tesseract/EasyOCR):** Any CPU, 4GB RAM
- **Recommended (PaddleOCR-VL/GOT-OCR2.0):** NVIDIA RTX 3060+ (12GB VRAM); PaddleOCR-VL needs flash-attn
- **High (DeepSeek-OCR-2/olmOCR-2/Qwen):** RTX 3090/4090 (24GB VRAM)

**Local LLM:** Auto-discovery of Ollama or LM Studio for semantic analysis.

> **GPU:** SOTA models are much faster with CUDA; CPU fallback is 10–50× slower.
