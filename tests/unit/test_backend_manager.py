"""
Unit tests for OCR-MCP backend manager module.
"""

import pytest
from unittest.mock import Mock, patch

from src.ocr_mcp.core.backend_manager import BackendManager, OCRBackend


class TestOCRBackend:
    """Test cases for the base OCRBackend class."""

    def test_backend_initialization(self, config):
        """Test backend initialization."""
        backend = OCRBackend("test-backend", config)

        assert backend.name == "test-backend"
        assert backend.config == config
        assert not backend.is_available()

    def test_backend_get_capabilities(self, config):
        """Test backend capabilities retrieval."""
        backend = OCRBackend("test-backend", config)

        capabilities = backend.get_capabilities()

        assert capabilities["name"] == "test-backend"
        assert not capabilities["available"]
        assert "modes" in capabilities
        assert "languages" in capabilities
        assert "gpu_support" in capabilities

    def test_backend_process_image_not_implemented(self, config):
        """Test that process_image raises NotImplementedError."""
        backend = OCRBackend("test-backend", config)

        with pytest.raises(NotImplementedError):
            await backend.process_image("fake_path")


class TestBackendManager:
    """Test cases for BackendManager class."""

    def test_manager_initialization(self, config):
        """Test backend manager initialization."""
        manager = BackendManager(config)

        assert manager.config == config
        assert isinstance(manager.backends, dict)
        assert hasattr(manager, 'scanner_manager')
        assert hasattr(manager, 'document_processor')

    def test_get_available_backends_empty(self, config):
        """Test getting available backends when none are available."""
        with patch('src.ocr_mcp.core.backend_manager.scanner_manager') as mock_scanner, \
             patch('src.ocr_mcp.core.backend_manager.document_processor') as mock_processor:

            mock_scanner.is_available.return_value = False
            mock_processor.is_available.return_value = False

            manager = BackendManager(config)

            # Mock all backends as unavailable
            for backend in manager.backends.values():
                backend._available = False

            available = manager.get_available_backends()
            assert available == []

    def test_get_backend_by_name(self, config):
        """Test retrieving backend by name."""
        manager = BackendManager(config)

        # Test existing backend
        backend = manager.get_backend("deepseek-ocr")
        assert backend is not None
        assert backend.name == "deepseek-ocr"

        # Test non-existing backend
        backend = manager.get_backend("nonexistent-backend")
        assert backend is None

    def test_select_backend_auto_mode(self, config):
        """Test automatic backend selection."""
        manager = BackendManager(config)

        # Mock backends with different availability
        mock_backend1 = Mock()
        mock_backend1.name = "backend1"
        mock_backend1.is_available.return_value = False

        mock_backend2 = Mock()
        mock_backend2.name = "backend2"
        mock_backend2.is_available.return_value = True

        manager.backends = {
            "backend1": mock_backend1,
            "backend2": mock_backend2
        }

        # Should select first available backend
        selected = manager.select_backend("auto")
        assert selected == mock_backend2

    def test_select_backend_specific_available(self, config):
        """Test selecting specific available backend."""
        manager = BackendManager(config)

        mock_backend = Mock()
        mock_backend.name = "test-backend"
        mock_backend.is_available.return_value = True

        manager.backends = {"test-backend": mock_backend}

        selected = manager.select_backend("test-backend")
        assert selected == mock_backend

    def test_select_backend_specific_unavailable(self, config):
        """Test selecting specific unavailable backend."""
        manager = BackendManager(config)

        mock_backend = Mock()
        mock_backend.name = "test-backend"
        mock_backend.is_available.return_value = False

        manager.backends = {"test-backend": mock_backend}

        # Should fall back to auto-selection
        selected = manager.select_backend("test-backend")
        # Since no backends are available in this test, should return None
        assert selected is None

    def test_select_backend_unknown_name(self, config):
        """Test selecting unknown backend name."""
        manager = BackendManager(config)

        selected = manager.select_backend("unknown-backend")
        assert selected is None

    @pytest.mark.asyncio
    async def test_process_with_backend_success(self, config, sample_image_path):
        """Test successful processing with a backend."""
        manager = BackendManager(config)

        mock_backend = Mock()
        mock_backend.name = "test-backend"
        mock_backend.is_available.return_value = True
        mock_backend.process_image = Mock(return_value={
            "success": True,
            "text": "Test OCR result",
            "backend": "test-backend"
        })

        manager.backends = {"test-backend": mock_backend}

        result = await manager.process_with_backend(
            "test-backend",
            str(sample_image_path),
            mode="text"
        )

        assert result["success"] is True
        assert result["text"] == "Test OCR result"
        assert result["backend_used"] == "test-backend"
        mock_backend.process_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_with_backend_failure(self, config, sample_image_path):
        """Test processing failure with a backend."""
        manager = BackendManager(config)

        mock_backend = Mock()
        mock_backend.name = "test-backend"
        mock_backend.is_available.return_value = True
        mock_backend.process_image = Mock(side_effect=Exception("Processing failed"))

        manager.backends = {"test-backend": mock_backend}

        result = await manager.process_with_backend(
            "test-backend",
            str(sample_image_path)
        )

        assert result["success"] is False
        assert "error" in result
        assert "backend_used" in result

    @pytest.mark.asyncio
    async def test_process_with_backend_unavailable(self, config, sample_image_path):
        """Test processing with unavailable backend."""
        manager = BackendManager(config)

        result = await manager.process_with_backend(
            "nonexistent-backend",
            str(sample_image_path)
        )

        assert result["success"] is False
        assert "error" in result
        assert "available_backends" in result

    def test_preference_order_auto_selection(self, config):
        """Test that auto-selection follows preference order."""
        manager = BackendManager(config)

        # Create mocks for all backends in preference order
        backends = {}
        preference_order = [
            "deepseek-ocr", "florence-2", "dots-ocr", "pp-ocrv5",
            "qwen-image-layered", "got-ocr", "tesseract", "easyocr"
        ]

        # Make all backends available
        for name in preference_order:
            mock_backend = Mock()
            mock_backend.name = name
            mock_backend.is_available.return_value = True
            backends[name] = mock_backend

        manager.backends = backends

        # Should select first in preference order
        selected = manager.select_backend("auto")
        assert selected.name == "deepseek-ocr"

    def test_fallback_selection_when_preferred_unavailable(self, config):
        """Test fallback to next available backend when preferred is unavailable."""
        manager = BackendManager(config)

        # Make first choice unavailable, second available
        mock_unavailable = Mock()
        mock_unavailable.name = "deepseek-ocr"
        mock_unavailable.is_available.return_value = False

        mock_available = Mock()
        mock_available.name = "florence-2"
        mock_available.is_available.return_value = True

        manager.backends = {
            "deepseek-ocr": mock_unavailable,
            "florence-2": mock_available
        }

        selected = manager.select_backend("auto")
        assert selected.name == "florence-2"

    def test_all_backends_unavailable_auto_selection(self, config):
        """Test auto-selection when all backends are unavailable."""
        manager = BackendManager(config)

        # Make all backends unavailable
        mock_backend = Mock()
        mock_backend.is_available.return_value = False
        manager.backends = {"test-backend": mock_backend}

        selected = manager.select_backend("auto")
        assert selected is None

    def test_backend_initialization_with_imports(self, config):
        """Test that backend manager initializes all expected backends."""
        manager = BackendManager(config)

        # Should have initialized all expected backends
        expected_backends = [
            "deepseek-ocr", "florence-2", "dots-ocr", "pp-ocrv5",
            "qwen-image-layered", "got-ocr", "tesseract", "easyocr"
        ]

        for backend_name in expected_backends:
            assert backend_name in manager.backends
            assert isinstance(manager.backends[backend_name], OCRBackend)

    def test_backend_manager_with_config_inheritance(self, config):
        """Test that backends inherit config correctly."""
        manager = BackendManager(config)

        for backend in manager.backends.values():
            assert backend.config == config

    def test_backend_manager_error_handling(self, config):
        """Test error handling in backend manager initialization."""
        # Should not raise exceptions even if some backends fail to initialize
        manager = BackendManager(config)

        # Manager should still be created successfully
        assert manager is not None
        assert isinstance(manager.backends, dict)

    def test_get_available_backends_partial_availability(self, config):
        """Test getting available backends when only some are available."""
        manager = BackendManager(config)

        # Mock some backends as available, others not
        available_count = 0
        for i, backend in enumerate(manager.backends.values()):
            if i % 2 == 0:  # Make every other backend available
                backend._available = True
                available_count += 1
            else:
                backend._available = False

        available = manager.get_available_backends()
        assert len(available) == available_count
        assert all(name in manager.backends for name in available)






