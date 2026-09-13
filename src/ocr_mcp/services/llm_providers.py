"""Unified local + cloud LLM provider registry, keystore, and chat proxy helpers.

Vendored pattern from arxiv-mcp's llm_providers.py (fleet pilot, proven live):
the webapp never talks to providers from the browser. All traffic goes
through the backend, and API keys live in a 0600 keystore under the user
cache dir (or env vars, which win).

Adaptations for ocr-mcp (vs pilot):
- No arxiv_mcp.config dependency: keystore/settings resolve to
  ``OCR_LLM_DATA_DIR`` or ``~/.cache/ocr-mcp`` (same root OCRConfig uses).
- Engine lifecycle (switch/loaded/VRAM) is NOT duplicated here: it reuses
  :mod:`ocr_mcp.services.llm_engine` (single engine path for REST + MCP).
- OpenRouter attribution headers point at ocr-mcp (port 10859/10858).

Provider IDs and key env names intentionally match the pilot so a later
"delegate to gateway when reachable" step stays a drop-in.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import httpx

from .llm_engine import gpu_vram, ollama_loaded, switch_ollama_model

__all__ = [
    "PROVIDERS",
    "chat_complete",
    "chat_stream",
    "data_file",
    "delete_key",
    "get_key",
    "get_provider",
    "gpu_vram",
    "install_status",
    "is_configured",
    "keys_configured",
    "list_models",
    "ollama_loaded",
    "onboarding_state",
    "probe_local",
    "public_provider_info",
    "read_llm_settings",
    "require_provider",
    "save_key",
    "start_install",
    "switch_ollama_model",
    "write_llm_settings",
]

logger = logging.getLogger(__name__)

LOCAL_PROBE_TIMEOUT = 3.0
CLOUD_TIMEOUT = 30.0
CHAT_TIMEOUT = 120.0
KEYSTORE_NAME = "llm_keys.json"
SETTINGS_NAME = "llm_settings.json"
ANTHROPIC_VERSION = "2023-06-01"

PROVIDERS: tuple[dict[str, Any], ...] = (
    {
        "id": "ollama",
        "label": "Ollama",
        "kind": "local",
        "base_url": "http://localhost:11434",
        # Native API: /v1 ignores options (e.g. num_ctx), and long-ctx models
        # default to 262k KV which offloads to CPU. Native honors num_ctx.
        "chat_path": "/api/chat",
        "models_path": "/api/tags",
        "tag_style": "ollama",
        "key_env": None,
        "curated": [],
    },
    {
        "id": "lmstudio",
        "label": "LM Studio",
        "kind": "local",
        "base_url": "http://localhost:1234",
        "chat_path": "/v1/chat/completions",
        "models_path": "/v1/models",
        "tag_style": "openai",
        "key_env": None,
        "curated": [],
    },
    {
        "id": "vllm",
        "label": "vLLM",
        "kind": "local",
        "base_url": "http://localhost:8000",
        "chat_path": "/v1/chat/completions",
        "models_path": "/v1/models",
        "tag_style": "openai",
        "key_env": None,
        "curated": [],
    },
    {
        "id": "openai",
        "label": "OpenAI",
        "kind": "cloud",
        "base_url": "https://api.openai.com/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "OPENAI_API_KEY",
        "curated": ["gpt-4o", "gpt-4o-mini"],
    },
    {
        "id": "anthropic",
        "label": "Anthropic",
        "kind": "cloud",
        "base_url": "https://api.anthropic.com",
        "chat_path": "/v1/messages",
        "models_path": "/v1/models",
        "tag_style": "anthropic",
        "key_env": "ANTHROPIC_API_KEY",
        "curated": ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-fable-5.1"],
    },
    {
        "id": "deepseek",
        "label": "DeepSeek",
        "kind": "cloud",
        # No /v1 prefix on this host: chat is POST /chat/completions.
        "base_url": "https://api.deepseek.com",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "DEEPSEEK_API_KEY",
        # Flash first: newest and stronger than pro despite the name.
        "curated": ["deepseek-v4-flash", "deepseek-v4-pro", "deepseek-v4-flash-vision-exp"],
    },
    {
        "id": "openrouter",
        "label": "OpenRouter",
        "kind": "cloud",
        "base_url": "https://openrouter.ai/api/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "OPENROUTER_API_KEY",
        "curated": [
            "openrouter/auto",
            "anthropic/claude-sonnet-4",
            "openai/gpt-4o",
            "meta-llama/llama-4-maverick",
        ],
    },
    {
        "id": "meta",
        "label": "Meta",
        "kind": "cloud",
        "base_url": "https://api.meta.ai/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "MODEL_API_KEY",
        # Contributor first: $0.20/M out, training-on-prompts acceptable per owner.
        "curated": [
            "muse-spark-1.3-contributor",
            "muse-spark-1.3",
            "muse-spark-1.2-contributor",
            "muse-spark-1.2",
            "muse-spark-1.1",
        ],
    },
)


def get_provider(provider_id: str) -> dict[str, Any] | None:
    """Return the registry row for a provider ID, or None."""
    for row in PROVIDERS:
        if row["id"] == provider_id:
            return row
    return None


def require_provider(provider_id: str) -> dict[str, Any]:
    row = get_provider(provider_id)
    if row is None:
        known = ", ".join(r["id"] for r in PROVIDERS)
        raise ValueError(f"Unknown provider '{provider_id}'. Known: {known}")
    return row


def data_dir() -> Path:
    """Writable dir for LLM settings + keystore (created on demand)."""
    override = os.environ.get("OCR_LLM_DATA_DIR", "").strip()
    base = Path(override) if override else Path.home() / ".cache" / "ocr-mcp"
    base.mkdir(parents=True, exist_ok=True)
    return base


def data_file(name: str) -> Path:
    return data_dir() / name


def keystore_path() -> Path:
    return data_file(KEYSTORE_NAME)


def settings_path() -> Path:
    return data_file(SETTINGS_NAME)


def _read_keystore() -> dict[str, str]:
    path = keystore_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("llm keystore unreadable (%s); treating as empty", exc)
        return {}
    return {k: v for k, v in data.items() if isinstance(v, str) and v}


def _write_keystore(entries: dict[str, str]) -> None:
    path = keystore_path()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        logger.debug("chmod 0600 on keystore failed (non-POSIX fs); continuing")
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def get_key(provider_id: str) -> str:
    """Resolve an API key: env var first, then keystore. Empty when unset."""
    row = require_provider(provider_id)
    env_name = row.get("key_env")
    if env_name:
        value = os.environ.get(env_name, "").strip()
        if value:
            return value
    return _read_keystore().get(provider_id, "")


def is_configured(provider_id: str) -> bool:
    """True when a cloud provider has a key available. Locals need no key."""
    row = require_provider(provider_id)
    if row["kind"] == "local":
        return True
    return bool(get_key(provider_id))


def keys_configured() -> dict[str, bool]:
    return {r["id"]: is_configured(r["id"]) for r in PROVIDERS if r["kind"] == "cloud"}


def save_key(provider_id: str, api_key: str) -> None:
    row = require_provider(provider_id)
    if row["kind"] != "cloud":
        raise ValueError(f"Provider '{provider_id}' takes no API key")
    key = (api_key or "").strip()
    if not key:
        raise ValueError("Empty API key")
    entries = _read_keystore()
    entries[provider_id] = key
    _write_keystore(entries)


def delete_key(provider_id: str) -> bool:
    require_provider(provider_id)
    entries = _read_keystore()
    if provider_id not in entries:
        return False
    del entries[provider_id]
    _write_keystore(entries)
    return True


def read_llm_settings() -> dict[str, Any]:
    """Saved selection (backend truth). Never includes key bytes."""
    base: dict[str, Any] = {"provider": "ollama", "endpoint": "http://localhost:11434", "model": ""}
    path = settings_path()
    if path.is_file():
        try:
            base.update(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass
    base.pop("api_key", None)
    return base


def write_llm_settings(payload: dict[str, Any]) -> dict[str, Any]:
    path = settings_path()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    return payload


def public_provider_info() -> list[dict[str, Any]]:
    """Registry rows safe for GET responses: capability flags, never key bytes."""
    return [
        {
            "id": r["id"],
            "label": r["label"],
            "kind": r["kind"],
            "base_url": r["base_url"],
            "needs_key": r["kind"] == "cloud",
            "key_env": r.get("key_env"),
            "configured": is_configured(r["id"]),
        }
        for r in PROVIDERS
    ]


def _parse_model_list(tag_style: str, payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    if tag_style == "ollama":
        models = payload.get("models") or []
        return [m.get("name", "") for m in models if isinstance(m, dict) and m.get("name")]
    data = payload.get("data") or []
    return [m.get("id", "") for m in data if isinstance(m, dict) and m.get("id")]


async def probe_local(provider_id: str) -> tuple[bool, list[str]]:
    """Probe a local engine (fast timeout). Returns (reachable, models)."""
    row = require_provider(provider_id)
    if row["kind"] != "local":
        raise ValueError(f"Provider '{provider_id}' is not local")
    url = row["base_url"] + row["models_path"]
    try:
        async with httpx.AsyncClient(timeout=LOCAL_PROBE_TIMEOUT) as client:
            resp = await client.get(url)
    except Exception as exc:
        logger.debug("local probe %s failed: %s", provider_id, exc)
        return False, []
    if resp.status_code >= 500:
        return False, []
    try:
        models = _parse_model_list(row["tag_style"], resp.json())
    except Exception:
        models = []
    return True, models


async def list_models(provider_id: str) -> dict[str, Any]:
    """Model list with source flag. Cloud: live when keyed, else curated."""
    row = require_provider(provider_id)
    if row["kind"] == "local":
        reachable, models = await probe_local(provider_id)
        return {"provider": provider_id, "models": models, "source": "live" if reachable else "none"}
    key = get_key(provider_id)
    if not key:
        return {"provider": provider_id, "models": list(row["curated"]), "source": "curated"}
    url = row["base_url"] + row["models_path"]
    headers = _auth_headers(row, key)
    try:
        async with httpx.AsyncClient(timeout=CLOUD_TIMEOUT) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            models = _parse_model_list(row["tag_style"], resp.json())
    except Exception as exc:
        logger.warning("live model list for %s failed (%s); curated fallback", provider_id, exc)
        return {"provider": provider_id, "models": list(row["curated"]), "source": "curated"}
    if not models:
        return {"provider": provider_id, "models": list(row["curated"]), "source": "curated"}
    return {"provider": provider_id, "models": models, "source": "live"}


def _auth_headers(row: dict[str, Any], api_key: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if row["id"] == "anthropic":
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = ANTHROPIC_VERSION
    elif row["id"] == "openrouter":
        headers["Authorization"] = f"Bearer {api_key}"
        headers["HTTP-Referer"] = "http://localhost:10858/"
        headers["X-Title"] = "ocr-mcp"
    elif row["kind"] == "cloud":
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _openai_body(model: str, messages: list[dict[str, Any]]) -> dict[str, Any]:
    return {"model": model, "messages": messages, "stream": False}


def _to_anthropic(model: str, messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Map OpenAI messages array to the Anthropic Messages API body."""
    system_parts: list[str] = []
    converted: list[dict[str, Any]] = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            system_parts.append(str(content))
        elif role in ("user", "assistant"):
            converted.append({"role": role, "content": str(content)})
        else:
            converted.append({"role": "user", "content": str(content)})
    body: dict[str, Any] = {"model": model, "max_tokens": 1024, "messages": converted}
    if system_parts:
        body["system"] = "\n\n".join(system_parts)
    return body


