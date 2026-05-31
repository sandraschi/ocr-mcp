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
OCR-MCP Configuration Management
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Load environment variables from .env file if present
load_dotenv()


class OCRConfig(BaseModel):
    """Configuration for OCR-MCP server."""

    # Cache and model directories (platform-aware: use home cache unless OCR_MODEL_DIR set)
    cache_dir: Path = Field(default_factory=lambda: Path.home() / ".cache" / "ocr-mcp")
    model_dir: Path = Field(default_factory=lambda: Path.home() / ".cache" / "ocr-mcp" / "models")
    model_cache_dir: Path = Field(default_factory=lambda: Path.home() / ".cache" / "ocr-mcp" / "models")

    # Device configuration
    device: str = Field(default="auto")  # "auto", "cuda", "cpu"
    max_memory_gb: float | None = Field(default=None)

    # Default backend settings
    default_backend: str = Field(default="auto")  # "auto", "got-ocr", "tesseract", etc.

    # Processing settings
    batch_size: int = Field(default=4)
    max_concurrent_jobs: int = Field(default=4)

    # Backend-specific settings
    got_ocr_model_size: str = Field(default="base")  # "base" or "large"
    tesseract_languages: str = Field(default="eng")
    tesseract_cmd: str | None = Field(default=None)
    # Directory containing pdftoppm (pdf2image); set by POPPLER_PATH or poppler_bootstrap
    poppler_path: str | None = Field(default=None)
    easyocr_languages: list = Field(default_factory=lambda: ["en"])

    # Mistral OCR API settings
    mistral_api_key: str | None = Field(default=None)
    mistral_base_url: str = Field(default="https://api.mistral.ai/v1")

    # Server-side MCP sampling (OpenAI-compatible chat/completions; default Ollama)
    sampling_api_key: str | None = Field(default=None)
    sampling_base_url: str = Field(default="http://127.0.0.1:11434/v1")
    sampling_model: str = Field(default="llama3.2")

    # Local document corpus (SQLite index); see corpus_management MCP tool
    corpus_dir: Path = Field(default_factory=lambda: Path.home() / ".cache" / "ocr-mcp" / "corpus")

    # Watch folder settings
    watch_folder_enabled: bool = Field(default=False)
    watch_folder_path: Path | None = Field(default=None)
    watch_folder_output_path: Path | None = Field(default=None)
    watch_folder_interval: int = Field(default=10)

    def __init__(self, **data):
        # Set default values first
        default_cache_dir = Path.home() / ".cache" / "ocr-mcp"

        # Override defaults with environment variables
        default_model_dir = str(default_cache_dir / "models")
        model_dir_env = os.getenv("OCR_MODEL_DIR")
        data.setdefault("cache_dir", Path(os.getenv("OCR_CACHE_DIR", str(default_cache_dir))))
        data.setdefault("model_dir", Path(model_dir_env) if model_dir_env else Path(default_model_dir))
        data.setdefault("model_cache_dir", Path(model_dir_env) if model_dir_env else Path(default_model_dir))
        data.setdefault("device", os.getenv("OCR_DEVICE", "auto"))
        data.setdefault(
            "max_memory_gb",
            float(os.getenv("OCR_MAX_MEMORY", 0)) if os.getenv("OCR_MAX_MEMORY") else None,
        )
        data.setdefault("default_backend", os.getenv("OCR_DEFAULT_BACKEND", "auto"))
        data.setdefault("batch_size", int(os.getenv("OCR_BATCH_SIZE", 4)))
        data.setdefault("max_concurrent_jobs", int(os.getenv("OCR_MAX_CONCURRENT", 4)))
        data.setdefault("mistral_api_key", os.getenv("MISTRAL_API_KEY"))
        data.setdefault(
            "mistral_base_url",
            os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1"),
        )
        # Local-first: do not auto-bind OPENAI_API_KEY (avoids surprise cloud billing).
        _sk = os.getenv("OCR_SAMPLING_API_KEY")
        if _sk is not None:
            data["sampling_api_key"] = _sk.strip() or None
        elif os.getenv("OCR_SAMPLING_USE_OPENAI_KEY", "").lower() in ("1", "true", "yes"):
            data.setdefault("sampling_api_key", os.getenv("OPENAI_API_KEY"))
        else:
            data.setdefault("sampling_api_key", None)
        data.setdefault(
            "sampling_base_url",
            os.getenv("OCR_SAMPLING_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/"),
        )
        data.setdefault("sampling_model", os.getenv("OCR_SAMPLING_MODEL", "llama3.2"))
        corpus_explicit = "corpus_dir" in data
        corpus_env = os.getenv("OCR_CORPUS_DIR")
        if corpus_env:
            data["corpus_dir"] = Path(corpus_env)
            corpus_explicit = True
        data.setdefault(
            "watch_folder_enabled",
            os.getenv("OCR_WATCH_FOLDER_ENABLED", "false").lower() == "true",
        )
        data.setdefault(
            "watch_folder_path",
            Path(os.getenv("OCR_WATCH_FOLDER_PATH")) if os.getenv("OCR_WATCH_FOLDER_PATH") else None,
        )
        data.setdefault(
            "watch_folder_output_path",
            Path(os.getenv("OCR_WATCH_FOLDER_OUTPUT")) if os.getenv("OCR_WATCH_FOLDER_OUTPUT") else None,
        )
        data.setdefault("watch_folder_interval", int(os.getenv("OCR_WATCH_FOLDER_INTERVAL", 10)))

        # Tesseract specific path detection
        tesseract_env = os.getenv("TESSERACT_CMD")
        if not tesseract_env:
            # Check common Windows paths if on Windows
            import sys

            if sys.platform == "win32":
                common_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                ]
                for p in common_paths:
                    if os.path.exists(p):
                        tesseract_env = p
                        break

        data.setdefault("tesseract_cmd", tesseract_env)

        poppler_env = os.getenv("POPPLER_PATH")
        if poppler_env:
            data.setdefault("poppler_path", poppler_env)

        super().__init__(**data)

        if not corpus_explicit:
            object.__setattr__(self, "corpus_dir", self.cache_dir / "corpus")

        # Ensure directories exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
        self.corpus_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
config = OCRConfig()
