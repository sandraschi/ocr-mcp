# OCR-MCP Testing Suite

Comprehensive testing framework for OCR-MCP with multiple testing strategies and CI/CD integration.

## 🏗️ Testing Architecture

```
tests/
├── conftest.py                 # Base test configuration and fixtures
├── conftest_advanced.py        # Advanced testing utilities
├── utils/
│   ├── test_helpers.py         # Test data generators and utilities
│   └── ...
├── unit/                       # Unit tests
├── integration/               # Integration tests
├── performance/               # Performance and load tests
├── security/                  # Security and input validation tests
├── fuzzing/                   # Fuzzing and property-based tests
├── smoke/                     # Basic functionality tests
├── regression/                # Regression tests
├── e2e/                       # End-to-end tests
├── acceptance/                # Acceptance tests
├── property/                  # Property-based tests
├── fixtures/                  # Test data and assets
├── mocks/                     # Mock objects and utilities
└── run_tests.py              # Advanced test runner
```

## 🚀 Quick Start

### Run All Tests
```bash
# Using the advanced test runner
python tests/run_tests.py all

# Or using pytest directly
pytest
```

### Run Specific Test Types
```bash
# Unit tests only
python tests/run_tests.py unit

# Integration tests
python tests/run_tests.py integration

# Performance tests
python tests/run_tests.py performance

# Security tests
python tests/run_tests.py security

# Fuzzing tests
python tests/run_tests.py fuzzing
```

### Run with Coverage
```bash
# Generate coverage reports
python tests/run_tests.py all --coverage

# View HTML coverage report
open reports/coverage/html/index.html
```

## 📊 Test Categories

### 🔬 Unit Tests (`tests/unit/`)
Test individual components in isolation.
```bash
pytest tests/unit/ -v
```

### 🔗 Integration Tests (`tests/integration/`)
Test component interactions and API endpoints.
```bash
pytest tests/integration/ -v -m integration
```

### ⚡ Performance Tests (`tests/performance/`)
Measure throughput, latency, and scalability.
```bash
pytest tests/performance/ -v -m performance
```

### 🔒 Security Tests (`tests/security/`)
Input validation, injection prevention, and security checks.
```bash
pytest tests/security/ -v -m security
```

### 🎯 Fuzzing Tests (`tests/fuzzing/`)
Property-based testing with random inputs.
```bash
pytest tests/fuzzing/ -v -m fuzzing
```

### 💨 Smoke Tests
Basic functionality verification.
```bash
pytest -k smoke -v
```

### 🔄 Regression Tests (`tests/regression/`)
Ensure previously fixed bugs stay fixed.
```bash
pytest tests/regression/ -v
```

### 🌐 End-to-End Tests (`tests/e2e/`)
Full workflow testing from input to output.
```bash
pytest tests/e2e/ -v -m e2e
```

## 🛠️ Testing Utilities

### Test Data Generators
```python
from tests.utils.test_helpers import TestDataGenerator

generator = TestDataGenerator()

# Create realistic test images
image = generator.create_test_image(
    text="Sample OCR text",
    width=800,
    height=600
)

# Create complex document images
complex_doc = generator.create_complex_document_image(
    pages=3,
    include_tables=True,
    include_headers=True
)
```

### Performance Profiling
```python
from tests.utils.test_helpers import PerformanceProfiler

profiler = PerformanceProfiler()
profiler.start()

# Your code here
result = ocr_backend.process_image(image_path)

elapsed = profiler.stop("ocr_processing")
stats = profiler.get_stats()
```

### Mock Backend Factory
```python
from tests.utils.test_helpers import MockBackendFactory

# Create complete backend suite
backends = MockBackendFactory.create_backend_suite()

# Create specific mock backend
mock_backend = MockBackendFactory.create_mock_backend(
    "deepseek-ocr",
    available=True,
    capabilities={"gpu_support": True, "accuracy": 0.92}
)
```

## 📈 Advanced Features

### Profiling Tests
```bash
# Profile test execution
python tests/run_tests.py unit --profile profile_output.prof

# Analyze profile
snakeviz profile_output.prof
```

### Load Testing
```python
# Test concurrent processing
@pytest.mark.parametrize("concurrent_jobs", [1, 2, 4, 8])
def test_concurrent_processing(concurrent_jobs, backend_manager):
    # Test with different concurrency levels
    pass
```

### Property-Based Testing
```python
from hypothesis import given, strategies as st

@given(
    text=st.text(min_size=1, max_size=1000),
    width=st.integers(min_value=10, max_value=2000)
)
def test_ocr_with_random_inputs(text, width):
    # Test OCR with random inputs
    pass
```

### Security Testing
```python
def test_path_traversal_prevention(security_test_cases):
    """Test prevention of path traversal attacks."""
    for malicious_path in security_test_cases["path_traversal"]:
        # Should fail validation
        assert ErrorHandler.validate_file_path(malicious_path) is not None
```

## 📋 Test Configuration