def _from_anthropic(payload: dict[str, Any]) -> str:
    blocks = payload.get("content") or []
    texts = [b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
    return "".join(texts)


# Context window for local Ollama chat: Ollama's vram-based default is 32k,
# but long-ctx models (e.g. 262k) would eat VRAM and offload to CPU.
OLLAMA_NUM_CTX = 32768


def _to_ollama_native(model: str, messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Map OpenAI messages array to the Ollama native /api/chat body."""
    converted = [{"role": m.get("role", "user"), "content": str(m.get("content", ""))} for m in messages]
    return {
        "model": model,
        "messages": converted,
        "stream": False,
        "options": {"num_ctx": OLLAMA_NUM_CTX},
    }


def _from_ollama_native(payload: dict[str, Any]) -> str:
    return str((payload.get("message") or {}).get("content", ""))


def _ollama_stream_text(payload: dict[str, Any]) -> str:
    """Extract delta text from one Ollama native SSE line ({}), "" when final."""
    if payload.get("done"):
        return ""
    return str((payload.get("message") or {}).get("content", ""))


async def chat_complete(
    provider_id: str,
    model: str,
    messages: list[dict[str, Any]],
) -> str:
    """Non-streaming chat via the backend proxy. Returns assistant text."""
    row = require_provider(provider_id)
    if not model.strip():
        raise ValueError("Empty model name")
    key = get_key(provider_id) if row["kind"] == "cloud" else ""
    if row["kind"] == "cloud" and not key:
        raise ValueError(f"Provider '{provider_id}' has no API key configured")
    headers = _auth_headers(row, key)
    if row["id"] == "anthropic":
        url = row["base_url"] + row["chat_path"]
        body = _to_anthropic(model, messages)
    elif row["id"] == "ollama":
        url = row["base_url"] + row["chat_path"]
        body = _to_ollama_native(model, messages)
    else:
        url = row["base_url"] + row["chat_path"]
        body = _openai_body(model, messages)
    try:
        async with httpx.AsyncClient(timeout=CHAT_TIMEOUT) as client:
            resp = await client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        raise RuntimeError(f"Provider '{provider_id}' HTTP {status}") from exc
    except Exception as exc:
        raise RuntimeError(f"Provider '{provider_id}' unreachable ({exc})") from exc
    if row["id"] == "anthropic":
        return _from_anthropic(data)
    if row["id"] == "ollama":
        return _from_ollama_native(data)
    try:
        return data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Provider '{provider_id}' returned an unexpected body") from exc


def _openai_sse_chunk(model: str, text: str) -> bytes:
    import time
    import uuid

    chunk = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}],
    }
    return ("data: " + json.dumps(chunk) + "\n\n").encode("utf-8")


async def chat_stream(
    provider_id: str,
    model: str,
    messages: list[dict[str, Any]],
) -> AsyncIterator[bytes]:
    """Streaming chat as OpenAI-style SSE bytes, normalized for every provider."""
    row = require_provider(provider_id)
    if not model.strip():
        raise ValueError("Empty model name")
    key = get_key(provider_id) if row["kind"] == "cloud" else ""
    if row["kind"] == "cloud" and not key:
        raise ValueError(f"Provider '{provider_id}' has no API key configured")
    headers = _auth_headers(row, key)
    headers["Accept"] = "text/event-stream"
    if row["id"] == "anthropic":
        url = row["base_url"] + row["chat_path"]
        body = _to_anthropic(model, messages)
        body["stream"] = True
        async with httpx.AsyncClient(timeout=CHAT_TIMEOUT) as client:
            async with client.stream("POST", url, json=body, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:].strip()
                    if payload in ("[DONE]", ""):
                        continue
                    try:
                        event = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    if event.get("type") == "content_block_delta":
                        text = (event.get("delta") or {}).get("text", "")
                        if text:
                            yield _openai_sse_chunk(model, text)
    elif row["id"] == "ollama":
        url = row["base_url"] + row["chat_path"]
        body = _to_ollama_native(model, messages)
        body["stream"] = True
        async with httpx.AsyncClient(timeout=CHAT_TIMEOUT) as client:
            async with client.stream("POST", url, json=body, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    text = line.strip()
                    if not text:
                        continue
                    try:
                        event = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    delta = _ollama_stream_text(event)
                    if delta:
                        yield _openai_sse_chunk(model, delta)
    else:
        url = row["base_url"] + row["chat_path"]
        body = _openai_body(model, messages)
        body["stream"] = True
        async with httpx.AsyncClient(timeout=CHAT_TIMEOUT) as client:
            async with client.stream("POST", url, json=body, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        yield (line + "\n\n").encode("utf-8")
    yield b"data: [DONE]\n\n"


INSTALL_ALLOWLIST = ("ollama",)
INSTALL_TIMEOUT = 600.0

_install_jobs: dict[str, dict[str, Any]] = {}
_install_lock = threading.Lock()


def _set_install_state(engine: str, **fields: Any) -> None:
    with _install_lock:
        job = _install_jobs.setdefault(engine, {"engine": engine, "state": "idle"})
        job.update(fields)


def _run_winget_ollama() -> None:
    import subprocess

    _set_install_state("ollama", state="running", output="")
    try:
        proc = subprocess.run(
            [
                "winget",
                "install",
                "-e",
                "--id",
                "Ollama.Ollama",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--silent",
            ],
            capture_output=True,
            text=True,
            timeout=INSTALL_TIMEOUT,
        )
        tail = (proc.stdout + proc.stderr)[-2000:]
        if proc.returncode == 0:
            _set_install_state("ollama", state="done", output=tail)
        else:
            _set_install_state("ollama", state="error", output=tail or f"exit {proc.returncode}")
    except FileNotFoundError:
        _set_install_state("ollama", state="error", output="winget not found on PATH")
    except Exception as exc:
        _set_install_state("ollama", state="error", output=str(exc)[:500])


def start_install(engine: str) -> dict[str, Any]:
    """Start a fixed-command engine install in the background (allowlisted only)."""
    if engine not in INSTALL_ALLOWLIST:
        allowed = ", ".join(INSTALL_ALLOWLIST)
        raise ValueError(f"Install not supported for '{engine}'. Allowed: {allowed}")
    if sys.platform != "win32":
        raise RuntimeError("One-click install is Windows-only")
    with _install_lock:
        if _install_jobs.get(engine, {}).get("state") == "running":
            return {"engine": engine, "started": False, "reason": "already running"}
    thread = threading.Thread(target=_run_winget_ollama, name="ollama-install", daemon=True)
    thread.start()
    return {"engine": engine, "started": True}


def install_status(engine: str) -> dict[str, Any]:
    if engine not in INSTALL_ALLOWLIST:
        raise ValueError(f"Unknown install engine '{engine}'")
    with _install_lock:
        job = dict(_install_jobs.get(engine, {"engine": engine, "state": "idle"}))
    return job


def onboarding_state() -> dict[str, Any]:
    """Fresh-install starter facts: what exists, what can be installed, best path."""
    clouds = {r["id"]: is_configured(r["id"]) for r in PROVIDERS if r["kind"] == "cloud"}
    return {
        "locals": [
            {"id": r["id"], "label": r["label"], "port": _port_hint(r["base_url"])}
            for r in PROVIDERS
            if r["kind"] == "local"
        ],
        "clouds_configured": [pid for pid, ok in clouds.items() if ok],
        "recommendation": _recommend_path(clouds),
    }


def _port_hint(base_url: str) -> int | None:
    try:
        return int(base_url.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        return None


def _recommend_path(clouds: dict[str, bool]) -> dict[str, str]:
    if any(clouds.values()):
        first = next(pid for pid, ok in clouds.items() if ok)
        return {
            "path": f"cloud:{first}",
            "reason": f"{first} key already configured — chat works immediately.",
        }
    return {
        "path": "cloud:meta",
        "reason": "Cheapest instant path: paste a Meta key (Contributor $0.20/M out). "
        "Free path: install Ollama (section 3 of the llm-guide skill) and come back.",
    }
