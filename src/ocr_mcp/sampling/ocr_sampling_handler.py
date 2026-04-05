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
OCR-MCP sampling fallback for FastMCP 3.1.

FastMCP invokes the handler as::

    await handler(messages, SamplingParams, request_context)

**Default posture:** OpenAI-compatible **local** inference (e.g. **Ollama** at
``http://127.0.0.1:11434/v1``) with **no API key** on loopback / RFC1918 LAN.
Set ``OCR_SAMPLING_USE_CLIENT_LLM=1`` on the server if you want Cursor (or
another host) to provide sampling instead of this handler.

Cloud OpenAI-compatible APIs need ``OCR_SAMPLING_API_KEY`` or
``OCR_SAMPLING_USE_OPENAI_KEY=1`` (uses ``OPENAI_API_KEY``).
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import httpx
from mcp.shared.context import RequestContext
from mcp.types import (
    CreateMessageRequestParams as SamplingParams,
)
from mcp.types import (
    CreateMessageResult,
    CreateMessageResultWithTools,
    ImageContent,
    SamplingMessage,
    TextContent,
    Tool,
    ToolResultContent,
    ToolUseContent,
)

if TYPE_CHECKING:
    from mcp.server.session import ServerSession

    from ..core.backend_manager import BackendManager
    from ..core.config import OCRConfig

logger = logging.getLogger(__name__)


def _sampling_allows_empty_api_key(base_url: str) -> bool:
    """Ollama and similar local servers often need no Bearer token."""
    try:
        parsed = urlparse(base_url)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    if host in ("127.0.0.1", "localhost", "::1"):
        return True
    if host.startswith("192.168."):
        return True
    if host.startswith("10."):
        return True
    if host.startswith("172."):
        parts = host.split(".")
        if len(parts) >= 2 and parts[0] == "172":
            try:
                second = int(parts[1])
            except ValueError:
                return False
            if 16 <= second <= 31:
                return True
    return False


def _sampling_http_enabled(api_key: str | None, base_url: str) -> bool:
    return bool(api_key and api_key.strip()) or _sampling_allows_empty_api_key(base_url)


def _hint_model(params: SamplingParams, default: str) -> str:
    mp = params.modelPreferences
    if mp is None:
        return default
    hints = getattr(mp, "hints", None) or []
    for h in hints:
        name = getattr(h, "name", None)
        if name:
            return name
    return default


def _tool_choice_openai(tc: Any | None) -> str | dict[str, Any]:
    if tc is None:
        return "auto"
    mode = getattr(tc, "mode", None)
    if mode == "required":
        return "required"
    if mode == "none":
        return "none"
    return "auto"


def _mcp_tools_to_openai(tools: list[Tool] | None) -> list[dict[str, Any]] | None:
    if not tools:
        return None
    out: list[dict[str, Any]] = []
    for t in tools:
        out.append(
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or f"MCP tool {t.name}",
                    "parameters": (t.inputSchema if isinstance(t.inputSchema, dict) else {"type": "object"}),
                },
            }
        )
    return out


def _serialize_tool_result(tr: ToolResultContent) -> str:
    if tr.structuredContent is not None:
        try:
            return json.dumps(tr.structuredContent, ensure_ascii=False)[:80000]
        except (TypeError, ValueError):
            return str(tr.structuredContent)[:80000]
    parts: list[str] = []
    for block in tr.content:
        if isinstance(block, TextContent):
            parts.append(block.text)
        elif isinstance(block, ImageContent):
            parts.append("[image]")
        else:
            parts.append(str(block))
    body = "\n".join(parts).strip()
    if tr.isError:
        return f"[tool error] {body}" if body else "[tool error]"
    return body if body else "(empty tool result)"


