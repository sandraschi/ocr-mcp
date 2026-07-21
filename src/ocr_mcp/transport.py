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

"""
FastMCP 3.1 Dual Transport Configuration

Standard module for all MCP servers in d:/Dev/repos.
Provides unified transport configuration for STDIO, HTTP Streamable, and legacy SSE modes.

Environment Variables:
    MCP_TRANSPORT: Transport mode (stdio, http, sse). Default: stdio
    MCP_HOST: Bind address for HTTP/SSE. Default: 127.0.0.1
    MCP_PORT: Port for HTTP/SSE. Default: 10859 (fleet 10700+; set MCP_PORT to override)
    MCP_PATH: HTTP endpoint path. Default: /mcp

CLI Arguments:
    --stdio: Run in STDIO mode (default, for Claude Desktop)
    --http: Run in HTTP Streamable mode
    --sse: Run in SSE mode (deprecated)
    --host: Bind address
    --port: Port number
    --path: HTTP endpoint path
    --debug: Enable debug logging

Usage:
    from .transport import run_server

    mcp = FastMCP("my-server", version="1.0.0")

    def main():
        run_server(mcp, server_name="my-server")
"""

import argparse
import asyncio
import logging
import os
from typing import Literal

logger = logging.getLogger(__name__)

TransportType = Literal["stdio", "http", "sse"]

# Environment variable standards
ENV_TRANSPORT = "MCP_TRANSPORT"  # stdio | http | sse
ENV_HOST = "MCP_HOST"  # default: 127.0.0.1
ENV_PORT = "MCP_PORT"  # default: 10859
ENV_PATH = "MCP_PATH"  # default: /mcp (HTTP only)


def get_transport_config() -> dict:
    """
    Get transport configuration from environment variables.

    Returns:
        Dictionary with transport, host, port, and path settings.
    """
    return {
        "transport": os.getenv(ENV_TRANSPORT, "stdio").lower(),
        "host": os.getenv(ENV_HOST, "127.0.0.1"),
        "port": int(os.getenv(ENV_PORT, "10859")),
        "path": os.getenv(ENV_PATH, "/mcp"),
    }


