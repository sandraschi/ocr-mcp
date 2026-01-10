"""
OCR-MCP Server: Revolutionary Document Understanding Server
"""

import logging
import asyncio
from pathlib import Path

from fastmcp import FastMCP

from .core.config import OCRConfig
from .core.backend_manager import BackendManager
from .tools.ocr_tools import register_sota_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
app = FastMCP(
    name="ocr-mcp",
    instructions="""You are OCR-MCP, a revolutionary document understanding server providing state-of-the-art OCR capabilities.

CORE CAPABILITIES:
- Multiple OCR backends: DeepSeek-OCR, Florence-2, PP-OCRv5, DOTS.OCR, GOT-OCR, Tesseract, EasyOCR
- Document processing: PDF, CBZ/CBR archives, images (PNG, JPG, TIFF, BMP, WebP)
- Scanner integration: Direct WIA control for Windows flatbed scanners
- Image preprocessing: Deskew, enhance, rotate, crop, quality pipeline
- Document analysis: Layout detection, table extraction, form analysis, structure parsing
- Quality assessment: OCR accuracy validation, confidence scoring, backend comparison
- Format conversion: PDF↔images, searchable PDFs, format optimization
- Intelligent workflows: Auto-routing, quality gates, batch processing, pipeline orchestration
- Output formats: Text, HTML, Markdown, JSON, XML

PORTMANTEAU TOOLS:
- document_processing: OCR, analysis, quality assessment operations
- image_management: Image preprocessing and conversion operations
- scanner_operations: Scanner hardware control operations
- workflow_management: Batch processing, pipelines, system operations

USAGE PATTERNS:
1. Document OCR: document_processing(operation="process_document") - Auto-selects best backend
2. Scanner control: scanner_operations(operation="list_scanners") - Hardware integration
3. Image preprocessing: image_management(operation="preprocess") - Quality optimization
4. Document analysis: document_processing(operation="analyze_layout") - Structure understanding
5. Quality assessment: document_processing(operation="assess_quality") - Accuracy validation
6. Batch workflows: workflow_management(operation="process_batch_intelligent") - Automated processing
7. Custom pipelines: workflow_management(operation="create_processing_pipeline") - Workflow orchestration

BACKEND SELECTION:
- DeepSeek-OCR: Best for complex documents, mathematical formulas
- Florence-2: Microsoft vision model, excellent layout understanding
- PP-OCRv5: Industrial-grade OCR, fast and reliable
- Tesseract: Classic OCR, good fallback option

Always provide clear, actionable results with confidence scores and processing details.""",
)


# Resources
@app.resource("resource://ocr/logs")
def get_ocr_logs() -> str:
    """Get the latest OCR processing logs"""
    try:
        log_path = Path("ocr_processing.log")
        if log_path.exists():
            return log_path.read_text()
        return "No OCR logs found."
    except Exception as e:
        return f"Error reading logs: {e}"


# Prompts
@app.prompt("prompt://ocr/process-instructions")
def get_process_instructions_prompt() -> str:
    """Prompt for helping users construct OCR processing instructions"""
    return """You are helping a user construct OCR processing instructions for the ocr-mcp server.
The user wants to process a document. Ask them for:
1. The path to the document (file://...)
2. The preferred backend (auto, deepseek-ocr, florence-2, etc.)
3. Any specific regions of interest [x1, y1, x2, y2]
4. Whether they need format conversion (e.g., to searchable PDF)

Then, help them call the `document_processing` tool with the appropriate `operation="process_document"`."""


# Global instances
config = OCRConfig()
backend_manager = BackendManager(config)

# Register all tools using SOTA registration
# Register all tools using SOTA registration
register_sota_tools(app, backend_manager, config)


async def run_server():
    """Run the server with background services."""
    from .services.watch_folder import WatchFolderService

    # Initialize and start watch folder service
    watch_service = WatchFolderService(backend_manager)
    # We can't await start() directly as it runs forever, so just start the task
    # The start method manages its own loop
    watch_task = asyncio.create_task(watch_service.start())

    try:
        await app.run_stdio_async()
    finally:
        watch_service.stop()
        try:
            # Give it a moment to stop gracefully
            await asyncio.wait_for(watch_task, timeout=2.0)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass


def main():
    """Main entry point for OCR-MCP server."""
    logger.info("Starting OCR-MCP server...")
    logger.info(f"Available backends: {backend_manager.get_available_backends()}")

    # Start the MCP server
    import asyncio

    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")


if __name__ == "__main__":
    main()
