"""
OCR-MCP Server: Revolutionary Document Understanding Server
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastmcp import FastMCP

from .core.backend_manager import BackendManager
from .core.config import OCRConfig
from .sampling.ocr_sampling_handler import OCRSamplingHandler
from .tools.ocr_tools import register_sota_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def server_lifespan(mcp_instance: FastMCP):
    """Server lifespan for startup and cleanup with FastMCP 2.14.3 features."""
    # ========== STARTUP ==========
    logger.info("OCR-MCP server starting up...")

    # Initialize persistent storage
    await mcp_instance.storage.set("server_started_at", time.time())
    await mcp_instance.storage.set("server_version", "2.14.3")

    # Load previous state if available
    last_backend_state = await mcp_instance.storage.get("backend_state")
    if last_backend_state:
        logger.info("Restored backend state from previous session", state=last_backend_state)

    # Initialize OCR backends and cache
    await mcp_instance.storage.set("backends_initialized", False)
    await mcp_instance.storage.set("processing_stats", {"total_processed": 0, "total_errors": 0})

    # Set initial server status
    await mcp_instance.storage.set("server_status", "initializing")

    try:
        # Initialize backend manager (this may take time for model downloads)
        global backend_manager
        backend_manager = BackendManager(config)

        # Update sampling handler with backend manager
        global sampling_handler
        sampling_handler.backend_manager = backend_manager
        sampling_handler.config = config

        # Cache backend information
        available_backends = backend_manager.get_available_backends()
        await mcp_instance.storage.set("available_backends", available_backends)
        await mcp_instance.storage.set("backends_initialized", True)
        await mcp_instance.storage.set("server_status", "ready")

        logger.info(f"OCR-MCP initialized with backends: {available_backends}")

        yield  # Server runs here

    except Exception as e:
        logger.error(f"Failed to initialize OCR backends: {e}")
        await mcp_instance.storage.set("server_status", "error")
        await mcp_instance.storage.set("initialization_error", str(e))
        raise

    # ========== SHUTDOWN ==========
    logger.info("OCR-MCP server shutting down...")

    # Save final state
    await mcp_instance.storage.set("last_shutdown", time.time())
    final_stats = await mcp_instance.storage.get("processing_stats")
    await mcp_instance.storage.set("final_processing_stats", final_stats)
    await mcp_instance.storage.set("server_status", "shutdown")

    # Clean up resources
    if "backend_manager" in globals():
        # Add cleanup logic for backend manager if needed
        pass

    logger.info("OCR-MCP shutdown complete")


# Initialize OCR Sampling Handler (will be updated in lifespan)
sampling_handler = OCRSamplingHandler()

# Initialize FastMCP server with 2.14.3 features
app = FastMCP(
    name="ocr-mcp",
    instructions="""You are OCR-MCP, a revolutionary document understanding server providing state-of-the-art OCR capabilities with FastMCP 2.14.3 conversational features and AI-powered sampling integration.

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

CONVERSATIONAL FEATURES (FastMCP 2.14.3):
- Progressive disclosure: Multi-level detail with recommendations and next steps
- Interactive clarification: Intelligent parameter collection and validation
- Rich metadata: Pagination, search metadata, refinement suggestions
- Error recovery: Contextual error handling with recovery options
- Persistent state: Cross-session memory and user preferences

SAMPLING INTEGRATION (FastMCP 2.14.3):
- AI-powered document analysis and processing decisions
- Autonomous OCR backend selection based on document characteristics
- Intelligent workflow orchestration without client round-trips
- Quality assessment and error recovery strategies
- SEP-1577 compliant agentic document processing

PORTMANTEAU TOOLS:
- document_processing: OCR, analysis, quality assessment operations
- image_management: Image preprocessing and conversion operations
- scanner_operations: Scanner hardware control operations
- workflow_management: Batch processing, pipelines, system operations
- agentic_document_workflow: AI-orchestrated multi-document processing (SEP-1577)

USAGE PATTERNS:
1. Document OCR: document_processing(operation="process_document") - Auto-selects best backend
2. Scanner control: scanner_operations(operation="list_scanners") - Hardware integration
3. Image preprocessing: image_management(operation="preprocess") - Quality optimization
4. Document analysis: document_processing(operation="analyze_layout") - Structure understanding
5. Quality assessment: document_processing(operation="assess_quality") - Accuracy validation
6. Batch workflows: workflow_management(operation="process_batch_intelligent") - Automated processing
7. Custom pipelines: workflow_management(operation="create_processing_pipeline") - Workflow orchestration
8. Agentic processing: agentic_document_workflow(operation="process_batch_intelligent") - AI-orchestrated workflows

BACKEND SELECTION:
- DeepSeek-OCR: Best for complex documents, mathematical formulas
- Florence-2: Microsoft vision model, excellent layout understanding
- PP-OCRv5: Industrial-grade OCR, fast and reliable
- Tesseract: Classic OCR, good fallback option

Always provide conversational responses with actionable recommendations, confidence scores, and next steps.""",
    lifespan=server_lifespan,  # FastMCP 2.14.3 lifespan management
    sampling_handler=sampling_handler,  # AI sampling integration
    sampling_handler_behavior="always",  # Always use sampling when available
    include_fastmcp_meta=True,  # Enhanced observability
    strict_input_validation=True,  # Production safety
    tasks=False,  # Background task support (disabled for compatibility)
    on_duplicate_tools="replace",  # Handle tool conflicts
    on_duplicate_resources="warn",  # Warn about duplicate resources
    on_duplicate_prompts="warn",  # Warn about duplicate prompts
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
backend_manager = None  # Will be initialized in lifespan

# Register all tools using SOTA registration
# Note: backend_manager will be None during registration, tools will access it dynamically
register_sota_tools(app, backend_manager, config)

# Register SEP-1577 agentic document workflow tool
try:
    from .tools.agentic_document_workflow import register_agentic_document_workflow

    register_agentic_document_workflow(app)
    logger.info("SEP-1577 agentic document workflow tool registered")
except ImportError as e:
    logger.warning(f"SEP-1577 agentic document workflow tool not available: {e}")
except Exception as e:
    logger.error(f"Failed to register SEP-1577 agentic document workflow tool: {e}")


async def run_server():
    """Run the server with background services using FastMCP 2.14.3 lifespan."""
    # The lifespan manager handles initialization and cleanup
    # Background services are managed through the lifespan context

    try:
        # Use the new FastMCP 2.14.3 stdio async method
        await app.run_stdio_async()
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


def main():
    """Main entry point for OCR-MCP server with FastMCP 2.14.3."""
    logger.info("Starting OCR-MCP server (FastMCP 2.14.3)...")

    # Server initialization is handled by the lifespan manager
    # The backend_manager will be available after lifespan startup

    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("OCR-MCP server stopped by user")
    except Exception as e:
        logger.error(f"OCR-MCP server failed: {e}")
        raise


if __name__ == "__main__":
    main()
