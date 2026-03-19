"""
FastMCP 3.1 Sampling with Tools Orchestration Tools (SEP-1577)

Real agentic workflows: context.sample_step loop with tool execution.
No mocks; requires FastMCP 3.1+ and client sampling support.
"""

import logging

from fastmcp import Context

logger = logging.getLogger(__name__)


# Fallback response builders (no optional advanced_memory dependency)
def build_success_response(**kwargs) -> dict:
    return {
        "success": True,
        "operation": kwargs.get("operation", "unknown"),
        "summary": kwargs.get("summary", "Operation completed"),
        "result": kwargs.get("result", {}),
        "next_steps": kwargs.get("next_steps", []),
        "suggestions": kwargs.get("suggestions", []),
    }


def build_error_response(**kwargs) -> dict:
    return {
        "success": False,
        "error": kwargs.get("error", "Unknown error"),
        "error_code": kwargs.get("error_code", "UNKNOWN_ERROR"),
        "message": kwargs.get("message", "An error occurred"),
        "recovery_options": kwargs.get("recovery_options", []),
        "urgency": kwargs.get("urgency", "medium"),
    }


def register_agentic_document_workflow(app):
    """Register the agentic document workflow tool with the FastMCP app."""

    @app.tool()
    async def agentic_document_workflow(
        workflow_prompt: str,
        available_tools: list[str],
        max_iterations: int = 5,
        context: Context | None = None,
    ) -> dict:
        """
        Execute agentic document workflows using FastMCP 3.1 sampling with tools.

        Uses context.sample_step in a loop: LLM decides tool calls, tools are executed,
        results fed back until the LLM returns a final text response or max_iterations.

        Args:
            workflow_prompt: Description of the document workflow to execute.
            available_tools: List of tool names to expose to the LLM (e.g. document_processing, scanner_operations).
            max_iterations: Maximum LLM-tool interaction rounds (default 5).

        Returns:
            Structured response with workflow execution results.
        """
        try:
            if not workflow_prompt:
                return build_error_response(
                    error="No workflow prompt provided",
                    error_code="MISSING_WORKFLOW_PROMPT",
                    message="workflow_prompt is required",
                    recovery_options=["Provide a clear description of the document workflow"],
                    urgency="medium",
                )
            if not available_tools:
                return build_error_response(
                    error="No tools specified",
                    error_code="EMPTY_TOOLS_LIST",
                    message="available_tools cannot be empty",
                    recovery_options=["Include at least one tool name the LLM can use"],
                    urgency="medium",
                )
            if not hasattr(context, "sample_step"):
                return build_error_response(
                    error="Sampling not available",
                    error_code="SAMPLING_UNAVAILABLE",
                    message="FastMCP context does not support sampling with tools (requires 3.1+)",
                    recovery_options=[
                        "Ensure FastMCP 3.1+ is installed",
                        "Check that sampling handlers are configured",
                    ],
                    urgency="high",
                )

            # Resolve tools from app by name
            all_tools = await app.list_tools()
            name_to_tool = {t.name: t for t in all_tools if hasattr(t, "name")}
            tools_for_sampling = [
                name_to_tool[name] for name in available_tools if name in name_to_tool
            ]
            missing = [n for n in available_tools if n not in name_to_tool]
            if missing:
                logger.warning("Agentic workflow: tools not found on app: %s", missing)
            if not tools_for_sampling:
                return build_error_response(
                    error="No matching tools found",
                    error_code="TOOLS_NOT_FOUND",
                    message=f"None of available_tools matched registered tools. Registered: {list(name_to_tool.keys())}",
                    recovery_options=[
                        "Use tool names from status() or document_processing, scanner_operations, etc."
                    ],
                    urgency="high",
                )

            system_prompt = (
                "You are an OCR/document workflow assistant. Use the provided tools to accomplish the user's document workflow. "
                "After using tools, summarize what was done and any next steps. Be concise."
            )
            messages: list = [{"role": "user", "content": workflow_prompt}]
            executed_tools: list[str] = []
            iterations = 0

            while iterations < max_iterations:
                iterations += 1
                logger.info("Agentic workflow step %s/%s", iterations, max_iterations)
                step = await context.sample_step(
                    messages,
                    system_prompt=system_prompt,
                    tools=tools_for_sampling,
                    execute_tools=True,
                    max_tokens=4096,
                )
                # Updated history for next round (when execute_tools=True, sampling run appends tool results)
                if hasattr(step, "history") and step.history:
                    messages = list(step.history)
                if hasattr(step, "tool_calls") and step.tool_calls:
                    for tc in step.tool_calls:
                        name = getattr(tc, "name", None) or getattr(tc, "tool_name", str(tc))
                        if name:
                            executed_tools.append(name)
                # Done when LLM returns text (no tool use)
                if not getattr(step, "is_tool_use", True):
                    final_text = getattr(step, "text", "") or ""
                    return build_success_response(
                        operation="agentic_document_workflow",
                        summary=f"Workflow completed in {iterations} round(s).",
                        result={
                            "final_output": final_text,
                            "iterations": iterations,
                            "executed_tools": list(dict.fromkeys(executed_tools)),
                        },
                        next_steps=["Review output and run further workflows if needed."],
                        suggestions=[
                            "Try workflow_management(operation='process_batch_intelligent', source_dir='...')",
                            "Use document_processing(operation='process_document', source_path='...')",
                        ],
                    )

            return build_success_response(
                operation="agentic_document_workflow",
                summary=f"Workflow stopped after {max_iterations} iterations (max).",
                result={
                    "final_output": getattr(step, "text", "") or "(max iterations reached)",
                    "iterations": iterations,
                    "executed_tools": list(dict.fromkeys(executed_tools)),
                },
                next_steps=["Increase max_iterations or simplify the workflow prompt."],
                suggestions=[],
            )
        except Exception as e:
            logger.error("Agentic document workflow failed: %s", e, exc_info=True)
            return build_error_response(
                error="Workflow execution failed",
                error_code="WORKFLOW_EXECUTION_ERROR",
                message=str(e),
                recovery_options=[
                    "Check workflow_prompt and available_tools",
                    "Ensure OCR backends and scanner are available",
                ],
                urgency="high",
            )
