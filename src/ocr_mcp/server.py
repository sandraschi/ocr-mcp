# MIT License
#
# Copyright (c) 2025 OCR-MCP Project
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
#
#
#
#

"""
OCR-MCP Server: Revolutionary Document Understanding Server (FastMCP 3.1).

Features:
- Sampling: sampling_handler for ctx.sample()/sample_step(); agentic_document_workflow uses sample_step with tools (SEP-1577).
- Prompts: process-instructions, quality-assessment-guide, scanner-workflow, batch-processing-guide, agentic-workflow-instructions.
- Resources: logs, capabilities (backends + 3.1 features), skills (LLM-oriented skills reference).
- Agentic workflow tool: AI-orchestrated multi-step document processing via sampling with tools.
"""

import logging
import os
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

# Local-first: always use server sampling (Ollama/OpenAI-compatible on localhost/LAN).
# Set OCR_SAMPLING_USE_CLIENT_LLM=1 to prefer the MCP host LLM when it supports sampling.
_USE_CLIENT_SAMPLING = os.getenv("OCR_SAMPLING_USE_CLIENT_LLM", "").lower() in (
    "1",
    "true",
    "yes",
)


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
    instructions="""OCR-MCP: High-fidelity document understanding and hardware control plane.

CORE CAPABILITIES:
- OCR Engines: DeepSeek-OCR, PaddleOCR-VL, PP-OCRv5, Mistral OCR, GOT-OCR, Tesseract, EasyOCR.
- Formats: PDF, CBZ/CBR, PNG, JPG, TIFF, WebP.
- Hardware: Direct WIA scanner control (Windows).
- Analysis: Layout parsing, table extraction, form detection, accuracy validation.
- Agentic: Autonomous multi-step orchestration via sampling (SEP-1577).

OPERATIONAL TOOLS:
- process_document: Primary OCR, layout analysis, and metadata extraction.
- manage_image: Preprocessing (deskew/denoise), format conversion, PDF layering.
- operate_scanner: Hardware acquisition and device configuration.
- manage_workflow: Batch processing and system health monitoring.
- manage_corpus: SQLite document indexing and full-text search.
- execute_agentic_workflow: Goal-oriented autonomous orchestration.

Always provide technical, actionable responses including confidence scores and recovery paths.""",
    lifespan=server_lifespan,  # FastMCP 3.1 lifespan management
    sampling_handler=sampling_handler,  # Default: local Ollama / OpenAI-compatible HTTP
    sampling_handler_behavior="fallback" if _USE_CLIENT_SAMPLING else "always",
    strict_input_validation=True,  # Production safety
    tasks=False,  # Background task support (disabled for compatibility)
    on_duplicate="replace",  # FastMCP 3.x: single policy for tools/resources/prompts
)


# Resources
@app.resource("resource://ocr/logs")
def get_ocr_logs() -> str:
    """Retrieves current processing logs for diagnostics."""
    try:
        log_path = Path("ocr_processing.log")
        if log_path.exists():
            return log_path.read_text()
        return "No OCR logs found."
    except Exception as e:
        return f"Error reading logs: {e}"


@app.resource("resource://ocr/capabilities")
def get_ocr_capabilities() -> str:
    """Lists available OCR backends and supported FastMCP features."""
    backends = []
    if _runtime.get("backend_manager"):
        try:
            backends = _runtime["backend_manager"].get_available_backends()
        except Exception:
            pass
    if not backends:
        backends = ["deepseek-ocr", "paddleocr-vl", "pp-ocrv5", "tesseract", "easyocr"]

    return (
        "OCR-MCP Capabilities:\n"
        "- Tools: process_document, manage_image, operate_scanner, manage_workflow, manage_corpus, execute_agentic_workflow\n"
        "- Features: SEP-1577 Sampling, Pydantic Structured Output, WIA Hardware Control\n"
        f"- Active Backends: {', '.join(backends)}"
    )


@app.resource("resource://ocr/skills")
def get_ocr_skills() -> str:
    """Standardized skills library for LLM orchestration."""
    return """# OCR-MCP Operational Skills

## 1. Document Extraction
- Use `process_document(operation='process_document')` for high-fidelity OCR.
- Use `process_document(operation='extract_tables')` for structured data recovery.
- If quality is low, run `manage_image(operation='preprocess')` first.

## 2. Hardware Acquisition
- Enumerate devices with `operate_scanner(operation='list_scanners')`.
- Acquire pages using `operate_scanner(operation='scan_document')`.

## 3. Autonomous Orchestration
- Use `execute_agentic_workflow` for multi-step goals like "Find the scanner, scan 5 pages, and extract all invoice totals."
"""


# Prompts
@app.prompt("prompt://ocr/process-instructions")
def get_process_instructions_prompt() -> str:
    """Guide for configuring document processing tasks."""
    return """Assist the user in defining a document processing task.
Collect:
1. Source path (local file://).
2. Backend (deepseek-ocr for complexity, paddleocr-vl for tables).
3. Operation (OCR, Layout, or Metadata).

Construct a `process_document` call based on these inputs."""


@app.prompt("prompt://ocr/quality-assessment-guide")
def get_quality_assessment_guide_prompt() -> str:
    """Workflow for evaluating and improving extraction quality."""
    return """1. Run `process_document(operation='process_document')`.
2. Evaluate with `process_document(operation='assess_quality')`.
3. If scores are low, apply `manage_image(operation='preprocess', deskew=True, denoise=True)`.
4. Re-run OCR and compare."""


@app.prompt("prompt://ocr/scanner-workflow")
def get_scanner_workflow_prompt() -> str:
    """Workflow for hardware-to-OCR pipelines."""
    return """1. Locate hardware: `operate_scanner(operation='list_scanners')`.
2. Configure: `operate_scanner(operation='configure_scan')`.
3. Acquire: `operate_scanner(operation='scan_document')`.
4. Extract: `process_document(operation='process_document', source_path=<scan_path>)`."""


@app.prompt("prompt://ocr/batch-processing-guide")
def get_batch_processing_guide_prompt() -> str:
    """Instructions for high-volume document batching."""
    return """Use `manage_workflow(operation='process_batch_intelligent')` for automated directory processing.
For custom logic, use `manage_workflow(operation='create_processing_pipeline')` to chain operations."""


@app.prompt("prompt://ocr/agentic-workflow-instructions")
def get_agentic_workflow_instructions_prompt() -> str:
    """Detailed guide for SEP-1577 autonomous execution."""
    return """Explain `execute_agentic_workflow` (SEP-1577):
- Provide a clear natural language goal (workflow_prompt).
- Pass relevant tool names in `available_tools`.
- The agent will autonomously loop, calling tools and analyzing results until the goal is achieved."""


# Global instances - mutable runtime for lifespan injection
config = OCRConfig()
try:
    from .utils.startup_bootstrap import run_ocr_startup_bootstrap

    run_ocr_startup_bootstrap(config)
except Exception as e:
    logger.warning("OCR startup bootstrap: %s", e)

_runtime = {"backend_manager": None, "config": config}

# Register all tools - runtime dict is mutated in lifespan
register_sota_tools(app, _runtime, config)

# Register SEP-1577 agentic document workflow tool
try:
    from .tools.agentic_document_workflow import register_agentic_document_workflow

    register_agentic_document_workflow(app)
    logger.info("SEP-1577 executive workflow tool registered")
except ImportError as e:
    logger.warning(f"SEP-1577 executive workflow tool not available: {e}")
except Exception as e:
    logger.error(f"Failed to register executive workflow tool: {e}")


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