def _sampling_messages_to_openai(
    messages: list[SamplingMessage],
    system_prompt: str | None,
) -> list[dict[str, Any]]:
    """Map MCP sampling history to OpenAI-style chat messages."""
    out: list[dict[str, Any]] = []
    if system_prompt:
        out.append({"role": "system", "content": system_prompt})

    for msg in messages:
        blocks = msg.content_as_list
        if msg.role == "user":
            tool_results = [b for b in blocks if isinstance(b, ToolResultContent)]
            texts = [b for b in blocks if isinstance(b, TextContent)]
            non_text = [b for b in blocks if not isinstance(b, (TextContent, ToolResultContent))]
            for tr in tool_results:
                out.append(
                    {
                        "role": "tool",
                        "tool_call_id": tr.toolUseId,
                        "content": _serialize_tool_result(tr),
                    }
                )
            if texts:
                joined = "\n".join(t.text for t in texts).strip()
                if joined:
                    out.append({"role": "user", "content": joined})
            for b in non_text:
                out.append(
                    {
                        "role": "user",
                        "content": f"[unsupported block in fallback handler: {type(b).__name__}]",
                    }
                )
        elif msg.role == "assistant":
            tool_uses = [b for b in blocks if isinstance(b, ToolUseContent)]
            texts = [b for b in blocks if isinstance(b, TextContent)]
            non_text = [b for b in blocks if not isinstance(b, (TextContent, ToolUseContent))]
            if tool_uses:
                tool_calls = []
                for tu in tool_uses:
                    args = tu.input
                    if isinstance(args, dict):
                        arg_str = json.dumps(args, ensure_ascii=False)
                    else:
                        arg_str = str(args)
                    tool_calls.append(
                        {
                            "id": tu.id or str(uuid.uuid4()),
                            "type": "function",
                            "function": {"name": tu.name, "arguments": arg_str},
                        }
                    )
                text_part = "\n".join(t.text for t in texts).strip() or None
                row: dict[str, Any] = {
                    "role": "assistant",
                    "tool_calls": tool_calls,
                }
                if text_part:
                    row["content"] = text_part
                else:
                    row["content"] = None
                out.append(row)
            else:
                joined = "\n".join(t.text for t in texts).strip()
                out.append({"role": "assistant", "content": joined})
            for b in non_text:
                out.append(
                    {
                        "role": "assistant",
                        "content": f"[unsupported block: {type(b).__name__}]",
                    }
                )
    return out


def _heuristic_backend_hints(user_text: str, available: list[str] | None) -> list[str]:
    """Non-LLM hints when API is unavailable; intersect with installed backends."""
    q = user_text.lower()
    candidates: list[str] = []
    if any(w in q for w in ("math", "formula", "equation", "latex")):
        candidates.extend(["deepseek-ocr", "deepseek-ocr2", "paddleocr-vl"])
    elif any(w in q for w in ("table", "layout", "form", "invoice", "chart")):
        candidates.extend(["paddleocr-vl", "pp-ocrv5", "dots-ocr"])
    elif any(w in q for w in ("fast", "speed", "batch")):
        candidates.extend(["pp-ocrv5", "tesseract", "easyocr"])
    else:
        candidates.extend(["paddleocr-vl", "pp-ocrv5", "tesseract"])
    if not available:
        return list(dict.fromkeys(candidates))
    return [b for b in dict.fromkeys(candidates) if b in available]


def _degraded_response_text(
    user_text: str,
    has_tools: bool,
    *,
    backend_manager: BackendManager | None,
) -> str:
    available = None
    if backend_manager is not None:
        try:
            available = backend_manager.get_available_backends()
        except Exception:
            available = None
    hints = _heuristic_backend_hints(user_text, available)
    tool_note = (
        "Start **Ollama** (`ollama serve`), `ollama pull` your model, and set "
        "OCR_SAMPLING_BASE_URL (default http://127.0.0.1:11434/v1) and OCR_SAMPLING_MODEL. "
        "Or set OCR_SAMPLING_USE_CLIENT_LLM=1 to use the MCP host LLM if it supports "
        "sampling with tools."
        if has_tools
        else (
            "Start **Ollama** on this machine (or point OCR_SAMPLING_BASE_URL at your LAN "
            "Ollama host). No API key is needed on localhost/private LAN. "
            "Alternatively set OCR_SAMPLING_USE_CLIENT_LLM=1 for host-provided sampling."
        )
    )
    return (
        "[OCR-MCP sampling — HTTP LLM not used]\n\n"
        f"{tool_note}\n\n"
        "Heuristic OCR backend suggestions (verify against your install): "
        f"{', '.join(hints) or 'auto'}.\n"
        "Typical next step: document_processing(operation=process_document, ...) or "
        "agentic_document_workflow once a local or cloud LLM endpoint is reachable."
    )


