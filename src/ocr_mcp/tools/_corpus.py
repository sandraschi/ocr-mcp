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

"""MCP corpus_management handlers (async wrappers around CorpusStore)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from ..core.config import OCRConfig
from ..core.error_handler import ErrorHandler
from ..corpus.store import get_corpus_store

logger = logging.getLogger(__name__)


def _normalize_tags(tags: list[str] | str | None) -> list[str] | None:
    if tags is None:
        return None
    if isinstance(tags, list):
        return [str(t).strip() for t in tags if str(t).strip()]
    parts = [p.strip() for p in str(tags).split(",")]
    return [p for p in parts if p]


async def handle_corpus_op(
    operation: str,
    config: OCRConfig,
    source_path: str | None = None,
    corpus_id: str | None = None,
    title: str | None = None,
    tags: list[str] | str | None = None,
    metadata: dict[str, Any] | None = None,
    query: str | None = None,
    limit: int = 20,
    ocr_text: str | None = None,
    ocr_text_path: str | None = None,
    backend: str | None = None,
    metadata_patch: dict[str, Any] | None = None,
) -> dict[str, Any]:
    store = get_corpus_store(config.corpus_dir)
    op = (operation or "").strip().lower()

    try:
        if op == "register":
            if not source_path:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override="register requires source_path",
                ).to_dict()
            return await asyncio.to_thread(
                store.register,
                source_path,
                title,
                _normalize_tags(tags),
                metadata,
            )

        if op == "update_metadata":
            if not corpus_id:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override="update_metadata requires corpus_id",
                ).to_dict()
            return await asyncio.to_thread(
                store.update_metadata,
                corpus_id,
                title,
                _normalize_tags(tags),
                metadata_patch,
            )

        if op == "get":
            if not corpus_id:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override="get requires corpus_id",
                ).to_dict()
            return await asyncio.to_thread(store.get, corpus_id)

        if op == "search":
            if not query or not str(query).strip():
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override="search requires non-empty query",
                ).to_dict()
            return await asyncio.to_thread(store.search, query, limit)

        if op == "list_recent":
            return await asyncio.to_thread(store.list_recent, limit)

        if op == "attach_ocr_result":
            if not corpus_id:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override="attach_ocr_result requires corpus_id",
                ).to_dict()
            if not ocr_text and not ocr_text_path:
                return ErrorHandler.create_error(
                    "PARAMETERS_INVALID",
                    message_override="attach_ocr_result requires ocr_text or ocr_text_path",
                ).to_dict()
            return await asyncio.to_thread(
                store.attach_ocr_result,
                corpus_id,
                ocr_text,
                ocr_text_path,
                backend,
            )

        valid = "register, update_metadata, get, search, list_recent, attach_ocr_result"
        return ErrorHandler.create_error(
            "PARAMETERS_INVALID",
            message_override=f"Unknown corpus operation: {operation}. Valid: {valid}",
        ).to_dict()
    except Exception as e:
        logger.exception("corpus_management %s failed", op)
        return ErrorHandler.handle_exception(e, context=f"corpus_management_{op}")
