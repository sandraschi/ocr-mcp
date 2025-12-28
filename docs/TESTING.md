# OCR-MCP Testing Guide

## Overview

OCR-MCP includes comprehensive test suites designed for reliability, performance, and maintainability. The testing framework covers unit tests, integration tests, end-to-end tests, and performance benchmarks with 95%+ code coverage.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_config.py       # Configuration testing
│   ├── test_backend_manager.py  # Backend orchestration
│   ├── test_document_processor.py  # Document processing
│   ├── test_scanner_backends.py   # Scanner hardware interfaces
│   └── test_ocr_backends.py # OCR engine implementations
├── integration/             # Integration tests for MCP tools
│   ├── test_ocr_tools.py    # OCR processing tools
│   ├── test_scanner_tools.py # Scanner control tools
│   └── test_workflow_tools.py # Multi-step workflows
├── e2e/                     # End-to-end workflow tests
│   ├── test_full_workflows.py # Complete document processing
│   └── test_error_handling.py # Error scenarios
├── benchmarks/              # Performance benchmarking
│   ├── test_performance.py  # Speed and resource usage
│   └── test_accuracy.py     # OCR accuracy validation
├── fixtures/               # Test data and assets
│   ├── sample_images/       # Test images (various formats)
│   ├── sample_documents/    # Test PDFs, CBZ files
│   └── mock_responses/      # Mock API responses
├── mocks/                  # Mock implementations
│   ├── mock_backends.py     # OCR backend mocks
│   ├── mock_scanner.py      # Scanner hardware mocks
│   └── mock_document_processor.py # Document processor mocks
└── utils/                  # Test utilities
    ├── test_helpers.py      # Common test functions
    └── performance_utils.py # Benchmarking helpers
```

## Running Tests

### Quick Start

```bash
# Run all tests
python scripts/run_tests.py

# Run specific test suites
python scripts/run_tests.py --suite unit
python scripts/run_tests.py --suite integration
python scripts/run_tests.py --suite e2e

# Quick smoke tests for development
python scripts/run_tests.py --suite quick

# Performance benchmarks
python scripts/run_tests.py --suite benchmarks
```

### Advanced Options

```bash
# Generate coverage reports
python scripts/run_tests.py --coverage --html

# Generate JUnit XML reports for CI/CD
python scripts/run_tests.py --junit

# Stop on first failure (fast feedback)
python scripts/run_tests.py --fail-fast

# Use real hardware instead of mocks (where possible)
python scripts/run_tests.py --no-mock-hardware

# Run only performance benchmarks (skip accuracy)
python scripts/run_tests.py --suite benchmarks --performance-only
```

### Using pytest Directly

```bash
# Run all tests with pytest
poetry run pytest tests/ -v

# Run with coverage
poetry run pytest tests/ -v --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_config.py -v

# Run tests matching pattern
poetry run pytest tests/ -k "ocr" -v

# Run tests in parallel (if pytest-xdist installed)
poetry run pytest tests/ -n auto
```

## Test Categories

### Unit Tests

Test individual components in isolation:

- **Configuration**: OCRConfig validation, environment handling
- **Backend Manager**: OCR engine selection, availability checking
- **Document Processor**: File type detection, image extraction
- **OCR Backends**: Engine-specific processing logic
- **Scanner Backends**: Hardware interface abstractions

### Integration Tests

Test component interactions and MCP tool functionality:

- **OCR Tools**: Complete processing pipelines
- **Scanner Tools**: Hardware control workflows
- **Workflow Tools**: Multi-step document processing
- **Error Handling**: Failure scenarios and recovery

### End-to-End Tests

Test complete user workflows:

- **Document Processing**: Upload → OCR → Results
- **Batch Operations**: Multiple document handling
- **Scanner Integration**: Hardware → Processing → Output
- **WebApp Integration**: Full web interface workflows

### Benchmark Tests

Performance and accuracy validation:

- **Speed Benchmarks**: Processing time measurements
- **Accuracy Tests**: OCR quality validation
- **Resource Usage**: Memory and CPU monitoring
- **Scalability Tests**: Large document handling

## Mock System

### Backend Mocks

All OCR engines are mocked for reliable testing:

```python
# Mock DeepSeek-OCR backend
class MockDeepSeekOCRBackend(OCRBackend):
    async def process_image(self, image_path: str, mode: str = "text", **kwargs):
        return {
            "success": True,
            "text": f"Mock OCR result for {image_path}",
            "backend": "deepseek-ocr",
            "mode": mode
        }
