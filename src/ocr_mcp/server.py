"""
OCR-MCP Server: Revolutionary Document Understanding Server (FastMCP 3.1).

Features:
- Sampling: sampling_handler for ctx.sample()/sample_step(); agentic_document_workflow uses sample_step with tools (SEP-1577).
- Prompts: process-instructions, quality-assessment-guide, scanner-workflow, batch-processing-guide, agentic-workflow-instructions.
- Resources: logs, capabilities (backends + 3.1 features), skills (LLM-oriented skills reference).
- Agentic workflow tool: AI-orchestrated multi-step document processing via sampling with tools.
"""

import asyncio
import logging
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
    """Server lifespan for startup and cleanup with FastMCP 3.1."""
    # ========== STARTUP ==========
    logger.info("OCR-MCP server starting up...")

    try:
        # Initialize backend manager (this may take time for model downloads)
        _runtime["backend_manager"] = BackendManager(config)
        bm = _runtime["backend_manager"]

        # Update sampling handler with backend manager
        global sampling_handler
        sampling_handler.backend_manager = bm
        sampling_handler.config = config

        # Cache backend information
        available_backends = bm.get_available_backends()
        logger.info("OCR-MCP initialized with backends: %s", available_backends)

        yield  # Server runs here

    except Exception as e:
        logger.error("Failed to initialize OCR backends: %s", e)
        raise

    # ========== SHUTDOWN ==========
    logger.info("OCR-MCP server shutting down...")
    logger.info("OCR-MCP shutdown complete")


# Initialize OCR Sampling Handler (will be updated in lifespan)
sampling_handler = OCRSamplingHandler()

