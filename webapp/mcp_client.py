"""
MCP Client for OCR-MCP WebApp
Communicates with the OCR-MCP server via stdio protocol
"""

import asyncio
import json
import sys
import subprocess
import threading
from typing import Dict, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class MCPClient:
    """Client for communicating with OCR-MCP server"""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.connected = False
        self._response_futures: Dict[str, asyncio.Future] = {}
        self._next_id = 1

    async def initialize(self):
        """Initialize connection to MCP server"""
        try:
            # Start the MCP server process
            server_path = Path(__file__).parent.parent / "src" / "ocr_mcp" / "__main__.py"
            python_path = sys.executable

            env = {
                **os.environ,
                "PYTHONPATH": str(Path(__file__).parent.parent / "src"),
                "PYTHONUNBUFFERED": "1"
            }

            self.process = subprocess.Popen(
                [python_path, str(server_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            # Start reading responses in background
            threading.Thread(target=self._read_responses, daemon=True).start()

            # Wait for server to be ready
            await asyncio.sleep(2)

            # Test connection
            await self._initialize_connection()
            self.connected = True
            logger.info("MCP client connected successfully")

        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")
            raise

    async def _initialize_connection(self):
        """Initialize MCP protocol connection"""
        # Send initialize request
        result = await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "ocr-mcp-webapp",
                "version": "0.1.0"
            }
        })

        # Send initialized notification
        await self._send_notification("notifications/initialized", {})

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool"""
        if not self.connected:
            raise Exception("MCP client not connected")

        return await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request"""
        if not self.process or not self.process.stdin:
            raise Exception("MCP process not available")

        request_id = self._next_id
        self._next_id += 1

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }

        # Create future for response
        future = asyncio.Future()
        self._response_futures[str(request_id)] = future

        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json)
        self.process.stdin.flush()

        # Wait for response
        try:
            result = await asyncio.wait_for(future, timeout=300.0)  # 5 minute timeout
            return result
        except asyncio.TimeoutError:
            raise Exception(f"Request timeout for method {method}")

    async def _send_notification(self, method: str, params: Dict[str, Any]):
        """Send a JSON-RPC notification"""
        if not self.process or not self.process.stdin:
            return

        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }

        notification_json = json.dumps(notification) + "\n"
        self.process.stdin.write(notification_json)
        self.process.stdin.flush()

    def _read_responses(self):
        """Read responses from MCP server in background thread"""
        if not self.process or not self.process.stdout:
            return

        try:
            for line in iter(self.process.stdout.readline, ''):
                if line.strip():
                    try:
                        response = json.loads(line.strip())

                        # Handle response
                        if "id" in response:
                            request_id = str(response["id"])
                            if request_id in self._response_futures:
                                future = self._response_futures.pop(request_id)
                                if "result" in response:
                                    future.set_result(response["result"])
                                elif "error" in response:
                                    future.set_exception(Exception(response["error"].get("message", "Unknown error")))
                                else:
                                    future.set_exception(Exception("Invalid response format"))

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse MCP response: {e}")
                    except Exception as e:
                        logger.error(f"Error processing MCP response: {e}")

        except Exception as e:
            logger.error(f"Error reading MCP responses: {e}")

    async def cleanup(self):
        """Cleanup resources"""
        if self.process:
            try:
                self.process.terminate()
                await asyncio.sleep(0.1)
                if self.process.poll() is None:
                    self.process.kill()
            except:
                pass
        self.connected = False
