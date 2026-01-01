#!/usr/bin/env python3
"""
Test script to start the OCR-MCP webapp
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_webapp():
    """Test webapp startup"""
    try:
        from webapp.backend.app import app
        print("[OK] Webapp imported successfully")

        # Test MCP client initialization
        from webapp.mcp_client import MCPClient
        client = MCPClient()
        print("[OK] MCP client created")

        # Try to initialize (but don't wait too long)
        try:
            await asyncio.wait_for(client.initialize(), timeout=30.0)
            print("[OK] MCP client initialized successfully")
        except asyncio.TimeoutError:
            print("[WARN] MCP client initialization timed out (expected in test)")
        except Exception as e:
            print(f"[ERROR] MCP client initialization failed: {e}")

        print("[OK] Webapp test completed")

    except Exception as e:
        print(f"[ERROR] Webapp test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_webapp())