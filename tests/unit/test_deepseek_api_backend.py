"""DeepSeek cloud OCR backend. No network."""

from pathlib import Path

import pytest

from ocr_mcp.backends.deepseek_api_backend import DeepSeekApiOcrBackend, parse_ocr_body
from ocr_mcp.core.config import OCRConfig


def test_parse_ocr_body_strips_keepalive_and_marks_truncation():
    body = '\n\n{"id":"ocr-1","purpose":"text_recognition","page_count":2,"pages":[{"index":0,"text":"Hello","finish_reason":"stop"},{"index":1,"text":"Cut","finish_reason":"length"}]}'
    parsed = parse_ocr_body(body)
    assert "Hello" in parsed["text"]
    assert "[page truncated]" in parsed["text"]
    assert parsed["truncated_pages"] == [1]
    assert parsed["page_count"] == 2


def test_backend_is_unavailable_without_a_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    backend = DeepSeekApiOcrBackend(OCRConfig(deepseek_api_key=None))
    assert backend.is_available() is False


@pytest.mark.asyncio
async def test_process_image_posts_purpose_and_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    sample = tmp_path / "note.png"
    sample.write_bytes(b"png")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    backend = DeepSeekApiOcrBackend(OCRConfig(deepseek_api_key="test-key"))
    seen: dict[str, object] = {}

    class FakeResponse:
        status_code = 200
        text = '{"pages":[{"index":0,"text":"Page one","finish_reason":"stop"}],"page_count":1,"purpose":"text_recognition","id":"ocr-9"}'

    class FakeClient:
        def __init__(self, *args, **kwargs):
            seen["timeout"] = kwargs.get("timeout")

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, headers=None, data=None, files=None):
            seen["url"] = url
            seen["auth"] = headers.get("Authorization") if headers else None
            seen["purpose"] = data.get("purpose") if data else None
            seen["filename"] = files["file"][0] if files else None
            return FakeResponse()

    monkeypatch.setattr("ocr_mcp.backends.deepseek_api_backend.httpx.AsyncClient", FakeClient)
    result = await backend.process_image(str(sample))
    assert result["success"] is True
    assert "Page one" in result["text"]
    assert seen["url"] == "https://api.deepseek.com/v1/tools/ocr"
    assert seen["auth"] == "Bearer test-key"
    assert seen["purpose"] == "text_recognition"
    assert seen["filename"] == "note.png"
    assert result["metadata"]["pages"] == 1
