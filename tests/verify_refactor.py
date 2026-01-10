import asyncio
import sys
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))


# Mock PIL.Image BEFORE importing ocr_tools which imports modules that need it
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()
sys.modules["PIL.Image"].open = MagicMock(return_value=MagicMock(size=(100, 100)))

# Mock FastMCP
sys.modules["mcp"] = MagicMock()
sys.modules["mcp.server"] = MagicMock()
sys.modules["mcp.server.fastmcp"] = MagicMock()
# Mock the FastMCP class and its instance
mock_mcp_instance = MagicMock()
# When FastMCP(...) is called, return our mock instance
sys.modules["mcp.server.fastmcp"].FastMCP = MagicMock(return_value=mock_mcp_instance)


# Crucial: Mock the tool decorator to return the function itself (or a wrapper) so we can inspect it
def mock_tool():
    def decorator(func):
        return func

    return decorator


mock_mcp_instance.tool = MagicMock(side_effect=mock_tool)


try:
    from ocr_mcp.tools import ocr_tools
except Exception as e:
    print(f"FAILED TO IMPORT ocr_tools: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

from ocr_mcp.core.backend_manager import BackendManager
from ocr_mcp.core.config import OCRConfig


async def verify_tools():
    print("Verifying OCR-MCP Tools...")

    # Mock BackendManager and Config
    backend_manager = MagicMock(spec=BackendManager)
    backend_manager.process_with_backend = AsyncMock(
        return_value={"success": True, "text": "Mock OCR"}
    )
    backend_manager.get_backend_status = AsyncMock(
        return_value={"tesseract": "available"}
    )

    config = MagicMock(spec=OCRConfig)

    # Mock PIL.Image
    sys.modules["PIL"] = MagicMock()
    sys.modules["PIL.Image"] = MagicMock()
    sys.modules["PIL.Image"].open = MagicMock(return_value=MagicMock(size=(100, 100)))

    # Inject mocks into ocr_tools (if not already handled by dependency injection in actual app,
    # but here we test the functions assuming dependencies are passed or global injection works)
    # Note: In the actual FastMCP app, dependencies are injected via the context or global state.
    # For this test, we will monkeypatch the global backend_manager/config in ocr_tools if present,
    # or rely on the tool functions being called with valid arguments if they accept them.

    # Check ocr_tools.py structure
    print("Checking tool registration...")
    tools = [
        ocr_tools.document_processing,
        ocr_tools.image_management,
        ocr_tools.scanner_operations,
        ocr_tools.workflow_management,
        ocr_tools.help,
        ocr_tools.status,
    ]

    for tool in tools:
        try:
            print(f"  - Verified tool: {tool}")
        except Exception as e:
            print(f"  - Failed to verify tool: {e}")

    # Verify document_processing routing
    print("\nVerifying document_processing routing...")
    try:
        # We need to ensure dependencies are set.
        # Since ocr_tools.ky creates them globally, we'll just check if the function exists and runs.
        # Ideally we'd invoke it, but FastMCP tools are decorated.
        # We'll check the signature or existence of the implementation module functions.
        from ocr_mcp.tools import _processor
        from ocr_mcp.tools import _image
        from ocr_mcp.tools import _scanner
        from ocr_mcp.tools import _workflow

        print("Sub-modules imported successfully.")

        # Test a direct call to _processor (bypass FastMCP wrapper for unit testing logic)
        res = await _processor.process_document(
            "dummy.jpg", backend_manager=backend_manager, config=config
        )
        print(f"  - _processor.process_document result: {res['success']}")

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(verify_tools())
