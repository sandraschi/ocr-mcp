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

"""Corpus SQLite store (v0)."""

from ocr_mcp.corpus.store import CorpusStore


def test_corpus_register_get_search(tmp_path):
    f = tmp_path / "doc.txt"
    f.write_text("hello corpus", encoding="utf-8")
    store = CorpusStore(tmp_path / "corpus.db")
    reg = store.register(str(f), title="My doc", tags=["a", "b"])
    assert reg["success"] is True
    cid = reg["corpus_id"]
    got = store.get(cid)
    assert got["success"] is True
    assert got["document"]["title"] == "My doc"
    sr = store.search("my doc")
    assert sr["success"] is True
    assert sr["count"] >= 1
