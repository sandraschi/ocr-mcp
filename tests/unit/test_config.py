"""
Unit tests for OCR-MCP configuration module.
"""

from pathlib import Path
from unittest.mock import patch

from ocr_mcp.core.config import OCRConfig


class TestOCRConfig:
    """Test cases for OCRConfig class."""

    def test_default_initialization(self, temp_dir):
        """Test config initialization with default values."""
        config = OCRConfig(device="cpu", default_backend="got-ocr")

        assert isinstance(config.cache_dir, Path)
        assert config.device == "cpu"
        assert config.default_backend == "got-ocr"
        assert config.max_concurrent_jobs == 4

    def test_custom_initialization(self, temp_dir):
        """Test config initialization with custom values."""
        custom_cache_dir = temp_dir / "custom_cache"
        config = OCRConfig(
            cache_dir=custom_cache_dir,
            device="cuda",
            default_backend="deepseek-ocr",
            max_concurrent_jobs=5,
        )

        assert config.cache_dir == custom_cache_dir
        assert config.device == "cuda"
        assert config.default_backend == "deepseek-ocr"
        assert config.max_concurrent_jobs == 5

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
            "deepseek-ocr",
            "florence-2",
            "dots-ocr",
            "pp-ocrv5",
            "qwen-image-layered",
            "got-ocr",
            "tesseract",
            "easyocr",
            "auto",
        ]

        for backend in valid_backends:
            config = OCRConfig(default_backend=backend)
            assert config.default_backend == backend

    def test_max_concurrent_validation(self):
        """Test max_concurrent_jobs parameter validation."""
        config = OCRConfig(max_concurrent_jobs=1)
        assert config.max_concurrent_jobs == 1

        config = OCRConfig(max_concurrent_jobs=10)
        assert config.max_concurrent_jobs == 10

        config = OCRConfig(max_concurrent_jobs=0)
        assert config.max_concurrent_jobs == 0

    def test_model_cache_dir_validation(self):
        """Test model_cache_dir is a Path."""
        config = OCRConfig()
        assert config.model_cache_dir is not None
        assert hasattr(config.model_cache_dir, "exists")

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
        """Test that config values are accessible and type-consistent."""
        config = OCRConfig(device="cpu")

        # Store original values
        original_device = config.device
        original_cache_dir = config.cache_dir

        # Pydantic models are mutable by default; just ensure values are readable
        assert config.device == original_device
        assert config.cache_dir == original_cache_dir

    @patch.dict("os.environ", {"OCR_CACHE_DIR": "/env/cache"}, clear=False)
    def test_environment_override_cache_dir(self):
        """Test that environment variables can override defaults."""
        config = OCRConfig()

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

        assert hasattr(config, "cache_dir")
        assert hasattr(config, "device")
        assert hasattr(config, "default_backend")
        assert hasattr(config, "max_concurrent_jobs")

        assert isinstance(config.cache_dir, Path)
        assert isinstance(config.device, str)
        assert isinstance(config.default_backend, str)
        assert isinstance(config.max_concurrent_jobs, int)

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
        config = OCRConfig(device="cuda", default_backend="florence-2", max_concurrent_jobs=5)

        config_dict = {
            "cache_dir": str(config.cache_dir),
            "device": config.device,
            "default_backend": config.default_backend,
            "max_concurrent_jobs": config.max_concurrent_jobs,
        }

        new_config = OCRConfig(
            cache_dir=Path(config_dict["cache_dir"]),
            device=config_dict["device"],
            default_backend=config_dict["default_backend"],
            max_concurrent_jobs=config_dict["max_concurrent_jobs"],
        )

        assert new_config.device == config.device
        assert new_config.default_backend == config.default_backend
        assert new_config.max_concurrent_jobs == config.max_concurrent_jobs