### Environment Variables
```bash
# Disable GPU for consistent testing
export OCR_DISABLE_GPU=true

# Set test-specific cache directory
export OCR_CACHE_DIR=/tmp/ocr_test_cache

# Enable verbose logging
export OCR_LOG_LEVEL=DEBUG
```

### Test Markers
```python
@pytest.mark.slow  # Mark slow tests
@pytest.mark.integration  # Integration tests
@pytest.mark.performance  # Performance tests
@pytest.mark.security  # Security tests
@pytest.mark.fuzzing  # Fuzzing tests
@pytest.mark.e2e  # End-to-end tests
```

### Custom Fixtures
```python
@pytest.fixture
def realistic_document_scenarios():
    """Realistic document testing scenarios."""
    return {
        "invoice": {
            "text": "Invoice content...",
            "expected_elements": ["invoice", "table", "totals"],
            "complexity": "medium"
        }
    }
```

## 🔧 Development Workflow

### Adding New Tests
1. Choose appropriate test category directory
2. Create test file: `test_feature_name.py`
3. Use descriptive test names: `test_should_process_image_correctly`
4. Add appropriate markers
5. Include docstrings explaining test purpose

### Test File Structure
```python
"""
Test module for OCR feature.

Tests cover:
- Basic functionality
- Edge cases
- Error handling
- Performance characteristics
"""

import pytest

class TestOCRFeature:
    """Test cases for OCR feature."""

    def test_basic_functionality(self, backend_manager):
        """Test basic OCR functionality."""
        pass

    def test_error_handling(self, backend_manager):
        """Test error handling scenarios."""
        pass

    @pytest.mark.performance
    def test_performance_under_load(self, backend_manager):
        """Test performance under load."""
        pass
```

### CI/CD Integration
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: python tests/run_tests.py all --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          file: reports/coverage/coverage.xml
```

## 📊 Test Reporting

### Generate Reports
```bash
# Generate comprehensive test report
python tests/run_tests.py all --report

# View HTML coverage report
open reports/coverage/html/index.html
```

### Performance Metrics
```python
# Track performance regressions
def test_performance_regression(performance_monitor):
    profiler.start()
    # Execute operation
    result = ocr_process(image)
    elapsed = profiler.stop("operation")

    # Assert performance requirements
    assert elapsed < 5.0  # Max 5 seconds
    assert result.confidence > 0.8  # Min confidence
```

## 🐛 Debugging Tests

### Verbose Output
```bash
# Run with verbose output
pytest tests/unit/test_backend_manager.py -v -s

# Show durations
pytest --durations=10
```

### Debug Specific Test
```bash
# Run single test with debugging
pytest tests/unit/test_backend_manager.py::TestBackendManager::test_get_available_backends -xvs

# Drop into debugger on failure
pytest --pdb
```

### Test Isolation
```bash
# Run tests in isolation (no shared fixtures)
pytest --disable-warnings -x --tb=short

# Run with specific Python path
PYTHONPATH=src pytest
```

## 📚 Best Practices

### Test Organization
- **One concept per test**: Each test should verify one specific behavior
- **Descriptive names**: Test names should explain what they verify
- **Independent tests**: Tests should not depend on each other
- **Fast execution**: Keep unit tests under 100ms each

### Fixture Usage
- **Minimal fixtures**: Only create what's needed for the test
- **Scope appropriately**: Use `function` scope for most fixtures
- **Cleanup**: Ensure fixtures clean up after themselves
- **Reusability**: Create fixtures for common test data

### Mock Strategy
- **Minimal mocking**: Mock only external dependencies
- **Realistic mocks**: Mocks should behave like real objects
- **Verification**: Verify mock interactions when necessary
- **Avoid over-mocking**: Test real code paths when possible

### Performance Testing
- **Realistic workloads**: Test with production-like data sizes
- **Measure accurately**: Use appropriate timing mechanisms
- **Baseline comparisons**: Compare against acceptable thresholds
- **Resource monitoring**: Track memory and CPU usage

### Security Testing
- **Comprehensive inputs**: Test all input vectors
- **Edge cases**: Include boundary conditions and unusual inputs
- **Injection attacks**: Test common attack patterns
- **Validation**: Ensure all inputs are properly validated

## 🚨 Common Issues

### Import Errors
```bash
# Ensure proper Python path
export PYTHONPATH=src:$PYTHONPATH
pytest tests/
```

### GPU/CPU Issues
```bash
# Disable GPU for testing
export OCR_DISABLE_GPU=true
pytest tests/unit/
```

### Memory Issues
```bash
# Limit memory usage in tests
export OCR_MAX_MEMORY=2048  # MB
pytest tests/performance/
```

### Slow Tests
```bash
# Skip slow tests
pytest -m "not slow"

# Run only fast tests
pytest -m "not (slow or performance)"
```

## 📞 Support

For testing questions or issues:
1. Check existing test examples in each category
2. Review `conftest.py` for available fixtures
3. Run tests with `--verbose` for detailed output
4. Check the test runner help: `python tests/run_tests.py --help`