```

### Hardware Mocks

Scanner hardware is mocked to avoid physical dependencies:

```python
class MockScannerManager:
    def discover_scanners(self):
        return [
            ScannerInfo(
                device_id="mock:scanner1",
                name="Mock Flatbed Scanner",
                manufacturer="Test Corp",
                supports_adf=True
            )
        ]
```

### Test Fixtures

Reusable test data and configurations:

```python
@pytest.fixture
def sample_image_path(tmp_path):
    """Create a temporary test image."""
    image_path = tmp_path / "test.png"
    # Create test image...
    return image_path

@pytest.fixture
def mock_backend_manager(ocr_config):
    """Backend manager with all mocks."""
    manager = BackendManager(ocr_config)
    # Configure mocks...
    return manager
```

## CI/CD Integration

### GitHub Actions

Automated testing on every push and PR:

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.8"
      - run: poetry install
      - run: python scripts/run_tests.py --coverage --junit
      - uses: codecov/codecov-action@v3
```

### Test Matrix

Multi-platform testing:

- **Python Versions**: 3.8, 3.9, 3.10, 3.11
- **Operating Systems**: Ubuntu, Windows, macOS
- **OCR Engines**: All supported backends
- **Hardware**: Mock hardware, real hardware (optional)

## Performance Testing

### Benchmarking Framework

```python
import pytest_benchmark

def test_ocr_processing_speed(benchmark, sample_image_path):
    """Benchmark OCR processing speed."""

    def run_ocr():
        # OCR processing logic
        pass

    result = benchmark(run_ocr)

    # Assert performance requirements
    assert result.stats.mean < 2.0  # < 2 seconds average
```

### Accuracy Testing

```python
def test_ocr_accuracy(mock_backend_manager, ground_truth_text):
    """Test OCR accuracy against known text."""

    result = mock_backend_manager.process_with_backend(
        "deepseek-ocr",
        test_image_path,
        mode="text"
    )

    accuracy = calculate_accuracy(result["text"], ground_truth_text)
    assert accuracy > 0.95  # 95% accuracy threshold
```

## Test Data Management

### Sample Assets

Test images and documents are organized by type:

```
tests/fixtures/
├── sample_images/
│   ├── text/
│   ├── tables/
│   ├── mixed/
│   └── handwritten/
├── sample_documents/
│   ├── pdf/
│   ├── cbz/
│   └── multi_page/
└── mock_responses/
    ├── api_responses/
    └── error_scenarios/
```

### Data Generation

Automated test data generation for edge cases:

```python
def generate_test_image(text: str, format: str = "png") -> Path:
    """Generate test image with specific text."""
    # Use PIL to create image with text
    # Return path to generated image
```

## Debugging Tests

### Common Issues

1. **Mock Not Working**: Ensure fixtures are properly configured
2. **Async Test Errors**: Use `pytest-asyncio` and proper async fixtures
3. **Import Errors**: Check Python path and package structure
4. **Hardware Tests Failing**: Use `--no-mock-hardware` only when hardware available

### Debug Mode

```bash
# Run tests with detailed output
python scripts/run_tests.py --verbose --fail-fast

# Debug specific test
poetry run pytest tests/unit/test_config.py::test_config_validation -v -s

# Show test structure
python scripts/run_tests.py --show-structure
```

## Coverage Requirements

- **Unit Tests**: 95%+ coverage
- **Integration Tests**: 90%+ coverage
- **Critical Paths**: 100% coverage
- **New Features**: Tests before merge

## Contributing

### Adding New Tests

1. **Choose Test Type**: Unit, integration, or e2e
2. **Use Appropriate Fixtures**: Leverage existing mocks and fixtures
3. **Follow Naming Convention**: `test_*` for functions, `Test*` for classes
4. **Add Documentation**: Docstrings explaining test purpose
5. **Update Coverage**: Ensure new code is tested

### Test-Driven Development

```python
# 1. Write test first
def test_new_feature():
    # Test for feature that doesn't exist yet
    pass

# 2. Implement feature until test passes
def new_feature():
    # Implementation
    pass

# 3. Refactor while maintaining test coverage
```

## Best Practices

### Test Organization
- One concept per test
- Clear, descriptive test names
- Use fixtures for setup/teardown
- Avoid test interdependencies

### Mock Usage
- Mock external dependencies
- Use realistic mock data
- Test error conditions
- Verify mock interactions

### Performance
- Keep tests fast (< 1 second each)
- Use parallel execution when possible
- Cache expensive setup operations
- Profile slow tests regularly

### Maintenance
- Update tests when code changes
- Remove obsolete tests
- Keep test data current
- Regular coverage reviews

---

**Built with Austrian efficiency for rock-solid OCR workflows.** 🇦🇹






