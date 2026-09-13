# ONBOARDING — ocr-mcp

First-run guide: what this is, what it costs, what to install, and how to
know it works. 5 minutes, no surprise downloads.

## What for

ocr-mcp is a local OCR + document-understanding server: 14 engines
(Tesseract, EasyOCR, PaddleOCR-VL, DeepSeek-OCR-2, GOT-OCR, Mistral OCR, …),
table/form extraction, WIA scanner control (Windows), and a React dashboard.
It exposes MCP tools (Claude Desktop) plus a REST backend the dashboard uses.

## Money / accounts

- **Free path (default):** local engines (Tesseract, EasyOCR, GOT-OCR) + any
  Ollama/LM Studio model you already run. No account, no key, no cost.
- **Paid path (optional):** Mistral OCR cloud API needs `MISTRAL_API_KEY`
  (pay-per-use on your Mistral account). Everything else keeps working
  without it.

## Prerequisites (wrappee + system)

- Python 3.12+ with `uv`, Node 22+ with `bun` (dashboard build only).
- **Tesseract** native binary for the `tesseract` backend
  (`winget install UB-Mannheim.TesseractOCR`, or set `TESSERACT_CMD`).
- **A WIA scanner** only if you want the Scanner pages; all OCR pages work
  without hardware.
- GPU (RTX 3060+) is recommended for the VLM backends (DeepSeek-OCR-2,
  PaddleOCR-VL); CPU works but is slow. Tesseract/EasyOCR run fine on CPU.

## Sanity check (60 seconds)

```powershell
Copy-Item .env.example .env
C:\Users\sandr\.local\bin\uv.exe sync
C:\Users\sandr\.local\bin\uv.exe run pytest tests/unit -q -p no:cacheprovider
```

Then start the stack (`.\start.ps1`), open the dashboard, and confirm:

1. Dashboard shows backend **connected** (green dot).
2. Dashboard shows the **AI setup banner** until a provider is configured —
   pick Ollama (free, local) or paste a Mistral key, then the banner clears.
3. Process page → upload any PNG → text comes back.

## Pitfalls

- First VLM run downloads GBs of models into `OCR_MODEL_DIR` — slow first
  start is normal; watch `GET /api/models/status` for progress.
- `MCP_TRANSPORT=stdio` (default, Claude Desktop) vs `http` (dashboard).
  The dashboard needs the HTTP backend on **10859**.
- Tesseract "not found" → set `TESSERACT_CMD` to `tesseract.exe` in `.env`.
- Dashboard port clash → `just zombie-clean` (fleet helper) then retry.

## MOCK-until-onboarded

Until a provider is configured, LLM-dependent surfaces (Chat, AI Settings)
show declared **MOCK** sample content. It clears automatically after a
successful provider test. See `docs/CONFIGURATION.md` (LLM section).
