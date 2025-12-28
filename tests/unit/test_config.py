"""
Unit tests for OCR-MCP configuration module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from src.ocr_mcp.core.config import OCRConfig


class TestOCRConfig:
    """Test cases for OCRConfig class."""

    def test_default_initialization(self, temp_dir):
        """Test config initialization with default values."""
        config = OCRConfig()

        assert isinstance(config.cache_dir, Path)
        assert config.device == "cpu"
        assert config.default_backend == "got-ocr"
        assert config.max_concurrent == 3
        assert config.model_cache_size == 2

    def test_custom_initialization(self, temp_dir):
        """Test config initialization with custom values."""
        custom_cache_dir = temp_dir / "custom_cache"
        config = OCRConfig(
            cache_dir=custom_cache_dir,
            device="cuda",
            default_backend="deepseek-ocr",
            max_concurrent=5,
            model_cache_size=4
        )

        assert config.cache_dir == custom_cache_dir
        assert config.device == "cuda"
        assert config.default_backend == "deepseek-ocr"
        assert config.max_concurrent == 5
        assert config.model_cache_size == 4

    def test_cache_dir_creation(self, temp_dir):
        """Test that cache directory is created if it doesn't exist."""
        cache_dir = temp_dir / "new_cache_dir"
        assert not cache_dir.exists()

        config = OCRConfig(cache_dir=cache_dir)

        # Directory should be created during initialization
        assert cache_dir.exists()
        assert cache_dir.is_dir()

    def test_cache_dir_string_conversion(self, temp_dir):
        """Test that string paths are converted to Path objects."""
        cache_dir_str = str(temp_dir / "string_cache")
        config = OCRConfig(cache_dir=cache_dir_str)

        assert isinstance(config.cache_dir, Path)
        assert config.cache_dir == Path(cache_dir_str)

    def test_device_validation(self):
        """Test device parameter validation."""
        # Valid devices
        config_cpu = OCRConfig(device="cpu")
        assert config_cpu.device == "cpu"

        config_cuda = OCRConfig(device="cuda")
        assert config_cuda.device == "cuda"

    def test_backend_validation(self):
        """Test default backend validation."""
        valid_backends = [
            "deepseek-ocr", "florence-2", "dots-ocr",
            "pp-ocrv5", "qwen-image-layered", "got-ocr",
            "tesseract", "easyocr", "auto"
        ]

        for backend in valid_backends:
            config = OCRConfig(default_backend=backend)
            assert config.default_backend == backend

    def test_max_concurrent_validation(self):
        """Test max_concurrent parameter validation."""
        # Valid values
        config = OCRConfig(max_concurrent=1)
        assert config.max_concurrent == 1

        config = OCRConfig(max_concurrent=10)
        assert config.max_concurrent == 10

        # Should not raise for reasonable values
        config = OCRConfig(max_concurrent=0)  # Edge case
        assert config.max_concurrent == 0

    def test_model_cache_size_validation(self):
        """Test model_cache_size parameter validation."""
        config = OCRConfig(model_cache_size=1)
        assert config.model_cache_size == 1

        config = OCRConfig(model_cache_size=10)
        assert config.model_cache_size == 10

    def test_config_equality(self):
        """Test config object equality."""
        config1 = OCRConfig(cache_dir=Path("/tmp/cache1"), device="cpu")
        config2 = OCRConfig(cache_dir=Path("/tmp/cache1"), device="cpu")
        config3 = OCRConfig(cache_dir=Path("/tmp/cache2"), device="cpu")

        # Should be equal if all fields match
        assert config1.cache_dir == config2.cache_dir
        assert config1.device == config2.device
        assert config1.default_backend == config2.default_backend

        # Different cache dir should not be equal
        assert config1.cache_dir != config3.cache_dir

    def test_config_immutability(self):
        """Test that config is effectively immutable after creation."""
        config = OCRConfig()

        # Store original values
        original_cache_dir = config.cache_dir
        original_device = config.device

        # Config should not allow modification
        with pytest.raises(AttributeError):
            config.device = "cuda"

        with pytest.raises(AttributeError):
            config.cache_dir = Path("/new/path")

        # Values should remain unchanged
        assert config.device == original_device
        assert config.cache_dir == original_cache_dir

    @patch.dict("os.environ", {"OCR_CACHE_DIR": "/env/cache"})
    def test_environment_override_cache_dir(self):
        """Test that environment variables can override defaults."""
        # Note: In real implementation, config could read from env
        # This test documents the intended behavior
        config = OCRConfig()

        # Currently, env vars are not automatically read
        # This test ensures the config doesn't break with env vars set
        assert isinstance(config.cache_dir, Path)

    def test_config_repr(self):
        """Test string representation of config."""
        config = OCRConfig(device="cuda", default_backend="deepseek-ocr")

        repr_str = repr(config)
        assert "OCRConfig" in repr_str
        assert "cuda" in repr_str
        assert "deepseek-ocr" in repr_str

    def test_config_properties_access(self):
        """Test that all config properties are accessible."""
        config = OCRConfig()

        # All properties should be accessible
        assert hasattr(config, 'cache_dir')
        assert hasattr(config, 'device')
        assert hasattr(config, 'default_backend')
        assert hasattr(config, 'max_concurrent')
        assert hasattr(config, 'model_cache_size')

        # All should have reasonable values
        assert isinstance(config.cache_dir, Path)
        assert isinstance(config.device, str)
        assert isinstance(config.default_backend, str)
        assert isinstance(config.max_concurrent, int)
        assert isinstance(config.model_cache_size, int)

    def test_cache_dir_permissions(self, temp_dir):
        """Test cache directory permissions and writability."""
        cache_dir = temp_dir / "test_cache"
        config = OCRConfig(cache_dir=cache_dir)

        # Directory should be writable
        test_file = cache_dir / "test.txt"
        test_file.write_text("test")
        assert test_file.exists()
        assert test_file.read_text() == "test"

        # Clean up
        test_file.unlink()

    def test_config_serialization(self):
        """Test that config can be serialized/deserialized."""
        config = OCRConfig(
            device="cuda",
            default_backend="florence-2",
            max_concurrent=5
        )

        # Convert to dict (manual serialization)
        config_dict = {
            "cache_dir": str(config.cache_dir),
            "device": config.device,
            "default_backend": config.default_backend,
            "max_concurrent": config.max_concurrent,
            "model_cache_size": config.model_cache_size
        }

        # Create new config from dict
        new_config = OCRConfig(**{k: v for k, v in config_dict.items() if k != "cache_dir"})
        new_config = OCRConfig(
            cache_dir=Path(config_dict["cache_dir"]),
            device=config_dict["device"],
            default_backend=config_dict["default_backend"],
            max_concurrent=config_dict["max_concurrent"],
            model_cache_size=config_dict["model_cache_size"]
        )

        # Should be equivalent
        assert new_config.device == config.device
        assert new_config.default_backend == config.default_backend
        assert new_config.max_concurrent == config.max_concurrent
        assert new_config.model_cache_size == config.model_cache_size






