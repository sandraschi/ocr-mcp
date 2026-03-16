"""
Unit tests for OCR-MCP backend manager module.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from ocr_mcp.core.backend_manager import BackendManager, OCRBackend


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

    @pytest.mark.asyncio
    async def test_backend_process_image_not_implemented(self, config):
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
        assert hasattr(manager, "scanner_manager")
        assert hasattr(manager, "document_processor")

    def test_get_available_backends_empty(self, config):
        """Test getting available backends when none are available."""
        with (
            patch("ocr_mcp.core.backend_manager.scanner_manager") as mock_scanner,
            patch("ocr_mcp.core.backend_manager.document_processor") as mock_processor,
        ):
            mock_scanner.is_available.return_value = False
            mock_processor.is_available.return_value = False

            manager = BackendManager(config)

            # Replace backends with unavailable mocks (avoid lazy loading)
            for name in manager.backends:
                mock_b = Mock()
                mock_b.name = name
                mock_b.is_available.return_value = False
                manager.backends[name] = mock_b

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

        mock_backend1 = Mock()
        mock_backend1.name = "got-ocr"
        mock_backend1.is_available.return_value = False

        mock_backend2 = Mock()
        mock_backend2.name = "tesseract"
        mock_backend2.is_available.return_value = True

        manager.backends = {"got-ocr": mock_backend1, "tesseract": mock_backend2}

        # select_backend("auto") uses preference_order; tesseract is last, got-ocr earlier
        selected = manager.select_backend("auto")
        assert selected is not None
        assert selected.is_available()

    def test_select_backend_specific_available(self, config):
        """Test selecting specific available backend."""
        manager = BackendManager(config)

        mock_backend = Mock()
        mock_backend.name = "tesseract"
        mock_backend.is_available.return_value = True

        manager.backends["tesseract"] = mock_backend

        selected = manager.select_backend("tesseract")
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
        """Test selecting unknown backend name (not in registry)."""
        manager = BackendManager(config)
        manager.backends = {}  # empty so get_backend returns None; auto returns None

        selected = manager.select_backend("unknown-backend")
        assert selected is None

    @pytest.mark.asyncio
    async def test_process_with_backend_success(self, config, sample_image_path):
        """Test successful processing with a backend."""
        manager = BackendManager(config)

        mock_backend = Mock(spec=["name", "is_available", "process_image"])
        mock_backend.name = "tesseract"
        mock_backend.is_available.return_value = True
        mock_backend.process_image = AsyncMock(
            return_value={"success": True, "text": "Test OCR result", "backend": "tesseract"}
        )

        manager.backends["tesseract"] = mock_backend

        result = await manager.process_with_backend(
            "tesseract", str(sample_image_path), mode="text"
        )

        assert result["success"] is True
        assert result["text"] == "Test OCR result"
        assert result["backend_used"] == "tesseract"
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

        result = await manager.process_with_backend("test-backend", str(sample_image_path))

        assert result["success"] is False
        assert "error" in result
        assert "backend_used" in result

    @pytest.mark.asyncio
    async def test_process_with_backend_unavailable(self, config, sample_image_path):
        """Test processing when no backend is available."""
        manager = BackendManager(config)
        manager.backends = {}  # No backends so select_backend returns None

        result = await manager.process_with_backend("got-ocr", str(sample_image_path))

        assert result["success"] is False
        assert "error" in result
        assert "available_backends" in result

    def test_preference_order_auto_selection(self, config):
        """Test that auto-selection follows preference order."""
        manager = BackendManager(config)

        preference_order = [
            "paddleocr-vl",
            "got-ocr",
            "tesseract",
        ]
        for name in preference_order:
            mock_backend = Mock()
            mock_backend.name = name
            mock_backend.is_available.return_value = True
            manager.backends[name] = mock_backend

        selected = manager.select_backend("auto")
        assert selected is not None
        assert selected.name == "paddleocr-vl"

    def test_fallback_selection_when_preferred_unavailable(self, config):
        """Test fallback to next available backend when preferred is unavailable."""
        manager = BackendManager(config)

        mock_unavailable = Mock()
        mock_unavailable.name = "paddleocr-vl"
        mock_unavailable.is_available.return_value = False

        mock_available = Mock()
        mock_available.name = "got-ocr"
        mock_available.is_available.return_value = True

        manager.backends = {"paddleocr-vl": mock_unavailable, "got-ocr": mock_available}

        selected = manager.select_backend("auto")
        assert selected is not None
        assert selected.name == "got-ocr"

    def test_all_backends_unavailable_auto_selection(self, config):
        """Test auto-selection when all backends are unavailable."""
        manager = BackendManager(config)

        for name in list(manager.backends.keys()):
            mock_backend = Mock()
            mock_backend.name = name
            mock_backend.is_available.return_value = False
            manager.backends[name] = mock_backend

        selected = manager.select_backend("auto")
        assert selected is None

    def test_backend_initialization_with_imports(self, config):
        """Test that backend manager has expected backends in registry."""
        manager = BackendManager(config)

        expected_backends = [
            "deepseek-ocr",
            "paddleocr-vl",
            "dots-ocr",
            "pp-ocrv5",
            "got-ocr",
            "tesseract",
            "easyocr",
        ]

        for backend_name in expected_backends:
            assert backend_name in manager.backends, f"missing {backend_name}"

    def test_backend_manager_with_config_inheritance(self, config):
        """Test that backends inherit config when loaded."""
        manager = BackendManager(config)
        # Only check backends that are loaded (non-None)
        for backend in manager.backends.values():
            if backend is not None and hasattr(backend, "config"):
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

        available_count = 0
        for i, name in enumerate(manager.backends):
            mock_b = Mock()
            mock_b.name = name
            mock_b.is_available.return_value = (i % 2 == 0)
            if i % 2 == 0:
                available_count += 1
            manager.backends[name] = mock_b

        available = manager.get_available_backends()
        assert len(available) == available_count
        assert all(n in manager.backends for n in available)
