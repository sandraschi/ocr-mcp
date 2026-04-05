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

"""Tests for MCP workflow source_dir expansion and corpus config alignment."""


from ocr_mcp.core.config import OCRConfig
from ocr_mcp.tools._workflow import expand_source_dir_to_document_paths


def test_expand_source_missing_returns_none():
    assert expand_source_dir_to_document_paths(None) is None
    assert expand_source_dir_to_document_paths("") is None
    assert expand_source_dir_to_document_paths("   ") is None


def test_expand_nonexistent_returns_empty(tmp_path):
    assert expand_source_dir_to_document_paths(str(tmp_path / "nope")) == []


def test_expand_file_pdf(tmp_path):
    f = tmp_path / "a.pdf"
    f.write_bytes(b"%PDF-1.4")
    paths = expand_source_dir_to_document_paths(str(f))
    assert paths == [str(f.resolve())]


def test_expand_dir_two_images(tmp_path):
    (tmp_path / "1.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (tmp_path / "skip.txt").write_text("no")
    (tmp_path / "2.jpg").write_bytes(b"\xff\xd8\xff")
    paths = expand_source_dir_to_document_paths(str(tmp_path))
    assert len(paths) == 2
    assert all(p.endswith(("1.png", "2.jpg")) for p in paths)


def test_corpus_dir_nested_under_cache_dir(tmp_path):
    cache = tmp_path / "c"
    cfg = OCRConfig(cache_dir=cache, device="cpu")
    assert cfg.corpus_dir == cache / "corpus"
    assert cfg.corpus_dir.is_dir()
