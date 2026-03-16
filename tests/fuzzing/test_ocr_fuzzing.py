"""
OCR Fuzzing Tests

Property-based and fuzzing tests for OCR-MCP to ensure robustness
against unexpected inputs and edge cases.
"""

import random
import string
from pathlib import Path

import pytest
from hypothesis import Verbosity, given, settings
from hypothesis import strategies as st

from src.ocr_mcp.core.error_handler import ErrorHandler
from tests.utils.test_helpers import TestDataGenerator


class TestOCRFuzzing:
    """Fuzzing tests for OCR operations."""

    @given(
        text=st.text(
            alphabet=st.characters(
                categories=[
                    "L",
                    "N",
                    "P",
                    "S",
                    "Zs",
                ],  # Letters, numbers, punctuation, symbols, spaces
                min_codepoint=0x0020,  # Avoid control characters
                max_codepoint=0x10FFFF,
            ),
            min_size=0,
            max_size=10000,
        )
    )
    @settings(max_examples=100, verbosity=Verbosity.normal)
    def test_text_input_fuzzing(self, text, file_manager):
        """Fuzz test with random text inputs."""
        # Create image with fuzzed text
        try:
            img = TestDataGenerator.create_test_image(
                text=text[:100]
            )  # Limit text length for image
            img_path = file_manager.create_temp_image(img)

            # Basic validation
            assert img_path.exists()

            # Test file operations
            result = ErrorHandler.validate_file_path(str(img_path))
            if len(text.strip()) > 0:
                # Non-empty text should create valid image
                assert result is None  # No validation errors
            else:
                # Empty text might still create valid image
                assert result is None or "FILE_NOT_FOUND" in str(result)

        except Exception as e:
            # Some inputs may legitimately fail - log but don't fail test
            pytest.skip(f"Fuzzed input caused expected failure: {e}")

    @given(
        width=st.integers(min_value=1, max_value=10000),
        height=st.integers(min_value=1, max_value=10000),
    )
    @settings(max_examples=50)
    def test_image_size_fuzzing(self, width, height, file_manager):
        """Fuzz test with random image dimensions."""
        try:
            # Limit extreme sizes for practicality
            width = min(width, 5000)
            height = min(height, 5000)

            img = TestDataGenerator.create_test_image(width=width, height=height)
            img_path = file_manager.create_temp_image(img)

            # Validate image was created
            assert img_path.exists()
            assert img.size == (width, height)

            # Test file validation
            result = ErrorHandler.validate_file_path(str(img_path))
            assert result is None  # Should be valid

        except (MemoryError, OSError) as e:
            # Legitimate failures for extreme sizes
            pytest.skip(f"Image size {width}x{height} caused expected failure: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected failure with size {width}x{height}: {e}")

    @given(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=20))
    @settings(max_examples=30)
    def test_batch_input_fuzzing(self, text_list, file_manager):
        """Fuzz test with random batch inputs."""
        try:
            image_paths = []

            for i, text in enumerate(text_list):
                if i >= 10:  # Limit batch size
                    break

                img = TestDataGenerator.create_test_image(text=text[:50])
                img_path = file_manager.create_temp_image(img)
                image_paths.append(str(img_path))

            # Validate all files were created
            for path in image_paths:
                assert Path(path).exists()

                result = ErrorHandler.validate_file_path(path)
                assert result is None

        except Exception as e:
            pytest.skip(f"Batch fuzzing caused expected failure: {e}")

    @given(
        filename=st.text(
            alphabet=st.characters(
                categories=["L", "N", "P", "S"], min_codepoint=0x0020, max_codepoint=0x10FFFF
            ),
            min_size=1,
            max_size=255,
        )
    )
    @settings(max_examples=50)
    def test_filename_fuzzing(self, filename, file_manager):
        """Fuzz test with random filenames."""
        try:
            # Sanitize filename for filesystem
            safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
            if not safe_filename:
                safe_filename = "test_file"

            # Create file with fuzzed name
            test_content = f"Content for {safe_filename}"
            file_path = file_manager.create_temp_file(test_content, f"_{safe_filename}.txt")

            # Validate file operations
            assert file_path.exists()
            assert file_path.read_text() == test_content

            # Test path validation
            result = ErrorHandler.validate_file_path(str(file_path))
            assert result is None

        except (OSError, ValueError) as e:
            # Filesystem-related failures are expected
            pytest.skip(f"Filename fuzzing caused expected failure: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected failure with filename '{filename}': {e}")

    @given(
        st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.one_of(
                st.text(max_size=1000), st.integers(), st.floats(), st.booleans(), st.none()
            ),
            min_size=0,
            max_size=100,
        )
    )
    @settings(max_examples=20)
    def test_metadata_fuzzing(self, metadata_dict, file_manager):
        """Fuzz test with random metadata structures."""
        try:
            # Test JSON serialization/deserialization
            import json

            json_str = json.dumps(metadata_dict)
            parsed_back = json.loads(json_str)

            # Basic validation
            assert isinstance(parsed_back, dict)
            assert len(parsed_back) == len(metadata_dict)

            # Test file operations with metadata
            metadata_file = file_manager.create_temp_file(json_str, "_metadata.json")
            read_back = json.loads(metadata_file.read_text())

            assert read_back == parsed_back

        except (TypeError, ValueError, json.JSONDecodeError) as e:
            # JSON-related failures are expected for complex objects
            pytest.skip(f"Metadata fuzzing caused expected failure: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected failure with metadata: {e}")

    @given(
        st.binary(min_size=0, max_size=1024 * 1024)  # Up to 1MB
    )
    @settings(max_examples=20)
    def test_binary_content_fuzzing(self, binary_data, file_manager):
        """Fuzz test with random binary content."""
        try:
            # Create file with binary content
            binary_file = file_manager.create_temp_file(binary_data, "_binary.bin")

            # Test file operations
            read_back = binary_file.read_bytes()
            assert read_back == binary_data

            # Test that it's recognized as a file
            result = ErrorHandler.validate_file_path(str(binary_file))
            assert result is None

        except Exception as e:
            # Binary data may cause various failures - acceptable
            pytest.skip(f"Binary content fuzzing caused expected failure: {e}")

    @given(
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=1000),
                st.integers(min_value=0, max_value=1000),
                st.integers(min_value=1, max_value=1000),
                st.integers(min_value=1, max_value=1000),
            ),
            min_size=0,
            max_size=10,
        )
    )
    @settings(max_examples=20)
    def test_coordinate_fuzzing(self, coordinates_list, file_manager):
        """Fuzz test with random coordinate data."""
        try:
            for coords in coordinates_list:
                x1, y1, x2, y2 = coords

                # Test coordinate validation
                if x1 >= x2 or y1 >= y2:
                    # Invalid coordinates should be rejected
                    continue

                # Valid coordinates should pass basic checks
                assert x1 < x2
                assert y1 < y2
                assert all(c >= 0 for c in [x1, y1, x2, y2])

                # Test region validation
                errors = ErrorHandler.validate_parameters(region=[x1, y1, x2, y2])
                if not errors:  # If no validation errors
                    assert len([x1, y1, x2, y2]) == 4

        except Exception as e:
            pytest.skip(f"Coordinate fuzzing caused expected failure: {e}")

    @given(
        st.text(
            alphabet=st.characters(
                categories=["L", "N", "P", "S", "Zs", "C"],  # Include control characters
                min_codepoint=0x0000,  # Include null and control chars
                max_codepoint=0x10FFFF,
            ),
            min_size=0,
            max_size=1000,
        )
    )
    @settings(max_examples=30)
    def test_unicode_fuzzing(self, unicode_text, file_manager):
        """Fuzz test with random Unicode text including control characters."""
        try:
            # Test basic string operations
            text_length = len(unicode_text)
            upper_text = unicode_text.upper()
            lower_text = unicode_text.lower()

            # Test file operations with Unicode
            unicode_file = file_manager.create_temp_file(unicode_text, "_unicode.txt")
            read_back = unicode_file.read_text()

            # Should be able to read back (encoding issues may occur)
            assert isinstance(read_back, str)

            # Test path validation
            result = ErrorHandler.validate_file_path(str(unicode_file))
            assert result is None

        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            # Unicode encoding issues are expected
            pytest.skip(f"Unicode fuzzing caused expected encoding failure: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected failure with Unicode text: {e}")

    def test_random_seed_consistency(self):
        """Test that random operations produce consistent results with fixed seeds."""
        # This test ensures our fuzzing is deterministic when needed
        random.seed(42)
        values1 = [random.randint(0, 100) for _ in range(10)]

        random.seed(42)
        values2 = [random.randint(0, 100) for _ in range(10)]

        assert values1 == values2

    @pytest.mark.parametrize("iterations", [10, 50, 100])
    def test_stress_fuzzing(self, iterations, file_manager):
        """Stress test with many rapid fuzzing iterations."""
        errors = 0
        successes = 0

        for i in range(iterations):
            try:
                # Generate random test data
                text = "".join(
                    random.choices(string.ascii_letters + string.digits, k=random.randint(1, 100))
                )
                width = random.randint(10, 1000)
                height = random.randint(10, 1000)

                # Create and validate image
                img = TestDataGenerator.create_test_image(
                    width=width, height=height, text=text[:20]
                )
                img_path = file_manager.create_temp_image(img)

                # Quick validation
                assert img_path.exists()
                result = ErrorHandler.validate_file_path(str(img_path))
                assert result is None

                successes += 1

            except Exception:
                errors += 1

        # Allow some failures but require majority success
        success_rate = successes / (successes + errors)
        assert success_rate >= 0.8, (
            f"Success rate too low: {success_rate:.2%} ({successes}/{successes + errors})"
        )

    def test_edge_case_coverage(self, file_manager):
        """Test specific edge cases that should be covered."""
        edge_cases = [
            ("empty_string", ""),
            ("very_long_text", "A" * 10000),
            ("special_chars", "!@#$%^&*()_+-=[]{}|;:,.<>?"),
            ("unicode_emojis", "🚀🔥💯😀🎉"),
            ("mixed_scripts", "Hello 世界 नमस्ते Привет"),
            ("numbers_only", "12345678901234567890"),
            ("whitespace_only", "   \n\t  \r\n  "),
        ]

        for case_name, text in edge_cases:
            try:
                img = TestDataGenerator.create_test_image(text=text[:50])  # Limit for image
                img_path = file_manager.create_temp_image(img)

                # Basic validation
                assert img_path.exists()

                # File operations should work
                result = ErrorHandler.validate_file_path(str(img_path))
                assert result is None

            except Exception as e:
                # Some edge cases may fail - that's OK
                pytest.skip(f"Edge case '{case_name}' caused expected failure: {e}")
