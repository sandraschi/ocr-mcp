"""
OCR-MCP Server: Revolutionary Document Understanding Server
"""

import logging

from fastmcp import FastMCP

from .core.config import OCRConfig
from .core.backend_manager import BackendManager
from .tools.ocr_tools import register_document_processing_tools
from .tools.image_tools import register_image_management_tools
from .tools.scanner_tools import register_scanner_operations_tools
from .tools.workflow_tools import register_workflow_management_tools

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

Always provide clear, actionable results with confidence scores and processing details."""
)

# Global instances
config = OCRConfig()
backend_manager = BackendManager(config)

# Register portmanteau tools (replacing individual tools for better discoverability)
register_document_processing_tools(app, backend_manager, config)
register_image_management_tools(app, backend_manager, config)
register_scanner_operations_tools(app, backend_manager, config)
register_workflow_management_tools(app, backend_manager, config)


def main():
    """Main entry point for OCR-MCP server."""
    logger.info("Starting OCR-MCP server...")
    logger.info(f"Available backends: {backend_manager.get_available_backends()}")

    # Start the MCP server
    import asyncio
    asyncio.run(app.run_stdio_async())


if __name__ == "__main__":
    main()
