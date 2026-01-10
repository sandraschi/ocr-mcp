import logging
logger = logging.getLogger(__name__)
#!/usr/bin/env python3
"""
Test import of OCR-MCP to check for syntax errors.
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    logger.info("Testing OCR-MCP import...")
    from ocr_mcp.server import app
    logger.info("SUCCESS: Import successful")

    import asyncio
    asynasync def test():
        tools = await app.get_tools()
        logger.info(f"SUCCESS: Got {len(tools)} tools")
        return tools

    tools = asyncio.run(test())
    logger.info(f"Tools: {[str(t) for t in tools]}")

except Exception as e:
    logger.info(f"ERROR: Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
