"""
OCR-MCP Web Application Backend
FastAPI server providing web interface for OCR-MCP functionality
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any
import logging

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import uvicorn

from ..mcp_client import MCPClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OCR-MCP Web Interface",
    description="Web interface for OCR-MCP document processing",
    version="0.1.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="webapp/frontend/static"), name="static")
templates = Jinja2Templates(directory="webapp/frontend/templates")

# Initialize MCP client
mcp_client = MCPClient()

# Global state for processing jobs
processing_jobs: Dict[str, Dict[str, Any]] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize MCP client on startup"""
    try:
        # Initialize MCP client in background to not block startup
        task = asyncio.create_task(mcp_client.initialize())
        logger.info("MCP client initialization started")

        # Wait a bit to see if it completes quickly
        try:
            await asyncio.wait_for(task, timeout=1.0)
            logger.info("MCP client initialization completed quickly")
        except asyncio.TimeoutError:
            logger.info("MCP client initialization is running in background")

    except Exception as e:
        logger.error(f"Failed to start MCP client initialization: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await mcp_client.cleanup()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main web interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if mcp_client.connected else "degraded",
        "mcp_connected": mcp_client.connected,
        "mcp_status": "connected" if mcp_client.connected else "not_connected",
        "instructions": "Start OCR-MCP server separately: python -m src.ocr_mcp.server" if not mcp_client.connected else None,
        "version": "0.1.0"
    }

@app.get("/api/scanners")
async def get_scanners():
    """Get available scanners"""
    if not mcp_client.connected:
        raise HTTPException(
            status_code=503,
            detail="MCP server not connected. Please start the OCR-MCP server separately: python -m src.ocr_mcp.server"
        )
    try:
        result = await mcp_client.call_tool("list_scanners", {})
        return result
    except Exception as e:
        logger.error(f"Failed to get scanners: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scan")
async def scan_document(
    device_id: str = Form(...),
    dpi: int = Form(300),
    color_mode: str = Form("Color"),
    paper_size: str = Form("A4")
):
    """Scan document using specified scanner"""
    try:
        result = await mcp_client.call_tool("scan_document", {
            "device_id": device_id,
            "dpi": dpi,
            "color_mode": color_mode,
            "paper_size": paper_size
        })
        return result
    except Exception as e:
        logger.error(f"Failed to scan document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    ocr_mode: str = Form("text"),
    backend: str = Form("auto")
):
    """Upload and process a file"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Generate job ID
        job_id = f"job_{len(processing_jobs)}"

        # Store job info
        processing_jobs[job_id] = {
            "status": "processing",
            "filename": file.filename,
            "file_path": temp_file_path,
            "ocr_mode": ocr_mode,
            "backend": backend,
            "result": None,
            "error": None
        }

        # Process in background
        background_tasks.add_task(process_file_background, job_id, temp_file_path, ocr_mode, backend)

        return {"job_id": job_id, "status": "processing"}

    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    """Get processing job status"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = processing_jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "filename": job["filename"],
        "result": job["result"],
        "error": job["error"]
    }

@app.post("/api/process_batch")
async def process_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    ocr_mode: str = Form("text"),
    backend: str = Form("auto")
):
    """Process multiple files in batch"""
    try:
        file_paths = []
        filenames = []

        for file in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
                content = await file.read()
                temp_file.write(content)
                file_paths.append(temp_file.name)
                filenames.append(file.filename)

        # Generate job ID
        job_id = f"batch_job_{len(processing_jobs)}"

        # Store job info
        processing_jobs[job_id] = {
            "status": "processing",
            "filenames": filenames,
            "file_paths": file_paths,
            "ocr_mode": ocr_mode,
            "backend": backend,
            "result": None,
            "error": None
        }

        # Process in background
        background_tasks.add_task(process_batch_background, job_id, file_paths, ocr_mode, backend)

        return {"job_id": job_id, "status": "processing", "file_count": len(files)}

    except Exception as e:
        logger.error(f"Failed to process batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/backends")
async def get_backends():
    """Get available OCR backends"""
    if not mcp_client.connected:
        raise HTTPException(
            status_code=503,
            detail="MCP server not connected. Please start the OCR-MCP server separately: python -m src.ocr_mcp.server"
        )
    try:
        result = await mcp_client.call_tool("list_backends", {})
        return result
    except Exception as e:
        logger.error(f"Failed to get backends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_file_background(job_id: str, file_path: str, ocr_mode: str, backend: str):
    """Process single file in background"""
    try:
        result = await mcp_client.call_tool("process_document", {
            "source_path": file_path,
            "ocr_mode": ocr_mode,
            "backend": backend
        })

        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["result"] = result

        # Clean up temp file
        try:
            os.unlink(file_path)
        except:
            pass

    except Exception as e:
        logger.error(f"Failed to process file {job_id}: {e}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)

async def process_batch_background(job_id: str, file_paths: List[str], ocr_mode: str, backend: str):
    """Process batch files in background"""
    try:
        result = await mcp_client.call_tool("process_batch_documents", {
            "source_paths": file_paths,
            "ocr_mode": ocr_mode,
            "backend": backend
        })

        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["result"] = result

        # Clean up temp files
        for file_path in file_paths:
            try:
                os.unlink(file_path)
            except:
                pass

    except Exception as e:
        logger.error(f"Failed to process batch {job_id}: {e}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)

def main():
    """Entry point for running the webapp"""
    port = int(os.getenv("WEBAPP_PORT", "7460"))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
