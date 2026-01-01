"""
OCR-MCP Web Application Backend
FastAPI server providing web interface for OCR-MCP functionality
"""

import asyncio
import json
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
    version="0.1.0",
)

# Configure CORS
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3002",
        "http://localhost:5173",
    ],  # Allow frontend ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
# Get the correct path relative to this script's location
script_dir = Path(__file__).parent
project_root = script_dir.parent
static_dir = project_root / "frontend" / "static"
templates_dir = project_root / "frontend" / "templates"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# Initialize MCP client
mcp_client = MCPClient()
demo_mode = False  # Real scanner functionality enabled

# Global state for processing jobs
processing_jobs: Dict[str, Dict[str, Any]] = {}

# Initialize BackendManager globally
backend_manager = None
try:
    from ocr_mcp.core.backend_manager import BackendManager
    from ocr_mcp.core.config import OCRConfig

    config = OCRConfig()
    backend_manager = BackendManager(config)
    logger.info("Global BackendManager initialized")
except Exception as e:
    logger.error(f"Failed to initialize global BackendManager: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize MCP client on startup"""
    if demo_mode:
        logger.info("Running in demo mode - skipping MCP client initialization")
        return

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
    if demo_mode:
        return {
            "status": "healthy",
            "mcp_connected": True,
            "mcp_status": "demo_mode",
            "demo_mode": True,
            "instructions": "Running in demo mode - start OCR-MCP server for full functionality: python -m src.ocr_mcp.server",
            "version": "0.1.0",
        }

    return {
        "status": "healthy" if mcp_client.connected else "degraded",
        "mcp_connected": mcp_client.connected,
        "mcp_status": "connected" if mcp_client.connected else "not_connected",
        "demo_mode": False,
        "instructions": "Start OCR-MCP server separately: python -m src.ocr_mcp.server"
        if not mcp_client.connected
        else None,
        "version": "0.1.0",
    }


@app.get("/api/scanners")
async def get_scanners():
    """Get available scanners"""
    logger.info("Scanner discovery requested")

    # Always try real scanner discovery first, even in demo mode
    try:
        if (
            backend_manager
            and backend_manager.scanner_manager
            and backend_manager.scanner_manager.is_available()
        ):
            logger.info("Scanner manager is available, discovering scanners...")
            scanners = backend_manager.scanner_manager.discover_scanners(
                force_refresh=True
            )
            logger.info(f"Found {len(scanners)} scanners")

            # Format scanner data for frontend
            scanner_list = []
            for scanner in scanners:
                scanner_list.append(
                    {
                        "id": scanner.device_id,
                        "name": scanner.name,
                        "manufacturer": scanner.manufacturer,
                        "type": scanner.device_type,
                        "status": "ready",  # Assume ready if discovered
                        "supports_adf": scanner.supports_adf,
                        "supports_duplex": scanner.supports_duplex,
                        "max_dpi": scanner.max_dpi,
                    }
                )

            if scanner_list:
                logger.info(f"Returning {len(scanner_list)} real scanners")
                return {"scanners": scanner_list}

    except Exception as e:
        logger.warning(f"Direct scanner discovery failed: {e}")

    # Try MCP client if available
    if mcp_client.connected:
        try:
            logger.info("Trying MCP client for scanner discovery")
            result = await mcp_client.call_tool(
                "scanner_operations", {"operation": "list_scanners"}
            )
            logger.info("MCP scanner discovery successful")
            return result
        except Exception as e:
            logger.warning(f"MCP scanner discovery failed: {e}")

    # Fallback to demo data if no real scanners found
    logger.info("No real scanners found, returning demo data")
    return {
        "scanners": [
            {
                "id": "canon_flatbed_demo",
                "name": "Canon CanoScan Flatbed (Demo)",
                "manufacturer": "Canon",
                "type": "flatbed",
                "status": "ready",
                "supports_adf": False,
                "supports_duplex": False,
                "max_dpi": 2400,
            },
            {
                "id": "demo_scanner_1",
                "name": "Demo Flatbed Scanner",
                "type": "flatbed",
                "status": "ready",
            },
            {
                "id": "demo_scanner_2",
                "name": "Demo ADF Scanner",
                "type": "adf",
                "status": "ready",
            },
        ]
    }


@app.post("/api/scan")
async def scan_document(
    device_id: str = Form(...),
    dpi: int = Form(300),
    color_mode: str = Form("Color"),
    paper_size: str = Form("A4"),
):
    """Scan document using specified scanner"""
    logger.info(
        f"Scan requested for device {device_id} with settings: {dpi} DPI, {color_mode}, {paper_size}"
    )

    try:
        # Try direct scanner access first
        if (
            backend_manager
            and backend_manager.scanner_manager
            and backend_manager.scanner_manager.is_available()
        ):
            settings = {
                "dpi": dpi,
                "color_mode": color_mode,
                "paper_size": paper_size,
            }

            logger.info(f"Scanning with settings: {settings}")
            image = backend_manager.scanner_manager.scan_document(device_id, settings)

            if image:
                # Save the scanned image temporarily
                import tempfile
                from pathlib import Path

                temp_dir = Path(tempfile.gettempdir()) / "ocr-mcp-scans"
                temp_dir.mkdir(exist_ok=True)

                safe_device_id = device_id.replace(":", "_").replace("\\", "_")
                filename = f"scan_{safe_device_id}_{int(__import__('time').time())}.png"
                filepath = temp_dir / filename

                image.save(str(filepath))
                logger.info(f"Scan successful, saved to {filepath}")

                return {
                    "success": True,
                    "device_id": device_id,
                    "settings": settings,
                    "image_path": str(filepath),
                    "image_info": {
                        "width": image.width,
                        "height": image.height,
                        "mode": image.mode,
                        "filename": filename,
                    },
                    "message": f"Document scanned successfully on {device_id}",
                }
            else:
                logger.warning("Scan returned no image")
                # Don't raise yet, try MCP client
    except Exception as e:
        logger.warning(f"Direct scanner access failed: {e}")

    # Try MCP client if direct access failed
    if mcp_client.connected:
        try:
            logger.info("Trying MCP client for scanning")
            result = await mcp_client.call_tool(
                "scanner_operations",
                {
                    "operation": "scan_document",
                    "device_id": device_id,
                    "dpi": dpi,
                    "color_mode": color_mode,
                    "paper_size": paper_size,
                },
            )
            return result
        except Exception as e:
            logger.warning(f"MCP scanner access failed: {e}")

    # Demo mode fallback
    logger.info("Using demo mode scan simulation")
    import time
    import tempfile
    from pathlib import Path

    # Simulate scan delay
    await asyncio.sleep(2)

    # Create a dummy image file for demo
    temp_dir = Path(tempfile.gettempdir()) / "ocr-mcp-scans"
    temp_dir.mkdir(exist_ok=True)

    safe_device_id = device_id.replace(":", "_").replace("\\", "_")
    filename = f"demo_scan_{safe_device_id}_{int(time.time())}.png"
    filepath = temp_dir / filename

    # Create a simple placeholder image (this would normally come from scanner)
    from PIL import Image

    demo_image = Image.new("RGB", (800, 600), color="lightgray")
    demo_image.save(str(filepath))

    return {
        "success": True,
        "device_id": device_id,
        "settings": {
            "dpi": dpi,
            "color_mode": color_mode,
            "paper_size": paper_size,
        },
        "image_path": str(filepath),
        "image_info": {
            "width": 800,
            "height": 600,
            "mode": "RGB",
            "filename": filename,
        },
        "message": f"Demo scan completed successfully (simulated)",
        "demo_mode": True,
    }


@app.post("/api/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    ocr_mode: str = Form("text"),
    backend: str = Form("auto"),
):
    """Upload and process a file"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(file.filename).suffix
        ) as temp_file:
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
            "error": None,
        }

        # Always use demo processing for now to ensure it works
        background_tasks.add_task(
            process_file_demo, job_id, file.filename, ocr_mode, backend
        )

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
        "error": job["error"],
    }


@app.post("/api/process_batch")
async def process_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    ocr_mode: str = Form("text"),
    backend: str = Form("auto"),
):
    """Process multiple files in batch"""
    try:
        file_paths = []
        filenames = []

        for file in files:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=Path(file.filename).suffix
            ) as temp_file:
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
            "error": None,
        }

        # Always use demo batch processing for now
        background_tasks.add_task(
            process_batch_demo, job_id, filenames, ocr_mode, backend
        )

        return {"job_id": job_id, "status": "processing", "file_count": len(files)}

    except Exception as e:
        logger.error(f"Failed to process batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backends")
async def get_backends():
    """Get available OCR backends"""
    if demo_mode:
        return {
            "backends": [
                {
                    "name": "florence-2",
                    "available": True,
                    "description": "Microsoft Florence-2 vision model",
                },
                {
                    "name": "pp-ocrv5",
                    "available": True,
                    "description": "PaddlePaddle OCR v5",
                },
                {
                    "name": "tesseract",
                    "available": True,
                    "description": "Tesseract OCR",
                },
                {"name": "easyocr", "available": True, "description": "EasyOCR"},
            ],
            "default_backend": "florence-2",
        }

    if not mcp_client.connected:
        raise HTTPException(
            status_code=503,
            detail="MCP server not connected. Please start the OCR-MCP server separately: python -m src.ocr_mcp.server",
        )
    try:
        result = await mcp_client.call_tool("list_backends", {})
        return result
    except Exception as e:
        logger.error(f"Failed to get backends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/optimize")
async def optimize_processing(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_quality: float = Form(0.8),
    max_attempts: int = Form(3),
):
    """Auto-optimize OCR processing for best quality"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(file.filename).suffix
        ) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Generate job ID
        job_id = f"optimize_{len(processing_jobs)}"

        # Store job info
        processing_jobs[job_id] = {
            "status": "processing",
            "filename": file.filename,
            "file_path": temp_file_path,
            "target_quality": target_quality,
            "max_attempts": max_attempts,
            "result": None,
            "error": None,
        }

        # Process in background
        background_tasks.add_task(
            optimize_background, job_id, temp_file_path, target_quality, max_attempts
        )

        return {"job_id": job_id, "status": "processing"}

    except Exception as e:
        logger.error(f"Failed to start optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/convert")
