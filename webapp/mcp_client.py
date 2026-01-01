"""
MCP Client for OCR-MCP WebApp
Communicates with the OCR-MCP server via stdio protocol
"""

import asyncio
import json
import os
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
        logger.info("MCPClient.initialize() method called")
        try:
            # Start the MCP server process
            python_path = sys.executable
            project_root = Path(__file__).parent.parent

            env = {
                **os.environ,
                "PYTHONPATH": str(project_root / "src"),
                "PYTHONUNBUFFERED": "1"
            }

            logger.info(f"Starting MCP server subprocess with command: {python_path} -m src.ocr_mcp.server")
            logger.info(f"Working directory: {project_root}")
            logger.info(f"Python executable: {python_path}")

            self.process = subprocess.Popen(
                [python_path, "-m", "src.ocr_mcp.server"],
                cwd=str(project_root),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,  # Redirect stderr to avoid interference
                text=True,
                env=env,
                bufsize=0  # Unbuffered
            )

            logger.info(f"MCP server subprocess started with PID: {self.process.pid}")

            # Check if process is still alive
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                logger.error(f"MCP server subprocess exited immediately with code {self.process.returncode}")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                raise Exception(f"MCP server subprocess failed to start: {stderr}")

            # Start reading responses in background
            threading.Thread(target=self._read_responses, daemon=True).start()

            # Wait for server to be ready (longer timeout)
            logger.info("Waiting 10 seconds for MCP server to initialize...")
            await asyncio.sleep(10)
            logger.info("Finished waiting for MCP server initialization")

            # Initialize MCP protocol connection directly
            logger.info("Initializing MCP protocol connection...")
            try:
                await self._initialize_connection()
                self.connected = True
                logger.info("MCP client connected successfully")
            except Exception as e:
                logger.error(f"MCP protocol initialization failed: {e}")
                raise

        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")
            # Try to get subprocess stderr if available
            if self.process and self.process.stderr:
                try:
                    stderr_output = self.process.stderr.read()
                    if stderr_output:
                        logger.error(f"MCP server stderr: {stderr_output}")
                except:
                    pass
            raise

    async def _initialize_connection(self):
        """Initialize MCP protocol connection with retry logic"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
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
                logger.info("MCP protocol initialized successfully")
                return result

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"MCP initialization attempt {attempt + 1} failed: {e}, retrying...")
                    await asyncio.sleep(2)
                else:
                    logger.error(f"MCP initialization failed after {max_retries} attempts: {e}")
                    raise

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
        logger.info(f"Sending request to MCP server: {request_json.strip()}")
        self.process.stdin.write(request_json)
        self.process.stdin.flush()
        logger.info("Request sent to MCP server")

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
            logger.info("Starting to read MCP server responses...")
            buffer = ""
            while True:
                char = self.process.stdout.read(1)
                if not char:
                    break
                buffer += char
                if char == '\n':
                    line_stripped = buffer.strip()
                    buffer = ""
                    if not line_stripped:
                        continue

                    logger.debug(f"Received line from MCP server: {line_stripped}")

                    # Skip non-JSON lines (log messages, etc.)
                    if not line_stripped.startswith('{'):
                        logger.debug(f"Skipping non-JSON line: {line_stripped}")
                        continue

                    try:
                        response = json.loads(line_stripped)
                        logger.info(f"Parsed MCP response: {response}")

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
                            else:
                                logger.warning(f"No future found for request ID: {request_id}")
                        else:
                            logger.warning(f"Response without ID: {response}")

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse MCP response: {e}, line: {line_stripped}")
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
