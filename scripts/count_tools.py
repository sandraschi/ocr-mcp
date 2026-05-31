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

import logging

logger = logging.getLogger(__name__)
#!/usr/bin/env python3
"""
Count and list registered MCP tools for OCR-MCP server.

This script imports the OCR-MCP server and counts all registered tools
without starting the actual MCP server.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from ocr_mcp.server import app

    async def count_tools():
        """Count and display registered tools."""
        try:
            # Get tools from the MCP app
            tools = await app.get_tools()
            tool_names = [tool if isinstance(tool, str) else str(tool) for tool in tools]

            logger.info(f"OCR-MCP Server - {len(tools)} tools registered:")
            logger.info("=" * 50)
            logger.info(f"All tools: {sorted(tool_names)}")
            logger.info()

            # Group tools by category
            ocr_tools = [t for t in tool_names if "ocr" in t.lower() or "process" in t.lower()]
            scanner_tools = [t for t in tool_names if "scan" in t.lower()]
            other_tools = [t for t in tool_names if t not in ocr_tools + scanner_tools]

            if ocr_tools:
                logger.info(f"OCR Tools ({len(ocr_tools)}):")
                for tool in sorted(ocr_tools):
                    logger.info(f"  - {tool}")
                logger.info()

            if scanner_tools:
                logger.info(f"Scanner Tools ({len(scanner_tools)}):")
                for tool in sorted(scanner_tools):
                    logger.info(f"  - {tool}")
                logger.info()

            if other_tools:
                logger.info(f"Other Tools ({len(other_tools)}):")
                for tool in sorted(other_tools):
                    logger.info(f"  - {tool}")

            logger.info(f"\nSUCCESS: Total {len(tools)} tools successfully registered")

        except Exception as e:
            logger.info(f"ERROR: Error counting tools: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    if __name__ == "__main__":
        asyncio.run(count_tools())

except ImportError as e:
    logger.info(f"ERROR: Import error: {e}")
    logger.info("Make sure you're running from the ocr-mcp directory and dependencies are installed.")
    sys.exit(1)
