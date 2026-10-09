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
    from contextlib import AsyncExitStack, asynccontextmanager

    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from ocr_mcp.server import app as _mcp

    @asynccontextmanager
    async def _lifespan(app_instance: FastAPI):
        # Compose the mounted MCP sub-app lifespan (fleet BUG-038); failure
        # only warns and serves REST (status quo, never a new crash).
        stack = AsyncExitStack()
        if _mcp_http is not None:
            try:
                await stack.enter_async_context(_mcp_http.lifespan(app_instance))
            except Exception as _ls_err:
                print(f"MCP sub-app lifespan not composed: {_ls_err}")
        try:
            yield
        finally:
            await stack.aclose()

    app = FastAPI(title="ocr-mcp", lifespan=_lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:10858",
            "http://127.0.0.1:10858",
            "http://localhost:10859",
            "http://127.0.0.1:10859",
            "http://tauri.localhost",
            "https://tauri.localhost",
            "tauri://localhost",
        ],
        allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # path="/": the sub-app serves the MCP endpoint at its own root; the parent
    # mount point supplies the /mcp prefix (fleet BUG-008).
    _mcp_http = _mcp.http_app(path="/")
    app.mount("/mcp", _mcp_http)

    host = os.environ.get("OCR_HOST", "127.0.0.1")
    port = int(os.environ.get("OCR_PORT", os.environ.get("MCP_PORT", "10859")))
    log_level = os.environ.get("OCR_LOG_LEVEL", "info")
    uvicorn.run(app, host=host, port=port, log_level=log_level)