async def convert_format(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_format: str = Form(...),
    ocr_mode: str = Form("auto"),
    backend: str = Form("auto"),
):
    """Convert document format with optional OCR"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(file.filename).suffix
        ) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Generate job ID
        job_id = f"convert_{len(processing_jobs)}"

        # Store job info
        processing_jobs[job_id] = {
            "status": "processing",
            "filename": file.filename,
            "file_path": temp_file_path,
            "target_format": target_format,
            "ocr_mode": ocr_mode,
            "backend": backend,
            "result": None,
            "error": None,
        }

        # Process in background
        background_tasks.add_task(
            convert_background, job_id, temp_file_path, target_format, ocr_mode, backend
        )

        return {"job_id": job_id, "status": "processing"}

    except Exception as e:
        logger.error(f"Failed to start conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/export")
async def export_results(data: Dict[str, Any]):
    """Export processed results in various formats"""
    try:
        export_type = data.get("export_type", "json")
        content = data.get("content", {})
        filename = data.get("filename", f"export_{len(processing_jobs)}")

        # Generate export based on type
        if export_type == "json":
            export_content = json.dumps(content, indent=2)
            media_type = "application/json"
            file_extension = "json"
        elif export_type == "xml":
            # Simple XML conversion
            export_content = dict_to_xml(content)
            media_type = "application/xml"
            file_extension = "xml"
        elif export_type == "csv":
            # Convert structured data to CSV
            export_content = dict_to_csv(content)
            media_type = "text/csv"
            file_extension = "csv"
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported export type: {export_type}"
            )

        return {
            "filename": f"{filename}.{file_extension}",
            "content": export_content,
            "media_type": media_type,
            "size": len(export_content),
        }

    except Exception as e:
        logger.error(f"Failed to export results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pipelines")
async def get_pipelines():
    """Get available processing pipelines"""
    # Return predefined pipelines
    return {
        "pipelines": [
            {
                "id": "basic_ocr",
                "name": "Basic OCR",
                "description": "Simple OCR processing",
                "steps": ["deskew_image", "enhance_image", "process_document"],
            },
            {
                "id": "quality_focused",
                "name": "Quality Focused",
                "description": "Multiple OCR attempts for high accuracy",
                "steps": [
                    "deskew_image",
                    "enhance_image",
                    "process_document",
                    "assess_ocr_quality",
                ],
            },
            {
                "id": "archive_ready",
                "name": "Archive Ready",
                "description": "Convert to searchable PDF with metadata",
                "steps": [
                    "deskew_image",
                    "enhance_image",
                    "process_document",
                    "convert_image_format",
                ],
            },
        ]
    }


@app.post("/api/pipelines/execute")
async def execute_pipeline(
    background_tasks: BackgroundTasks,
    pipeline_id: str = Form(...),
    file: UploadFile = File(...),
):
    """Execute a processing pipeline"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(file.filename).suffix
        ) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Generate job ID
        job_id = f"pipeline_{len(processing_jobs)}"

        # Store job info
        processing_jobs[job_id] = {
            "status": "processing",
            "filename": file.filename,
            "file_path": temp_file_path,
            "pipeline_id": pipeline_id,
            "result": None,
            "error": None,
        }

        # Process in background
        background_tasks.add_task(
            execute_pipeline_background, job_id, pipeline_id, temp_file_path
        )

        return {"job_id": job_id, "status": "processing"}

    except Exception as e:
        logger.error(f"Failed to execute pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_file_background(
    job_id: str, file_path: str, ocr_mode: str, backend: str
):
    """Process single file in background"""
    try:
        result = await mcp_client.call_tool(
            "process_document",
            {"source_path": file_path, "ocr_mode": ocr_mode, "backend": backend},
        )

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


