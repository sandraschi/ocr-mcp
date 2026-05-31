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
SQLite-backed document corpus (v0).

Stores metadata + optional OCR excerpt/path; does not duplicate large binaries by default.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_STORE_LOCK = threading.Lock()
_STORES: dict[str, CorpusStore] = {}


def _utc_ts() -> float:
    return time.time()


def _file_sha256(path: Path, max_bytes: int = 50 * 1024 * 1024) -> str | None:
    try:
        h = hashlib.sha256()
        total = 0
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                total += len(chunk)
                if total > max_bytes:
                    h.update(chunk[: max_bytes - (total - len(chunk))])
                    break
                h.update(chunk)
        return h.hexdigest()
    except OSError as e:
        logger.debug("hash failed %s: %s", path, e)
        return None


class CorpusStore:
    """Thread-safe SQLite corpus."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn_lock = threading.Lock()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._conn_lock:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS corpus_documents (
                        id TEXT PRIMARY KEY,
                        source_path TEXT NOT NULL,
                        content_hash TEXT,
                        title TEXT,
                        tags TEXT,
                        ocr_text_path TEXT,
                        ocr_excerpt TEXT,
                        backend TEXT,
                        metadata_json TEXT,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    )
                    """
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_corpus_created ON corpus_documents(created_at DESC)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_corpus_path ON corpus_documents(source_path)")
                conn.commit()
            finally:
                conn.close()

    def register(
        self,
        source_path: str,
        title: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        p = Path(source_path).expanduser()
        if not p.is_file():
            return {"success": False, "error": f"Not a file or missing: {source_path}"}
        resolved = str(p.resolve())
        chash = _file_sha256(p)
        cid = str(uuid.uuid4())
        now = _utc_ts()
        tag_json = json.dumps(tags or [])
        meta_json = json.dumps(metadata or {}, default=str)
        ttl = title or p.name
        with self._conn_lock:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    INSERT INTO corpus_documents (
                        id, source_path, content_hash, title, tags,
                        ocr_text_path, ocr_excerpt, backend, metadata_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, ?, ?, ?)
                    """,
                    (cid, resolved, chash, ttl, tag_json, meta_json, now, now),
                )
                conn.commit()
            finally:
                conn.close()
        return {
            "success": True,
            "corpus_id": cid,
            "source_path": resolved,
            "content_hash": chash,
            "title": ttl,
        }

    def update_metadata(
        self,
        corpus_id: str,
        title: str | None = None,
        tags: list[str] | None = None,
        metadata_patch: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self._conn_lock:
            conn = self._connect()
            try:
                row = conn.execute("SELECT * FROM corpus_documents WHERE id = ?", (corpus_id,)).fetchone()
                if not row:
                    return {"success": False, "error": f"Unknown corpus_id: {corpus_id}"}
                d = dict(row)
                new_title = title if title is not None else d["title"]
                new_tags = json.dumps(tags) if tags is not None else d["tags"]
                meta = json.loads(d["metadata_json"] or "{}")
                if metadata_patch:
                    meta.update(metadata_patch)
                new_meta = json.dumps(meta, default=str)
                now = _utc_ts()
                conn.execute(
                    """
                    UPDATE corpus_documents
                    SET title = ?, tags = ?, metadata_json = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (new_title, new_tags, new_meta, now, corpus_id),
                )
                conn.commit()
            finally:
                conn.close()
        return {"success": True, "corpus_id": corpus_id}

    def get(self, corpus_id: str) -> dict[str, Any]:
        with self._conn_lock:
            conn = self._connect()
            try:
                row = conn.execute("SELECT * FROM corpus_documents WHERE id = ?", (corpus_id,)).fetchone()
            finally:
                conn.close()
        if not row:
            return {"success": False, "error": f"Unknown corpus_id: {corpus_id}"}
        d = dict(row)
        d["tags"] = json.loads(d["tags"] or "[]")
        d["metadata"] = json.loads(d["metadata_json"] or "{}")
        del d["metadata_json"]
        return {"success": True, "document": d}

    def search(self, query: str, limit: int = 20) -> dict[str, Any]:
        q = f"%{query.strip().lower()}%"
        lim = max(1, min(limit, 200))
        with self._conn_lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    """
                    SELECT id, source_path, title, tags, ocr_excerpt, backend, created_at
                    FROM corpus_documents
                    WHERE lower(title) LIKE ?
                       OR lower(source_path) LIKE ?
                       OR lower(COALESCE(ocr_excerpt,'')) LIKE ?
                       OR lower(tags) LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (q, q, q, q, lim),
                ).fetchall()
            finally:
                conn.close()
        hits = [dict(r) for r in rows]
        return {"success": True, "count": len(hits), "results": hits}

    def list_recent(self, limit: int = 20) -> dict[str, Any]:
        lim = max(1, min(limit, 200))
        with self._conn_lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    """
                    SELECT id, source_path, title, tags, backend, created_at
                    FROM corpus_documents
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (lim,),
                ).fetchall()
            finally:
                conn.close()
        out = []
        for r in rows:
            d = dict(r)
            d["tags"] = json.loads(d["tags"] or "[]")
            out.append(d)
        return {"success": True, "count": len(out), "results": out}

    def attach_ocr_result(
        self,
        corpus_id: str,
        ocr_text: str | None = None,
        ocr_text_path: str | None = None,
        backend: str | None = None,
        excerpt_max: int = 2000,
    ) -> dict[str, Any]:
        excerpt = None
        if ocr_text:
            excerpt = ocr_text[:excerpt_max]
        elif ocr_text_path and Path(ocr_text_path).is_file():
            try:
                excerpt = Path(ocr_text_path).read_text(encoding="utf-8", errors="replace")[:excerpt_max]
            except OSError:
                excerpt = None
        now = _utc_ts()
        with self._conn_lock:
            conn = self._connect()
            try:
                row = conn.execute("SELECT id FROM corpus_documents WHERE id = ?", (corpus_id,)).fetchone()
                if not row:
                    return {"success": False, "error": f"Unknown corpus_id: {corpus_id}"}
                conn.execute(
                    """
                    UPDATE corpus_documents
                    SET ocr_text_path = ?, ocr_excerpt = ?, backend = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (ocr_text_path, excerpt, backend, now, corpus_id),
                )
                conn.commit()
            finally:
                conn.close()
        return {"success": True, "corpus_id": corpus_id}


def get_corpus_store(corpus_dir: Path) -> CorpusStore:
    """Singleton per resolved corpus directory."""
    key = str(corpus_dir.resolve())
    with _STORE_LOCK:
        if key not in _STORES:
            _STORES[key] = CorpusStore(corpus_dir / "corpus.db")
        return _STORES[key]