# Initialize FastMCP server with 3.1
app = FastMCP(
    name="ocr-mcp",
    instructions="""You are OCR-MCP, a revolutionary document understanding server providing state-of-the-art OCR capabilities with FastMCP 3.1 conversational features and AI-powered sampling integration.

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

CONVERSATIONAL FEATURES (FastMCP 3.1):
- Progressive disclosure: Multi-level detail with recommendations and next steps
- Interactive clarification: Intelligent parameter collection and validation
- Rich metadata: Pagination, search metadata, refinement suggestions
- Error recovery: Contextual error handling with recovery options
- Persistent state: Cross-session memory and user preferences

SAMPLING INTEGRATION (FastMCP 3.1):
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
    lifespan=server_lifespan,  # FastMCP 3.1 lifespan management
    sampling_handler=sampling_handler,  # AI sampling integration
    sampling_handler_behavior="always",  # Always use sampling when available
    strict_input_validation=True,  # Production safety
    tasks=False,  # Background task support (disabled for compatibility)
    on_duplicate="replace",  # FastMCP 3.x: single policy for tools/resources/prompts
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


@app.resource("resource://ocr/capabilities")
def get_ocr_capabilities() -> str:
    """List available OCR backends and server capabilities (FastMCP 3.1)."""
    backends = []
    if _runtime.get("backend_manager"):
        try:
            backends = _runtime["backend_manager"].get_available_backends()
        except Exception:
            pass
    if not backends:
        backends = [
            "deepseek-ocr", "deepseek-ocr2", "paddleocr-vl", "olmocr-2", "pp-ocrv5",
            "dots-ocr", "got-ocr", "qwen-layered", "tesseract", "easyocr", "auto",
        ]
    return (
        "OCR-MCP 3.1 capabilities:\n"
        "- Tools: document_processing, image_management, scanner_operations, "
        "workflow_management, agentic_document_workflow\n"
        "- Sampling: ctx.sample() / ctx.sample_step() for agentic workflows (SEP-1577)\n"
        "- Prompts: process-instructions, quality-assessment-guide, scanner-workflow, "
        "batch-processing-guide, agentic-workflow-instructions\n"
        f"- Available backends (when server running): {', '.join(backends)}\n"
        "- Resources: logs, capabilities, skills"
    )


@app.resource("resource://ocr/skills")
def get_ocr_skills() -> str:
    """OCR-MCP skills reference for LLMs (FastMCP 3.1)."""
    return """# OCR-MCP Skills (FastMCP 3.1)

## Document processing
- **process_document**: Run OCR on a file (PDF, image, CBZ). Use backend "auto" for best-fit or name a backend.
- **analyze_layout**: Detect structure (tables, sections, forms).
- **assess_quality**: Validate OCR output and confidence.

## Image management
- **preprocess**: Deskew, enhance, rotate, crop.
- **convert**: Convert between image formats and PDF.

## Scanner operations (Windows WIA)
- **list_scanners**: Discover connected scanners.
- **scanner_properties** / **configure_scan**: Get/set DPI, color mode, paper size.
- **scan_document**: Acquire from flatbed.

## Workflow management
- **process_batch_intelligent**: Batch process a folder with auto backend selection.
- **create_processing_pipeline**: Define and run custom pipelines.

## Agentic workflow (SEP-1577, sampling with tools)
- **agentic_document_workflow**: Give a natural-language workflow prompt and a list of tool names; the LLM uses ctx.sample_step() to call tools until the workflow is done.
- Recommended tools to pass: document_processing, image_management, scanner_operations, workflow_management.
- Use for: "Scan and OCR the next page", "Process this folder and summarize", "Preprocess then run OCR with quality check".
"""


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


@app.prompt("prompt://ocr/quality-assessment-guide")
def get_quality_assessment_guide_prompt() -> str:
    """Prompt for OCR quality evaluation workflow."""
    return """Guide the user through OCR quality assessment using the ocr-mcp server.
1. Use document_processing(operation="process_document", ...) to get OCR output.
2. Use document_processing(operation="assess_quality", ...) to validate confidence and suggest improvements.
3. Optionally compare backends by running process_document with different backend values and assess_quality on each.
4. Recommend preprocessing (image_management(operation="preprocess")) if quality is low (e.g. deskew, enhance)."""


@app.prompt("prompt://ocr/scanner-workflow")
def get_scanner_workflow_prompt() -> str:
    """Prompt for scanner-based capture and OCR workflow."""
    return """Guide the user through scanning and OCR with ocr-mcp (Windows WIA).
1. Call scanner_operations(operation="list_scanners") to discover devices.
2. Use scanner_operations(operation="scanner_properties", device_id="...") to check DPI and capabilities.
3. Use scanner_operations(operation="scan_document", device_id="...", ...) to acquire an image.
4. Then use document_processing(operation="process_document", source_path=<path to saved scan>) to run OCR, or workflow_management for batch scan+OCR."""


@app.prompt("prompt://ocr/batch-processing-guide")
def get_batch_processing_guide_prompt() -> str:
    """Prompt for batch document processing."""
    return """Guide the user through batch document processing with ocr-mcp.
1. Use workflow_management(operation="process_batch_intelligent", source_dir="...") to process a folder with automatic backend selection and quality handling.
2. Or use workflow_management(operation="create_processing_pipeline", ...) to define a custom pipeline and run it on multiple files.
3. For scan-and-OCR batches, combine scanner_operations(operation="scan_document") (or a scan loop) with process_batch_intelligent on the output folder."""


@app.prompt("prompt://ocr/agentic-workflow-instructions")
def get_agentic_workflow_instructions_prompt() -> str:
    """Prompt for using the agentic document workflow (FastMCP 3.1 sampling with tools)."""
    return """Explain how to use the agentic_document_workflow tool (SEP-1577, FastMCP 3.1).
1. The user provides a workflow_prompt (natural language) and available_tools (e.g. ["document_processing", "image_management", "scanner_operations", "workflow_management"]).
2. The server uses ctx.sample_step() in a loop: the LLM chooses tool calls, tools run, results are fed back until the LLM returns a final answer or max_iterations is reached.
3. Example: agentic_document_workflow(workflow_prompt="Scan the next page and run OCR, then summarize in one paragraph", available_tools=["scanner_operations", "document_processing"], max_iterations=5).
4. Best for: multi-step document tasks without the client orchestrating each step."""


# Global instances - mutable runtime for lifespan injection
config = OCRConfig()
_runtime = {"backend_manager": None, "config": config}

# Register all tools - runtime dict is mutated in lifespan
register_sota_tools(app, _runtime, config)

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
    """Run the server with background services using FastMCP 3.1 lifespan."""
    # The lifespan manager handles initialization and cleanup
    # Background services are managed through the lifespan context

    try:
        # Use FastMCP 3.1 stdio async method
        await app.run_stdio_async()
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


def main():
    """Main entry point with unified transport handling (FastMCP 3.1)."""
    from .transport import run_server

    logger.info("Starting OCR-MCP server (FastMCP 3.1)...")
    run_server(app, server_name="ocr-mcp")


if __name__ == "__main__":
    main()