def create_argument_parser(server_name: str) -> argparse.ArgumentParser:
    """
    Create standardized CLI argument parser for MCP servers.

    Args:
        server_name: Name of the MCP server for help text.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description=f"{server_name} - FastMCP 3.1 Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Environment Variables:
  {ENV_TRANSPORT}    Transport mode: stdio, http, sse (default: stdio)
  {ENV_HOST}         Bind address (default: 127.0.0.1)
  {ENV_PORT}         Port number (default: 10859)
  {ENV_PATH}         HTTP endpoint path (default: /mcp)

Examples:
  # STDIO mode (Claude Desktop)
  python -m {server_name.replace("-", "_")} --stdio

  # HTTP mode (web apps)
  python -m {server_name.replace("-", "_")} --http --port 10859

  # Via environment
  MCP_TRANSPORT=http MCP_PORT=10859 python -m {server_name.replace("-", "_")}
""",
    )

    transport_group = parser.add_mutually_exclusive_group()
    transport_group.add_argument("--stdio", action="store_true", help="Run in STDIO (JSON-RPC) mode (default)")
    transport_group.add_argument("--http", action="store_true", help="Run in HTTP Streamable mode (FastMCP 3.1)")
    transport_group.add_argument("--sse", action="store_true", help="Run in SSE mode (deprecated, use --http)")

    parser.add_argument("--host", default=None, help=f"Host to bind to (default: ${ENV_HOST} or 127.0.0.1)")
    parser.add_argument("--port", type=int, default=None, help=f"Port to listen on (default: ${ENV_PORT} or 10859)")
    parser.add_argument("--path", default=None, help=f"HTTP endpoint path (default: ${ENV_PATH} or /mcp)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    return parser


def resolve_transport(args: argparse.Namespace) -> TransportType:
    """
    Resolve transport type from CLI args with environment fallback.

    Priority:
        1. CLI arguments (--http, --stdio, --sse)
        2. Environment variable (MCP_TRANSPORT)
        3. Default (stdio)

    Args:
        args: Parsed CLI arguments.

    Returns:
        Transport type string.
    """
    if args.http:
        return "http"
    elif args.sse:
        logger.warning(
            "SSE transport is deprecated. Consider using --http instead. "
            "SSE support will be removed in a future version."
        )
        return "sse"
    elif args.stdio:
        return "stdio"
    else:
        # Fall back to environment variable
        env_transport = os.getenv(ENV_TRANSPORT, "stdio").lower()
        if env_transport not in ("stdio", "http", "sse"):
            logger.warning(f"Invalid {ENV_TRANSPORT}='{env_transport}', defaulting to stdio")
            return "stdio"
        if env_transport == "sse":
            logger.warning("SSE transport is deprecated. Consider using MCP_TRANSPORT=http instead.")
        return env_transport  # type: ignore


def resolve_config(args: argparse.Namespace) -> dict:
    """
    Resolve full transport configuration from CLI args and environment.

    CLI args take precedence over environment variables.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Dictionary with transport, host, port, path settings.
    """
    env_config = get_transport_config()

    return {
        "transport": resolve_transport(args),
        "host": args.host if args.host is not None else env_config["host"],
        "port": args.port if args.port is not None else env_config["port"],
        "path": args.path if args.path is not None else env_config["path"],
    }


def run_server(mcp_app, args: argparse.Namespace | None = None, server_name: str = "mcp-server") -> None:
    """
    Unified server runner for all transport modes.

    This is the main entry point for running an MCP server with proper
    transport configuration based on CLI arguments and environment variables.

    Args:
        mcp_app: FastMCP application instance.
        args: Parsed CLI arguments (optional, will parse if None).
        server_name: Server name for logging and help text.

    Raises:
        Exception: If server fails to start.
    """
    # Simply run the async version
    asyncio.run(run_server_async(mcp_app, args, server_name))


async def run_server_async(mcp_app, args: argparse.Namespace | None = None, server_name: str = "mcp-server") -> None:
    """
    Asynchronous unified server runner for all transport modes.

    Args:
        mcp_app: FastMCP application instance.
        args: Parsed CLI arguments (optional, will parse if None).
        server_name: Server name for logging and help text.
    """
    if args is None:
        parser = create_argument_parser(server_name)
        args = parser.parse_args()

    # Configure logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug(f"Debug logging enabled for {server_name}")

    config = resolve_config(args)
    transport = config["transport"]

    logger.info(f"Starting {server_name} v{getattr(mcp_app, 'version', '?.?.?')}")
    logger.info(f"Transport: {transport.upper()}")

    try:
        if transport == "stdio":
            logger.info("Running in STDIO mode - Ready for Claude Desktop!")
            await mcp_app.run_stdio_async()

        elif transport == "http":
            host = config["host"]
            port = config["port"]
            path = config["path"]
            endpoint = f"http://{host}:{port}{path}"
            logger.info(f"Running in HTTP Streamable mode: {endpoint}")
            import uvicorn
            from fastapi.middleware.cors import CORSMiddleware

            http_app = mcp_app.http_app()
            cors_origins = [
                "http://localhost:10858",
                "http://127.0.0.1:10858",
                "tauri://localhost",
                "http://tauri.localhost",
                "https://tauri.localhost",
            ]
            cors_regex = r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$"
            http_app.add_middleware(
                CORSMiddleware,
                allow_origins=cors_origins,
                allow_origin_regex=cors_regex,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            config_obj = uvicorn.Config(http_app, host=host, port=port, log_level="info")
            server = uvicorn.Server(config_obj)
            await server.serve()

        elif transport == "sse":
            host = config["host"]
            port = config["port"]
            logger.warning("SSE mode is deprecated. Migrate to HTTP Streamable (--http).")
            logger.info(f"Running in SSE mode: http://{host}:{port}")
            await mcp_app.run_sse_async(host=host, port=port)

    except asyncio.CancelledError:
        logger.info(f"{server_name} task cancelled")
    except Exception as e:
        logger.error(f"{server_name} failed: {e}", exc_info=True)
        raise


# Export public API
__all__ = [
    "ENV_HOST",
    "ENV_PATH",
    "ENV_PORT",
    "ENV_TRANSPORT",
    "TransportType",
    "create_argument_parser",
    "get_transport_config",
    "resolve_config",
    "resolve_transport",
    "run_server",
    "run_server_async",
]
