"""PyInstaller entrypoint for ocr-mcp HTTP sidecar."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn

if getattr(sys, "frozen", False):
    base = Path(sys._MEIPASS)
else:
    base = Path(__file__).resolve().parent
if str(base / "src") not in sys.path:
    sys.path.insert(0, str(base / "src"))

os.environ.setdefault("MCP_TRANSPORT", "http")

if __name__ == "__main__":
    from fastapi import FastAPI

    from ocr_mcp.server import app as _mcp

    app = FastAPI(title="ocr-mcp")
    app.mount("/mcp", _mcp.http_app())

    host = os.environ.get("OCR_HOST", "127.0.0.1")
    port = int(os.environ.get("OCR_PORT", os.environ.get("MCP_PORT", "10859")))
    log_level = os.environ.get("OCR_LOG_LEVEL", "info")
    uvicorn.run(app, host=host, port=port, log_level=log_level)