class OCRSamplingHandler:
    """
    OpenAI-compatible chat/completions (default: local Ollama).

    Callable as ``(messages, params, request_context)`` per FastMCP.
    """

    def __init__(
        self,
        backend_manager: BackendManager | None = None,
        config: OCRConfig | None = None,
    ) -> None:
        self.backend_manager = backend_manager
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def __call__(
        self,
        messages: list[SamplingMessage],
        params: SamplingParams,
        request_context: RequestContext[ServerSession, Any],
    ) -> CreateMessageResult | CreateMessageResultWithTools | str:
        _ = request_context  # reserved for tracing / future use
        cfg = self.config
        api_key = getattr(cfg, "sampling_api_key", None) if cfg else None
        base_url = (
            (getattr(cfg, "sampling_base_url", None) or "http://127.0.0.1:11434/v1").rstrip("/")
            if cfg
            else "http://127.0.0.1:11434/v1"
        )
        default_model = getattr(cfg, "sampling_model", None) or "llama3.2"
        model = _hint_model(params, default_model)
        max_tokens = params.maxTokens
        temperature = params.temperature
        sdk_tools = params.tools
        has_tools = bool(sdk_tools)

        openai_messages = _sampling_messages_to_openai(messages, params.systemPrompt)
        if not _sampling_http_enabled(api_key, base_url):
            last_user = ""
            for m in reversed(messages):
                if m.role == "user":
                    for b in m.content_as_list:
                        if isinstance(b, TextContent):
                            last_user = b.text
                            break
                    if last_user:
                        break
            text = _degraded_response_text(
                last_user,
                has_tools,
                backend_manager=self.backend_manager,
            )
            if has_tools:
                return CreateMessageResultWithTools(
                    role="assistant",
                    model="none",
                    content=TextContent(type="text", text=text),
                    stopReason="endTurn",
                )
            return CreateMessageResult(
                role="assistant",
                model="none",
                content=TextContent(type="text", text=text),
                stopReason="endTurn",
            )

        url = f"{base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        oa_tools = _mcp_tools_to_openai(sdk_tools)
        if oa_tools:
            payload["tools"] = oa_tools
            payload["tool_choice"] = _tool_choice_openai(params.toolChoice)

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(url, headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
        except httpx.HTTPStatusError as e:
            err_body = ""
            try:
                err_body = e.response.text[:2000]
            except Exception:
                pass
            msg = (
                f"[OCR-MCP sampling] HTTP {e.response.status_code} from {url}. "
                f"Check Ollama is running, OCR_SAMPLING_MODEL is pulled, URL/base path, "
                f"and API key if using a cloud endpoint. Body: {err_body}"
            )
            self.logger.warning(msg)
            return CreateMessageResult(
                role="assistant",
                model=model,
                content=TextContent(type="text", text=msg),
                stopReason="endTurn",
            )
        except Exception as e:
            msg = f"[OCR-MCP sampling] Request failed: {e!s}"
            self.logger.exception("Sampling fallback failed")
            return CreateMessageResult(
                role="assistant",
                model=model,
                content=TextContent(type="text", text=msg),
                stopReason="endTurn",
            )

        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        finish = (choice.get("finish_reason") or "stop") or "stop"
        tool_calls = msg.get("tool_calls") or []
        content_text = msg.get("content") or ""

        if tool_calls:
            blocks: list[TextContent | ToolUseContent] = []
            if isinstance(content_text, str) and content_text.strip():
                blocks.append(TextContent(type="text", text=content_text))
            for tc in tool_calls:
                fn = tc.get("function") or {}
                name = fn.get("name") or "unknown_tool"
                raw_args = fn.get("arguments") or "{}"
                try:
                    parsed: Any = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    if not isinstance(parsed, dict):
                        parsed = {"value": parsed}
                except json.JSONDecodeError:
                    parsed = {"_raw": raw_args}
                tid = tc.get("id") or str(uuid.uuid4())
                blocks.append(ToolUseContent(type="tool_use", name=name, id=tid, input=parsed))
            return CreateMessageResultWithTools(
                role="assistant",
                model=str(data.get("model") or model),
                content=blocks,
                stopReason="toolUse",
            )

        if isinstance(content_text, list):
            # Some APIs return multipart content
            text_parts = []
            for part in content_text:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text") or "")
                else:
                    text_parts.append(str(part))
            content_text = "\n".join(text_parts)

        stop_reason = "endTurn"
        if finish in ("length", "max_tokens", "maxTokens"):
            stop_reason = "maxTokens"
        return CreateMessageResult(
            role="assistant",
            model=str(data.get("model") or model),
            content=TextContent(type="text", text=str(content_text)),
            stopReason=stop_reason,
        )

    async def check_health(self) -> dict[str, Any]:
        model = None
        base = ""
        key = None
        if self.config is not None:
            model = getattr(self.config, "sampling_model", None)
            base = (getattr(self.config, "sampling_base_url", None) or "").rstrip("/")
            key = getattr(self.config, "sampling_api_key", None)
        http_ok = _sampling_http_enabled(key, base) if base else bool(key and key.strip())
        return {
            "status": "healthy",
            "server_side_llm_configured": http_ok,
            "sampling_base_url": base or None,
            "sampling_fallback_model": model,
            "backend_available": self.backend_manager is not None,
            "config_loaded": self.config is not None,
        }

    def get_available_models(self) -> list[str]:
        """Configured sampling model when HTTP LLM is enabled (local or cloud)."""
        if not self.config:
            return []
        base = (getattr(self.config, "sampling_base_url", None) or "").rstrip("/")
        key = getattr(self.config, "sampling_api_key", None)
        if not _sampling_http_enabled(key, base):
            return []
        return [getattr(self.config, "sampling_model", "llama3.2")]
