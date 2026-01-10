"""
OCR-MCP: Config
"""

import logging

logger = logging.getLogger(__name__)
"""
OCR-MCP Configuration Management
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file if present
load_dotenv()


class OCRConfig(BaseModel):
    """Configuration for OCR-MCP server."""

    # Cache and model directories
    cache_dir: Path = Field(default_factory=lambda: Path.home() / ".cache" / "ocr-mcp")
    model_cache_dir: Path = Field(
        default_factory=lambda: Path.home() / ".cache" / "ocr-mcp" / "models"
    )

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

    # Mistral OCR API settings
    mistral_api_key: Optional[str] = Field(default=None)
    mistral_base_url: str = Field(default="https://api.mistral.ai/v1")

    # Watch folder settings
    watch_folder_enabled: bool = Field(default=False)
    watch_folder_path: Optional[Path] = Field(default=None)
    watch_folder_output_path: Optional[Path] = Field(default=None)
    watch_folder_interval: int = Field(default=10)

    def __init__(self, **data):
        # Set default values first
        default_cache_dir = Path.home() / ".cache" / "ocr-mcp"

        # Override defaults with environment variables
        data.setdefault(
            "cache_dir", Path(os.getenv("OCR_CACHE_DIR", str(default_cache_dir)))
        )
        data.setdefault("device", os.getenv("OCR_DEVICE", "auto"))
        data.setdefault(
            "max_memory_gb",
            float(os.getenv("OCR_MAX_MEMORY", 0))
            if os.getenv("OCR_MAX_MEMORY")
            else None,
        )
        data.setdefault("default_backend", os.getenv("OCR_DEFAULT_BACKEND", "auto"))
        data.setdefault("batch_size", int(os.getenv("OCR_BATCH_SIZE", 4)))
        data.setdefault("max_concurrent_jobs", int(os.getenv("OCR_MAX_CONCURRENT", 4)))
        data.setdefault("mistral_api_key", os.getenv("MISTRAL_API_KEY"))
        data.setdefault(
            "mistral_base_url",
            os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1"),
        )
        data.setdefault(
            "watch_folder_enabled",
            os.getenv("OCR_WATCH_FOLDER_ENABLED", "false").lower() == "true",
        )
        data.setdefault(
            "watch_folder_path",
            Path(os.getenv("OCR_WATCH_FOLDER_PATH"))
            if os.getenv("OCR_WATCH_FOLDER_PATH")
            else None,
        )
        data.setdefault(
            "watch_folder_output_path",
            Path(os.getenv("OCR_WATCH_FOLDER_OUTPUT"))
            if os.getenv("OCR_WATCH_FOLDER_OUTPUT")
            else None,
        )
        data.setdefault(
            "watch_folder_interval", int(os.getenv("OCR_WATCH_FOLDER_INTERVAL", 10))
        )

        super().__init__(**data)

        # Ensure directories exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
config = OCRConfig()
