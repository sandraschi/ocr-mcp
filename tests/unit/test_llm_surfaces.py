"""
Unit tests for fleet LLM surfaces (vends Phase 2) + Apps hub wiring (Phase 1).

Covers the SETTINGS_LLM.md card-header contract against backend/app.py:
settings get/save, key delete, providers/models/loaded/unload/gpus,
onboarding, install allowlist, chat validation, and the standard
/api/apps* routes. LLM file state is isolated per-test via
OCR_LLM_DATA_DIR -> tmp_path (llm_providers resolves paths at call time).

Imports ``backend.app`` (full module init). Marked ``webapp``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.webapp


@pytest.fixture(scope="module")
def webapp_module():
    """Import webapp once per module (heavy: managers, bootstrap)."""
    import backend.app as app_mod

    return app_mod


@pytest.fixture
def llm_env(monkeypatch, tmp_path: Path):
    """Isolate LLM settings + keystore in tmp (never the real cache dir)."""
    monkeypatch.setenv("OCR_LLM_DATA_DIR", str(tmp_path / "llmtest"))
    return tmp_path / "llmtest"


@pytest.fixture
def client(webapp_module):
    from fastapi.testclient import TestClient

    from backend.app import app

    return TestClient(app)


# --- settings get/save ---


def test_llm_settings_get_shape(client, llm_env):
    r = client.get("/api/settings/llm")
    assert r.status_code == 200
    data = r.json()
    assert data["provider"] == "ollama"
    assert data["endpoint"] == "http://localhost:11434"
    assert data["model"] == ""
    assert "api_key" not in data
    assert isinstance(data["keys_configured"], dict)


def test_llm_settings_save_roundtrip(client, llm_env):
    r = client.post(
        "/api/settings/llm",
        json={"provider": "lmstudio", "endpoint": "http://localhost:1234", "model": ""},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["provider"] == "lmstudio"
    assert body["key_saved"] is False

    stored = json.loads((llm_env / "llm_settings.json").read_text(encoding="utf-8"))
    assert stored == {"provider": "lmstudio", "endpoint": "http://localhost:1234", "model": ""}

    g = client.get("/api/settings/llm")
    assert g.json()["provider"] == "lmstudio"


def test_llm_settings_save_unknown_provider_400(client, llm_env):
    r = client.post("/api/settings/llm", json={"provider": "nope", "model": ""})
    assert r.status_code == 400


def test_llm_settings_save_key_for_local_400(client, llm_env):
    r = client.post("/api/settings/llm", json={"provider": "ollama", "model": "", "api_key": "x"})
    assert r.status_code == 400


# --- key save/clear ---


def test_llm_cloud_key_save_and_clear(client, llm_env):
    r = client.post(
        "/api/settings/llm",
        json={"provider": "openai", "model": "", "api_key": "sk-test-fake"},
    )
    assert r.status_code == 200
    assert r.json()["key_saved"] is True

    g = client.get("/api/settings/llm")
    assert g.json()["keys_configured"]["openai"] is True
    assert "sk-test-fake" not in g.text

    d = client.delete("/api/settings/llm/key", params={"provider": "openai"})
    assert d.status_code == 200
    assert d.json()["removed"] is True

    g2 = client.get("/api/settings/llm")
    assert g2.json()["keys_configured"]["openai"] is False


def test_llm_key_delete_unknown_provider_400(client, llm_env):
    r = client.delete("/api/settings/llm/key", params={"provider": "nope"})
    assert r.status_code == 400


# --- providers / models / loaded / unload / gpus ---


def test_llm_providers_shape(client, llm_env):
    r = client.get("/api/llm/providers")
    assert r.status_code == 200
    providers = r.json()["providers"]
    ids = {p["id"] for p in providers}
    assert {"ollama", "lmstudio", "openai", "anthropic"} <= ids
    for p in providers:
        assert set(p) >= {"id", "label", "kind", "base_url", "needs_key", "key_env", "configured"}
        assert "sk-test" not in json.dumps(p)
    clouds = [p for p in providers if p["kind"] == "cloud"]
    assert clouds and all(p["needs_key"] for p in clouds)


def test_llm_models_unknown_provider_400(client, llm_env):
    assert client.get("/api/llm/models", params={"provider": "nope"}).status_code == 400


def test_llm_models_cloud_curated_without_key(client, llm_env, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    r = client.get("/api/llm/models", params={"provider": "openai"})
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "openai"
    assert body["source"] == "curated"
    assert len(body["models"]) > 0


def test_llm_loaded_non_ollama_400(client, llm_env):
    assert client.get("/api/llm/loaded", params={"provider": "lmstudio"}).status_code == 400


def test_llm_loaded_ollama_shape(client, llm_env):
    r = client.get("/api/llm/loaded", params={"provider": "ollama"})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert isinstance(body["engine"], bool)
    assert isinstance(body["models"], list)


def test_llm_unload_non_ollama_400(client, llm_env):
    r = client.post("/api/llm/unload", json={"provider": "lmstudio"})
    assert r.status_code == 400


def test_llm_gpus_shape(client, llm_env):
    r = client.get("/api/llm/gpus")
    assert r.status_code == 200
    assert isinstance(r.json()["gpus"], list)


# --- onboarding / install ---


def test_llm_onboarding_shape(client, llm_env):
    r = client.get("/api/llm/onboarding")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["locals"], list)
    assert isinstance(body["clouds_configured"], list)
    assert set(body["recommendation"]) >= {"path", "reason"}


def test_llm_install_allowlist(client, llm_env):
    r = client.post("/api/llm/install", json={"engine": "evil-engine"})
    assert r.status_code == 400
    r2 = client.get("/api/llm/install/status", params={"engine": "evil-engine"})
    assert r2.status_code == 400


def test_llm_install_status_idle(client, llm_env):
    r = client.get("/api/llm/install/status", params={"engine": "ollama"})
    assert r.status_code == 200
    assert r.json()["state"] == "idle"


# --- chat validation (no live engine needed) ---


def test_llm_chat_empty_model_rejected(client, llm_env):
    r = client.post(
        "/api/llm/chat", json={"provider": "ollama", "model": "", "messages": [{"role": "user", "content": "hi"}]}
    )
    assert r.status_code in (400, 422)


def test_llm_chat_unknown_provider_400(client, llm_env):
    r = client.post(
        "/api/llm/chat",
        json={"provider": "nope", "model": "x", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert r.status_code == 400


def test_llm_chat_stream_unknown_provider_400(client, llm_env):
    r = client.post(
        "/api/llm/chat/stream",
        json={"provider": "nope", "model": "x", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert r.status_code == 400


# --- Apps hub (Phase 1 wiring) ---


def test_apps_hub_lists_registry(client):
    r = client.get("/api/apps")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["apps"], list)
    assert len(body["apps"]) > 0
    assert body["fleet_total"] >= len(body["apps"])


def test_apps_health_dead_port(client):
    r = client.get("/api/apps/health", params={"port": 9})
    assert r.status_code == 200
    body = r.json()
    assert body["port"] == 9
    assert body["alive"] is False


def test_apps_ensure_unknown_fails_safe(client):
    r = client.post("/api/apps/ensure", json={"id": "no-such-app-xyz", "port": 9})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert body.get("alive", False) is False


# --- llm_ops MCP tool (no live engine needed) ---


class _FakeFastMCP:
    def __init__(self):
        self.fns = {}

    def tool(self, *args, **kwargs):
        def deco(fn):
            self.fns[fn.__name__] = fn
            return fn

        return deco


@pytest.fixture(scope="module")
def llm_ops_fn():
    from ocr_mcp.tools.llm_ops import register_llm_ops_tool

    fake = _FakeFastMCP()
    register_llm_ops_tool(fake)
    return fake.fns["llm_ops"]


@pytest.mark.asyncio
async def test_llm_ops_vram(llm_ops_fn):
    out = await llm_ops_fn(operation="vram")
    assert out["success"] is True
    assert isinstance(out["gpus"], list)


@pytest.mark.asyncio
async def test_llm_ops_unknown_operation(llm_ops_fn):
    out = await llm_ops_fn(operation="bogus")
    assert out["success"] is False


@pytest.mark.asyncio
async def test_llm_ops_switch_needs_model(llm_ops_fn):
    out = await llm_ops_fn(operation="switch_model", model="  ")
    assert out["success"] is False


@pytest.mark.asyncio
async def test_llm_ops_list_models_curated(llm_ops_fn, llm_env, monkeypatch):
    monkeypatch.setenv("OCR_LLM_DATA_DIR", str(llm_env))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    out = await llm_ops_fn(operation="list_models", provider="openai")
    assert out["success"] is True
    assert len(out["models"]) > 0
