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

            print(f"OCR-MCP Server - {len(tools)} tools registered:")
            print("=" * 50)
            print(f"All tools: {sorted(tool_names)}")
            print()

            # Group tools by category
            ocr_tools = [t for t in tool_names if 'ocr' in t.lower() or 'process' in t.lower()]
            scanner_tools = [t for t in tool_names if 'scan' in t.lower()]
            other_tools = [t for t in tool_names if t not in ocr_tools + scanner_tools]

            if ocr_tools:
                print(f"OCR Tools ({len(ocr_tools)}):")
                for tool in sorted(ocr_tools):
                    print(f"  - {tool}")
                print()

            if scanner_tools:
                print(f"Scanner Tools ({len(scanner_tools)}):")
                for tool in sorted(scanner_tools):
                    print(f"  - {tool}")
                print()

            if other_tools:
                print(f"Other Tools ({len(other_tools)}):")
                for tool in sorted(other_tools):
                    print(f"  - {tool}")

            print(f"\nSUCCESS: Total {len(tools)} tools successfully registered")

        except Exception as e:
            print(f"ERROR: Error counting tools: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    if __name__ == "__main__":
        asyncio.run(count_tools())

except ImportError as e:
    print(f"ERROR: Import error: {e}")
    print("Make sure you're running from the ocr-mcp directory and dependencies are installed.")
    sys.exit(1)
