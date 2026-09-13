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

"""
llm_ops portmanteau — local LLM engine management for agents.

Gives agents the same engine path the webapp AI Settings page uses, so UI
and MCP clients cannot drift (SETTINGS_LLM.md rule 4: save switches VRAM).
Fleet pattern vendored from arxiv-mcp (proven live against Ollama).

Adaptation: list_models uses ocr-mcp's own llm_providers registry probe
(registry, keystore, sampling defaults are repo-specific by design).
"""

import logging
from typing import Any, Literal

from fastmcp.tools.tool import ToolAnnotations

from ..services.llm_engine import gpu_vram, ollama_loaded, switch_ollama_model
from ..services.llm_providers import list_models

logger = logging.getLogger(__name__)


def register_llm_ops_tool(app):
    """Register the llm_ops portmanteau tool with the FastMCP app."""

    @app.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False
        )
    )
    async def llm_ops(
        operation: Literal["list_models", "loaded", "switch_model", "unload_all", "vram"],
        provider: str = "ollama",
        model: str = "",
        endpoint: str = "",
    ) -> dict[str, Any]:
        """LLM_OPS - Manage the local LLM engine from an agent.

        Ops: list_models (engine model list) | loaded (residents + VRAM) |
        switch_model (make `model` the only resident: evict rest, warm it) |
        unload_all (evict everything, loads nothing) | vram (per-GPU telemetry).
        Only ollama supports loaded/switch/unload (engine API); anything else
        returns success=False with recovery options instead of pretending.
        """
        if operation == "list_models":
            data = await list_models(provider)
            return {"success": True, "operation": operation, **data}
        if operation == "vram":
            return {"success": True, "operation": operation, "gpus": gpu_vram()}
        if provider != "ollama":
            return {
                "success": False,
                "message": f"Operation '{operation}' needs the ollama engine.",
                "error": f"unsupported provider '{provider}'",
                "error_type": "ValueError",
                "operation": operation,
                "recovery_options": ["Use provider 'ollama' (local engine)."],
            }
        base = endpoint.rstrip("/") if endpoint else "http://localhost:11434"
        if operation == "loaded":
            data = await ollama_loaded(base)
            return {"success": True, "operation": operation, "provider": provider, **data}
        if operation == "switch_model":
            if not model.strip():
                return {
                    "success": False,
                    "message": "switch_model needs a model name.",
                    "error": "empty model",
                    "error_type": "ValueError",
                    "operation": operation,
                    "recovery_options": ["Call list_models first, then switch to a name from that list."],
                }
            switch = await switch_ollama_model(model.strip(), base)
            return {
                "success": True,
                "operation": operation,
                "provider": provider,
                "model": model.strip(),
                **switch,
            }
        if operation == "unload_all":
            switch = await switch_ollama_model("", base)
            return {"success": True, "operation": operation, "provider": provider, **switch}
        return {
            "success": False,
            "message": f"Unknown operation '{operation}'.",
            "error": f"unknown operation '{operation}'",
            "error_type": "ValueError",
            "operation": operation,
            "recovery_options": ["Use list_models, loaded, switch_model, unload_all, or vram."],
        }

    return llm_ops
