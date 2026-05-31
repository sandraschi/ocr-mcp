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

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))


# Mock PIL and other heavy dependencies
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()
sys.modules["PIL.ExifTags"] = MagicMock()
sys.modules["fastmcp"] = MagicMock()
sys.modules["fastmcp.Context"] = MagicMock()


# Mock the tool decorator
def mock_tool(*args, **kwargs):
    def decorator(func):
        return func

    return decorator


mock_app = MagicMock()
mock_app.tool = MagicMock(side_effect=mock_tool)

try:
    from ocr_mcp.tools import ocr_tools
    from ocr_mcp.tools.models import ToolResponse

    print("SUCCESS: Imported ocr_tools and models.")
except Exception as e:
    print(f"FAILED TO IMPORT ocr_tools/models: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

from ocr_mcp.core.backend_manager import BackendManager
from ocr_mcp.core.config import OCRConfig


async def verify_tools():
    print("\n--- Verifying OCR-MCP SOTA v13.1 Refit ---")

    # Mock BackendManager and Config
    backend_manager = MagicMock(spec=BackendManager)
    backend_manager.process_with_backend = AsyncMock(return_value={"success": True, "text": "Mock OCR"})
    backend_manager.get_backend_status = AsyncMock(return_value={"tesseract": "available"})
    config = MagicMock(spec=OCRConfig)

    # Register tools with mock app
    ocr_tools.register_sota_tools(mock_app, backend_manager, config)

    # Check if tools were registered (mocked)
    print("Checking tool registration names...")

    # Map of old names to new names for verification
    expected_tools = [
        "process_document",
        "manage_image",
        "operate_scanner",
        "manage_workflow",
        "manage_corpus",
        "get_help",
        "get_status",
    ]

    # In our mock, since we decorated them, they are just functions in the module now
    # but the register_sota_tools function defines them locally.

    # Get all tool function names from mock_app.tool calls
    # Note: FastMCP tool() decorator might be called without args, in which case func name is used.
    # Our mock_tool decorator doesn't capture the func name automatically in call_args_list
    # unless we inspect the decorator's 'func' argument.

    # Let's adjust the mock to capture the functions themselves
    registered_funcs = [call.args[0].__name__ for call in mock_app.tool.return_value.call_args_list if call.args]

    # Actually, the way decorator is called in ocr_tools is:
    # @app.tool()
    # async def name(...):

    # So app.tool() -> decorator(func) -> func
    # The decorator is called with the function.

    # Let's check how many times the decorator was called
    print(f"App.tool() was called {len(mock_app.tool.call_args_list)} times.")

    # Since we returned the same 'decorator' function from mock_tool,
    # we can check what that decorator was called with.
    # But mock_app.tool is a MagicMock, its return_value is another MagicMock.

    # Let's define the decorator better to capture the function names
    found_tools = []

    def recording_decorator(func):
        found_tools.append(func.__name__)
        return func

    mock_app.tool.side_effect = lambda *a, **k: recording_decorator

    # Re-register
    ocr_tools.register_sota_tools(mock_app, backend_manager, config)

    print(f"Registered tools tracked: {found_tools}")

    for expected in expected_tools:
        if expected in found_tools:
            print(f"  [OK] {expected}")
        else:
            print(f"  [MISSING] {expected}")

    print("\nVerifying Tool Schema Consistency...")
    # Verify we can create a ToolResponse
    resp = ToolResponse(success=True, operation="test", summary="Verified")
    print(f"  - ToolResponse model functional: {resp.success}")

    print("\nVerifying Sub-module Integration...")
    try:
        from ocr_mcp.tools import _processor

        res = await _processor.process_document(source_path="dummy.jpg", backend_manager=backend_manager, config=config)
        print(f"  - _processor.process_document baseline check: {res.get('success')}")
    except Exception as e:
        print(f"  - Sub-module check failed: {e}")

    print("\n--- Verification Complete ---")


if __name__ == "__main__":
    asyncio.run(verify_tools())
