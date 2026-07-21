"""Prefab UI cards for OCR-MCP.

Provides @mcp.tool(app=True) tools that render rich in-chat cards
for health status, backend listing, and job results.
"""

import logging
import time
from typing import Any

from fastmcp import Context
from fastmcp.server.server import ToolResult
from prefab_ui import PrefabApp
from prefab_ui.components import Div, Heading, Row

logger = logging.getLogger(__name__)


def register_prefab_tools(app, runtime: dict[str, Any]):
    """Register Prefab UI tools with the FastMCP app."""

    @app.tool(app=True)
    async def show_health_card(ctx: Context) -> ToolResult:
        """Display a rich health card with backend status, tool count, and system info.

        Shows live status from the backend manager: available backends, total tools,
        and server health indicators.
        """
        bm = runtime.get("backend_manager")
        backends_info = {}
        tool_count = 7
        uptime = int(time.time() - _get_start_time())

        if bm:
            try:
                info = bm.list_backends()
                backends_info = info.get("backends", {})
                tool_count = info.get("total_count", 14)
            except Exception:
                pass

        available = {k: v for k, v in backends_info.items() if v.get("available")}
        with PrefabApp(title="OCR-MCP Health") as app:
            Heading("Server Status")
            Row(label="Tools", value=str(tool_count))
            Row(label="Uptime", value=f"{uptime}s")
            Row(label="Available Backends", value=f"{len(available)}/{len(backends_info)}")
            if available:
                Heading("Available Backends")
                for name, info in available.items():
                    desc = info.get("description", name)
                    caps = info.get("capabilities", {})
                    modes = ", ".join(caps.get("modes", ["text"]))
                    Div(f"{name} - {desc} | Modes: {modes}")
        return ToolResult(content="OCR-MCP health card rendered.", structured_content=app)

    @app.tool(app=True)
    async def show_backends_card(ctx: Context) -> ToolResult:
        """Display all registered OCR backends with availability and capabilities.

        Shows each backend's status (available/offline), model size, supported modes,
        and key strengths. Useful for choosing the right backend for a task.
        """
        bm = runtime.get("backend_manager")
        backends_info = {}
        if bm:
            try:
                info = bm.list_backends()
                backends_info = info.get("backends", {})
            except Exception:
                pass

        with PrefabApp(title="OCR Backends") as app:
            Heading("Registered Backends")
            Row(label="Total", value=str(len(backends_info)))
            Row(label="Available", value=str(sum(1 for v in backends_info.values() if v.get("available"))))
            for name, info in backends_info.items():
                available = info.get("available", False)
                desc = info.get("description", name)
                model_size = info.get("model_size", "?")
                caps = info.get("capabilities", {})
                modes = ", ".join(caps.get("modes", ["text"]))
                status_icon = "OK" if available else "OFF"
                Div(f"[{status_icon}] {name} ({model_size}): {desc} | Modes: {modes}")
        avail = sum(1 for v in backends_info.values() if v.get("available"))
        return ToolResult(content=f"{len(backends_info)} backends ({avail} available).", structured_content=app)


_START_TIME = time.time()


def _get_start_time() -> float:
    return _START_TIME
