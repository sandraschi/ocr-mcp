import sys
import os
import uvicorn
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
from io import BytesIO

# Add src to path to import backend logic
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(os.path.join(PROJECT_ROOT, "src"))

from ocr_mcp.backends.scanner.wia_scanner import WIABackend, ScanSettings, ScannerInfo

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScannerBridge")

app = FastAPI(title="OCR-MCP Scanner Bridge")

# CORS for accessing from everywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Backend
try:
    scanner_backend = WIABackend()
    if not scanner_backend.is_available():
        logger.warning(
            "WIA Backend initialized but reports unavailable (Are you on Windows?)"
        )
except Exception as e:
    logger.error(f"Failed to initialize WIA Backend: {e}")
    scanner_backend = None


class ScanRequest(BaseModel):
    device_id: str
    settings: dict


@app.get("/")
def health_check():
    return {
        "status": "running",
        "backend_available": scanner_backend.is_available()
        if scanner_backend
        else False,
    }


@app.get("/scanners")
def list_scanners():
    if not scanner_backend or not scanner_backend.is_available():
        raise HTTPException(status_code=503, detail="Scanner backend unavailable")

    scanners = scanner_backend.discover_scanners()
    return scanners


@app.get("/scanners/{device_id}/properties")
def get_scanner_props(device_id: str):
    if not scanner_backend:
        raise HTTPException(status_code=503, detail="Scanner backend unavailable")

    props = scanner_backend.get_scanner_properties(device_id)
    if not props:
        raise HTTPException(
            status_code=404, detail="Scanner not found or props unavailable"
        )
    return props


@app.post("/scan")
def perform_scan(request: ScanRequest):
    if not scanner_backend:
        raise HTTPException(status_code=503, detail="Scanner backend unavailable")

    # Convert dict settings to object
    try:
        settings_obj = ScanSettings(**request.settings)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid settings: {e}")

    image = scanner_backend.scan_document(request.device_id, settings_obj)

    if not image:
        raise HTTPException(status_code=500, detail="Scan failed")

    # Serialize Image to Base64
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return {"success": True, "image_data": img_str, "format": "png", "size": image.size}


if __name__ == "__main__":
    print("Starting Scanner Bridge on Port 15002...")
    print(
        "Make sure this script is running on the HOST machine (Windows) where scanners are connected."
    )
    uvicorn.run(app, host="0.0.0.0", port=15002)
