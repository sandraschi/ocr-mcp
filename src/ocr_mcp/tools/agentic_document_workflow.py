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
FastMCP 3.1 Sampling with Tools Orchestration (SEP-1577).

Enables autonomous agentic workflows where the LLM decides tool sequences
to accomplish complex document processing tasks.
"""

import logging
from typing import Literal

from fastmcp import Context

from .models import ToolResponse

logger = logging.getLogger(__name__)


def register_agentic_document_workflow(app):
    """Register the agentic document workflow tool with the FastMCP app."""

    @app.tool()
    async def execute_agentic_workflow(
        workflow_prompt: str,
        available_tools: list[
            Literal[
                "process_document",
                "manage_image",
                "operate_scanner",
                "manage_workflow",
                "manage_corpus",
                "get_help",
                "get_status",
            ]
        ],
        max_iterations: int = 5,
        context: Context | None = None,
    ) -> ToolResponse:
        """
        Execute an autonomous document workflow using LLM sampling.

        The LLM will observe tool results and iterate until the goal is met or
        max_iterations is reached.

        VALID TOOLS:
        - process_document: OCR, layout analysis, table extraction.
        - manage_image: Preprocessing, PDF conversion, embedding text.
        - operate_scanner: Hardware control for WIA scanners.
        - manage_corpus: SQLite document indexing and search.
        - manage_workflow: Batch orchestration and system health.

        RECOVERY:
        - If the LLM loops or fails, simplify the workflow_prompt or reduce
          the number of available_tools to focus the agent.
        """
        operation = "execute_agentic_workflow"
        try:
            if not workflow_prompt:
                return ToolResponse(
                    success=False,
                    operation=operation,
                    summary="No workflow prompt provided.",
                    next_steps=["Provide a clear description of the document task."],
                )
            if not available_tools:
                return ToolResponse(
                    success=False,
                    operation=operation,
                    summary="No tools specified for the agent.",
                    next_steps=["Include at least one valid tool name in available_tools."],
                )
            system_prompt = (
                "You are an OCR/document workflow assistant. Use the provided tools "
                "to accomplish the user's document workflow. "
                "After using tools, summarize what was done and any next steps. Be concise."
            )
            messages: list = [{"role": "user", "content": workflow_prompt}]
            executed_tools: list[str] = []
            iterations = 0

            # Try ctx.sample() first (FastMCP 3.4+), fall back to context.sample_step() (3.1)
            has_sample = hasattr(context, "sample") and callable(context.sample)
            has_sample_step = hasattr(context, "sample_step") and callable(context.sample_step)

            if not has_sample and not has_sample_step:
                return ToolResponse(
                    success=False,
                    operation=operation,
                    summary="Sampling not supported by current context.",
                    next_steps=["Ensure the client supports sampling (FastMCP 3.1+)."],
                )

            # Resolve tools from app by name
            all_tools = await app.list_tools()
            name_to_tool = {t.name: t for t in all_tools if hasattr(t, "name")}
            tools_for_sampling = [name_to_tool[name] for name in available_tools if name in name_to_tool]

            missing = [n for n in available_tools if n not in name_to_tool]
            if missing:
                logger.warning("Agentic workflow: tools not found on app: %s", missing)

            if not tools_for_sampling:
                return ToolResponse(
                    success=False,
                    operation=operation,
                    summary=(f"None of the requested tools were found. Registered: {list(name_to_tool.keys())}"),
                )

            while iterations < max_iterations:
                iterations += 1
                logger.info("Agentic workflow step %s/%s", iterations, max_iterations)

                if has_sample:
                    result = await context.sample(
                        messages,
                        system_prompt=system_prompt,
                        tools=tools_for_sampling,
                        max_tokens=4096,
                    )
                    step_text = result.get("content", "") if isinstance(result, dict) else str(result)
                    step_tools = result.get("tool_calls", []) if isinstance(result, dict) else []
                    for tc in step_tools:
                        name = tc.get("name", str(tc)) if isinstance(tc, dict) else str(tc)
                        executed_tools.append(name)
                    if not step_tools:
                        return ToolResponse(
                            success=True,
                            operation=operation,
                            summary=f"Workflow completed in {iterations} round(s).",
                            result={
                                "final_output": step_text,
                                "iterations": iterations,
                                "executed_tools": list(dict.fromkeys(executed_tools)),
                            },
                            next_steps=["Review results or refine the workflow prompt."],
                        )
                else:
                    step = await context.sample_step(
                        messages,
                        system_prompt=system_prompt,
                        tools=tools_for_sampling,
                        execute_tools=True,
                        max_tokens=4096,
                    )
                    if hasattr(step, "history") and step.history:
                        messages = list(step.history)
                    if hasattr(step, "tool_calls") and step.tool_calls:
                        for tc in step.tool_calls:
                            name = getattr(tc, "name", None) or getattr(tc, "tool_name", str(tc))
                            if name:
                                executed_tools.append(name)
                    if not getattr(step, "is_tool_use", True):
                        final_text = getattr(step, "text", "") or ""
                        return ToolResponse(
                            success=True,
                            operation=operation,
                            summary=f"Workflow completed in {iterations} round(s).",
                            result={
                                "final_output": final_text,
                                "iterations": iterations,
                                "executed_tools": list(dict.fromkeys(executed_tools)),
                            },
                            next_steps=["Review results or refine the workflow prompt."],
                        )

            return ToolResponse(
                success=True,
                operation=operation,
                summary=f"Workflow reached max iterations ({max_iterations}).",
                result={
                    "final_output": getattr(step, "text", "") or "(timeout)",
                    "iterations": iterations,
                    "executed_tools": list(dict.fromkeys(executed_tools)),
                },
                next_steps=["Increase max_iterations or simplify the prompt."],
            )
        except Exception as e:
            logger.error("Agentic document workflow failed: %s", e, exc_info=True)
            return ToolResponse(
                success=False,
                operation=operation,
                summary=f"Execution error: {e!s}",
                next_steps=["Verify tool availability and prompt clarity."],
            )
