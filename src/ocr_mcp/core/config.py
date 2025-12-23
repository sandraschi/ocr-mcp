"""
OCR-MCP Configuration Management
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class OCRConfig(BaseModel):
    """Configuration for OCR-MCP server."""

    # Cache and model directories
    cache_dir: Path = Field(default_factory=lambda: Path.home() / ".cache" / "ocr-mcp")
    model_cache_dir: Path = Field(default_factory=lambda: Path.home() / ".cache" / "ocr-mcp" / "models")

    # Device configuration
    device: str = Field(default="auto")  # "auto", "cuda", "cpu"
    max_memory_gb: Optional[float] = Field(default=None)

    # Default backend settings
    default_backend: str = Field(default="auto")  # "auto", "got-ocr", "tesseract", etc.

    # Processing settings
    batch_size: int = Field(default=4)
    max_concurrent_jobs: int = Field(default=4)

    # Backend-specific settings
    got_ocr_model_size: str = Field(default="base")  # "base" or "large"
    tesseract_languages: str = Field(default="eng")
    easyocr_languages: list = Field(default_factory=lambda: ["en"])

    def __init__(self, **data):
        # Set default values first
        default_cache_dir = Path.home() / ".cache" / "ocr-mcp"

        # Override defaults with environment variables
        data.setdefault("cache_dir", Path(os.getenv("OCR_CACHE_DIR", str(default_cache_dir))))
        data.setdefault("device", os.getenv("OCR_DEVICE", "auto"))
        data.setdefault("max_memory_gb", float(os.getenv("OCR_MAX_MEMORY", 0)) if os.getenv("OCR_MAX_MEMORY") else None)
        data.setdefault("default_backend", os.getenv("OCR_DEFAULT_BACKEND", "auto"))
        data.setdefault("batch_size", int(os.getenv("OCR_BATCH_SIZE", 4)))
        data.setdefault("max_concurrent_jobs", int(os.getenv("OCR_MAX_CONCURRENT", 4)))

        super().__init__(**data)

        # Ensure directories exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
config = OCRConfig()
