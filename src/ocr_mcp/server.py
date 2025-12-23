"""
OCR-MCP Server: Revolutionary Document Understanding Server
"""

import logging
from pathlib import Path

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
    name="ocr-mcp"
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
