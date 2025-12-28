"""
OCR-MCP Server: Revolutionary Document Understanding Server
"""

import logging

from fastmcp import FastMCP

from .core.config import OCRConfig
from .core.backend_manager import BackendManager
from .tools.ocr_tools import register_ocr_tools
from .tools.scanner_tools import register_scanner_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
app = FastMCP(
    name="ocr-mcp",
    instructions="""You are OCR-MCP, a revolutionary document understanding server providing state-of-the-art OCR capabilities.

CORE CAPABILITIES:
- Multiple OCR backends: DeepSeek-OCR, Florence-2, PP-OCRv5, DOTS.OCR, GOT-OCR, Tesseract
- Document processing: PDF, CBZ/CBR archives, images (PNG, JPG, TIFF, BMP)
- Scanner integration: Direct WIA control for Windows flatbed scanners
- Batch processing: Concurrent processing of multiple documents
- Output formats: Text, HTML, Markdown, JSON, XML

USAGE PATTERNS:
1. Document OCR: process_document() - Auto-selects best backend
2. Scanner control: list_scanners(), scan_document() - Hardware integration
3. Batch processing: process_batch_documents() - Concurrent operations
4. Image analysis: extract_regions() - Fine-grained text extraction

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

# Register tools
register_ocr_tools(app, backend_manager, config)
register_scanner_tools(app, backend_manager, config)


def main():
    """Main entry point for OCR-MCP server."""
    logger.info("Starting OCR-MCP server...")
    logger.info(f"Available backends: {backend_manager.get_available_backends()}")

    # Start the MCP server
    import asyncio
    asyncio.run(app.run_stdio_async())


if __name__ == "__main__":
    main()