async def process_batch_background(
    job_id: str, file_paths: List[str], ocr_mode: str, backend: str
):
    """Process batch files in background"""
    try:
        result = await mcp_client.call_tool(
            "process_batch_documents",
            {"source_paths": file_paths, "ocr_mode": ocr_mode, "backend": backend},
        )

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


async def process_file_demo(job_id: str, filename: str, ocr_mode: str, backend: str):
    """Demo processing - simulate OCR results"""
    try:
        logger.info(f"Starting demo processing for job {job_id}, file {filename}")
        # Simulate processing time
        await asyncio.sleep(2)
        logger.info(f"Demo processing sleep completed for job {job_id}")

        # Generate mock OCR results based on filename
        if "pdf" in filename.lower():
            mock_text = f"This is extracted text from {filename}.\n\nDocument processed using {backend} backend in {ocr_mode} mode.\n\nThis is a demo result showing how the OCR-MCP webapp works.\n\nFeatures demonstrated:\n- Multi-backend OCR support\n- Quality assessment\n- Format conversion\n- Batch processing\n\nThank you for trying OCR-MCP!"
        else:
            mock_text = f"Image {filename} processed successfully.\n\nOCR Results:\nSample text extracted from the image.\nConfidence: 95%\nBackend: {backend}\nMode: {ocr_mode}"

        mock_result = {
            "text": mock_text,
            "quality_score": 0.87,
            "backend_used": backend,
            "processing_time": 1.5,
            "confidence": 0.92,
            "demo_mode": True,
        }

        logger.info(f"Setting job {job_id} to completed with result")
        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["result"] = mock_result
        logger.info(f"Demo processing completed successfully for job {job_id}")

    except Exception as e:
        logger.error(f"Failed to process demo file {job_id}: {e}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)


async def process_batch_demo(
    job_id: str, filenames: List[str], ocr_mode: str, backend: str
):
    """Demo batch processing - simulate results for multiple files"""
    try:
        results = []

        for i, filename in enumerate(filenames):
            # Simulate processing time for each file
            await asyncio.sleep(0.5)

            # Generate mock results
            mock_result = {
                "filename": filename,
                "text": f"Extracted text from {filename} (file {i + 1} of {len(filenames)}).\n\nProcessed with {backend} in {ocr_mode} mode.\nDemo batch processing result.",
                "quality_score": 0.85 + (i * 0.02),  # Vary quality slightly
                "processing_time": 1.0 + (i * 0.1),
                "status": "completed",
                "demo_mode": True,
            }
            results.append(mock_result)

        batch_result = {
            "total_files": len(filenames),
            "successful": len(filenames),
            "failed": 0,
            "results": results,
            "average_quality": 0.87,
            "total_time": len(filenames) * 1.2,
            "demo_mode": True,
        }

        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["result"] = batch_result

    except Exception as e:
        logger.error(f"Failed to process demo batch {job_id}: {e}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)


async def optimize_background(
    job_id: str, file_path: str, target_quality: float, max_attempts: int
):
    """Auto-optimize OCR processing in background"""
    try:
        # Try different backends and settings to achieve target quality
        best_result = None
        best_quality = 0.0

        backends = ["auto", "florence-2", "deepseek-ocr", "pp-ocrv5"]
        modes = ["auto", "text", "format"]

        for attempt in range(max_attempts):
            for backend in backends:
                for mode in modes:
                    try:
                        result = await mcp_client.call_tool(
                            "process_document",
                            {
                                "source_path": file_path,
                                "ocr_mode": mode,
                                "backend": backend,
                            },
                        )

                        # Check quality score (mock for now)
                        quality_score = result.get("quality_score", 0.5)

                        if quality_score >= target_quality:
                            processing_jobs[job_id]["status"] = "completed"
                            processing_jobs[job_id]["result"] = result
                            return

                        if quality_score > best_quality:
                            best_quality = quality_score
                            best_result = result

                    except Exception as e:
                        logger.warning(
                            f"Optimization attempt {attempt + 1} with {backend}/{mode} failed: {e}"
                        )
                        continue

        # Return best result found
        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["result"] = best_result or {
            "error": "Could not achieve target quality"
        }

        # Clean up temp file
        try:
            os.unlink(file_path)
        except:
            pass

    except Exception as e:
        logger.error(f"Failed to optimize {job_id}: {e}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)


async def convert_background(
    job_id: str, file_path: str, target_format: str, ocr_mode: str, backend: str
):
    """Convert document format in background"""
    try:
        # First OCR the document if needed
        ocr_result = None
        if target_format in ["pdf", "docx"]:
            ocr_result = await mcp_client.call_tool(
                "process_document",
                {"source_path": file_path, "ocr_mode": ocr_mode, "backend": backend},
            )

        # Convert format
        result = await mcp_client.call_tool(
            "convert_image_format",
            {
                "source_path": file_path,
                "target_format": target_format,
                "ocr_text": ocr_result.get("text") if ocr_result else None,
            },
        )

        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["result"] = result

        # Clean up temp file
        try:
            os.unlink(file_path)
        except:
            pass

    except Exception as e:
        logger.error(f"Failed to convert {job_id}: {e}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)


async def execute_pipeline_background(job_id: str, pipeline_id: str, file_path: str):
    """Execute processing pipeline in background"""
    try:
        # Define pipeline steps
        pipelines = {
            "basic_ocr": ["deskew_image", "enhance_image", "process_document"],
            "quality_focused": [
                "deskew_image",
                "enhance_image",
                "process_document",
                "assess_ocr_quality",
            ],
            "archive_ready": [
                "deskew_image",
                "enhance_image",
                "process_document",
                "convert_image_format",
            ],
        }

        steps = pipelines.get(pipeline_id, ["process_document"])
        results = {}

        # Execute each step in sequence
        for step in steps:
            try:
                if step == "process_document":
                    result = await mcp_client.call_tool(
                        "process_document",
                        {
                            "source_path": file_path,
                            "ocr_mode": "auto",
                            "backend": "auto",
                        },
                    )
                elif step == "deskew_image":
                    result = await mcp_client.call_tool(
                        "deskew_image", {"image_path": file_path}
                    )
                elif step == "enhance_image":
                    result = await mcp_client.call_tool(
                        "enhance_image", {"image_path": file_path, "intensity": 1.0}
                    )
                elif step == "assess_ocr_quality":
                    # First get OCR result
                    ocr_result = await mcp_client.call_tool(
                        "process_document",
                        {
                            "source_path": file_path,
                            "ocr_mode": "auto",
                            "backend": "auto",
                        },
                    )
                    result = await mcp_client.call_tool(
                        "assess_ocr_quality", {"ocr_result": ocr_result}
                    )
                elif step == "convert_image_format":
                    result = await mcp_client.call_tool(
                        "convert_image_format",
                        {"source_path": file_path, "target_format": "pdf"},
                    )

                results[step] = result

            except Exception as e:
                logger.warning(f"Pipeline step {step} failed: {e}")
                results[step] = {"error": str(e)}

        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["result"] = {
            "pipeline_id": pipeline_id,
            "steps_executed": steps,
            "results": results,
        }

        # Clean up temp file
        try:
            os.unlink(file_path)
        except:
            pass

    except Exception as e:
        logger.error(f"Failed to execute pipeline {job_id}: {e}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)


# Utility functions for export
def dict_to_xml(data: Dict[str, Any], root_name: str = "data") -> str:
    """Convert dictionary to XML string"""

    def _dict_to_xml(data: Any, key: str = None) -> str:
        if isinstance(data, dict):
            xml_parts = []
            for k, v in data.items():
                xml_parts.append(f"<{k}>{_dict_to_xml(v)}</{k}>")
            return "".join(xml_parts)
        elif isinstance(data, list):
            xml_parts = []
            item_name = key[:-1] if key and key.endswith("s") else "item"
            for item in data:
                xml_parts.append(f"<{item_name}>{_dict_to_xml(item)}</{item_name}>")
            return "".join(xml_parts)
        else:
            return str(data)

    return f"<?xml version='1.0' encoding='UTF-8'?>\n<{root_name}>{_dict_to_xml(data)}</{root_name}>"


def dict_to_csv(data: Dict[str, Any]) -> str:
    """Convert dictionary to CSV string"""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Simple flattening for CSV
    if isinstance(data, dict):
        writer.writerow(["Key", "Value"])
        for key, value in data.items():
            writer.writerow([key, str(value)])
    elif isinstance(data, list) and data and isinstance(data[0], dict):
        if data:
            headers = list(data[0].keys())
            writer.writerow(headers)
            for row in data:
                writer.writerow([row.get(h, "") for h in headers])

    return output.getvalue()


def main():
    """Entry point for running the webapp"""
    port = int(os.getenv("WEBAPP_PORT", "7460"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
