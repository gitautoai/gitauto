# pylint: disable=redefined-outer-name
# pylint: disable=too-many-public-methods
"""Unit tests for the should_test_file function."""

from unittest.mock import patch

import pytest

from utils.files.should_test_file import should_test_file


class TestShouldTestFile:
    """Test cases for the should_test_file function."""

    @pytest.fixture
    def mock_evaluate_condition(self):
        """Mock the evaluate_condition function."""
        with patch("utils.files.should_test_file.evaluate_condition") as mock_evaluate:
            yield mock_evaluate

    @pytest.fixture
    def sample_file_path(self):
        """Sample file path for testing."""
        return "services/calculator.py"

    @pytest.fixture
    def sample_code_content(self):
        """Sample code content that should be tested."""
        return "class Calculator:\n    def add(self, a, b):\n        return a + b"

    @pytest.fixture
    def trivial_code_content(self):
        """Sample trivial code content that shouldn't be tested."""
        return "#!/usr/bin/env python\nfrom app import main\nmain()"

    def test_should_test_file_returns_true_when_evaluation_true(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that function returns True when evaluate_condition returns True."""
        mock_evaluate_condition.return_value = True

        result = should_test_file(
            file_path=sample_file_path,
            content=sample_code_content,
        )

        assert result is True
        mock_evaluate_condition.assert_called_once()

    def test_should_test_file_returns_false_when_evaluation_false(
        self, mock_evaluate_condition, sample_file_path, trivial_code_content
    ):
        """Test that function returns False when evaluate_condition returns False."""
        mock_evaluate_condition.return_value = False

        result = should_test_file(
            file_path=sample_file_path,
            content=trivial_code_content,
        )

        assert result is False
        mock_evaluate_condition.assert_called_once()

    def test_should_test_file_returns_false_when_evaluation_none(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that function returns False when evaluate_condition returns None."""
        mock_evaluate_condition.return_value = None

        result = should_test_file(
            file_path=sample_file_path, content=sample_code_content
        )

        # Should return False when evaluation fails (avoid generating garbage)
        assert result is False
        mock_evaluate_condition.assert_called_once()

    def test_should_test_file_handles_exception_gracefully(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that function returns False when evaluate_condition raises exception."""
        mock_evaluate_condition.side_effect = Exception("API Error")

        result = should_test_file(
            file_path=sample_file_path, content=sample_code_content
        )

        # Should return False when exception occurs (handled by decorator)
        assert result is False
        mock_evaluate_condition.assert_called_once()

    def test_should_test_file_passes_correct_content_format(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that function passes correctly formatted content to evaluate_condition."""
        mock_evaluate_condition.return_value = True

        should_test_file(sample_file_path, sample_code_content)

        # Verify the content is passed correctly with file path
        call_args = mock_evaluate_condition.call_args
        content_arg = call_args[1]["content"]
        assert f"File path: {sample_file_path}" in content_arg
        assert sample_code_content in content_arg
        assert content_arg.startswith(f"File path: {sample_file_path}\n\nContent:\n")

    def test_should_test_file_uses_correct_system_prompt(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that function uses the correct system prompt."""
        mock_evaluate_condition.return_value = True

        should_test_file(sample_file_path, sample_code_content)

        # Verify the system prompt contains expected keywords
        call_args = mock_evaluate_condition.call_args
        system_prompt = call_args[1]["system_prompt"]

        # Check for key phrases in the system prompt
        assert "experienced senior engineer" in system_prompt
        assert "practical and strict" in system_prompt
        assert "TRUE" in system_prompt
        assert "FALSE" in system_prompt
        assert "actual logic worth testing" in system_prompt
        assert "trivial code that doesn't need tests" in system_prompt

    def test_should_test_file_with_empty_file_path(
        self, mock_evaluate_condition, sample_code_content
    ):
        """Test function behavior with empty file path."""
        mock_evaluate_condition.return_value = True

        result = should_test_file("", sample_code_content)

        assert result is True
        mock_evaluate_condition.assert_called_once()

        # Verify empty file path is still passed correctly
        call_args = mock_evaluate_condition.call_args
        content_arg = call_args[1]["content"]
        assert "File path: \n\nContent:\n" in content_arg

    def test_should_test_file_with_empty_content(
        self, mock_evaluate_condition, sample_file_path
    ):
        """Test function behavior with empty content."""
        mock_evaluate_condition.return_value = False

        result = should_test_file(sample_file_path, "")

        assert result is False
        mock_evaluate_condition.assert_called_once()

        # Verify empty content is passed correctly
        call_args = mock_evaluate_condition.call_args
        content_arg = call_args[1]["content"]
        assert f"File path: {sample_file_path}\n\nContent:\n" == content_arg

    def test_should_test_file_with_multiline_content(
        self, mock_evaluate_condition, sample_file_path
    ):
        """Test function behavior with multiline content."""
        multiline_content = """def complex_function(x, y):
    if x > 0:
        return x + y
    else:
        return x - y

class DataProcessor:
    def process(self, data):
        return [item.upper() for item in data if item]"""

        mock_evaluate_condition.return_value = True

        result = should_test_file(sample_file_path, multiline_content)

        assert result is True
        mock_evaluate_condition.assert_called_once()

        # Verify multiline content is preserved
        call_args = mock_evaluate_condition.call_args
        content_arg = call_args[1]["content"]
        assert multiline_content in content_arg
        assert content_arg.count("\n") >= multiline_content.count("\n")

    def test_should_test_file_with_special_characters_in_content(
        self, mock_evaluate_condition, sample_file_path
    ):
        """Test function behavior with special characters in content."""
        special_content = 'def test():\n    return "Hello, 世界! @#$%^&*()"\n    # Comment with émojis 🚀'
        mock_evaluate_condition.return_value = True

        result = should_test_file(sample_file_path, special_content)

        assert result is True
        mock_evaluate_condition.assert_called_once()

        # Verify special characters are preserved
        call_args = mock_evaluate_condition.call_args
        content_arg = call_args[1]["content"]
        assert special_content in content_arg

    def test_should_test_file_decorator_default_behavior(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that the handle_exceptions decorator works with correct defaults."""
        # Test that the decorator is applied with correct parameters
        # by verifying the function still works when evaluate_condition fails
        mock_evaluate_condition.side_effect = ValueError("Network error")

        result = should_test_file(sample_file_path, sample_code_content)

        # Should return False (default_return_value) when exception occurs
        assert result is False

    def test_should_test_file_with_different_file_extensions(
        self, mock_evaluate_condition, sample_code_content
    ):
        """Test function behavior with different file extensions."""
        file_paths = [
            "service.py",
            "component.js",
            "model.rb",
            "controller.java",
            "helper.go",
            "utils.ts",
            "config.json",
            "README.md",
        ]

        mock_evaluate_condition.return_value = True

        for file_path in file_paths:
            result = should_test_file(file_path, sample_code_content)
            assert result is True

            # Verify each file path is passed correctly
            call_args = mock_evaluate_condition.call_args
            content_arg = call_args[1]["content"]
            assert f"File path: {file_path}" in content_arg

    def test_should_test_file_evaluate_condition_called_with_correct_parameters(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that evaluate_condition is called with exactly the right parameters."""
        mock_evaluate_condition.return_value = True

        should_test_file(sample_file_path, sample_code_content)

        # Verify evaluate_condition was called exactly once with correct parameters
        mock_evaluate_condition.assert_called_once()
        call_args = mock_evaluate_condition.call_args

        # Should be called with keyword arguments
        assert "content" in call_args[1]
        assert "system_prompt" in call_args[1]

        # Should not have positional arguments
        assert len(call_args[0]) == 0

        # Should have exactly 2 keyword arguments
        assert len(call_args[1]) == 2

    def test_should_test_file_with_none_inputs(self, mock_evaluate_condition):
        """Test function behavior with None inputs."""
        mock_evaluate_condition.return_value = False

        # Test with None file_path - should handle gracefully
        result = should_test_file(None, "some content")
        assert result is False

        # Test with None content - should handle gracefully
        result = should_test_file("test.py", None)
        assert result is False

    def test_should_test_file_with_very_long_content(
        self, mock_evaluate_condition, sample_file_path
    ):
        """Test function behavior with very long content."""
        # Create a very long content string
        long_content = "def function():\n    pass\n" * 1000
        mock_evaluate_condition.return_value = True

        result = should_test_file(sample_file_path, long_content)

        assert result is True
        mock_evaluate_condition.assert_called_once()

        # Verify long content is passed correctly
        call_args = mock_evaluate_condition.call_args
        content_arg = call_args[1]["content"]
        assert long_content in content_arg

    def test_should_test_file_system_prompt_immutable(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that the system prompt remains consistent across calls."""
        mock_evaluate_condition.return_value = True

        # Make multiple calls
        should_test_file(sample_file_path, sample_code_content)
        first_call_prompt = mock_evaluate_condition.call_args[1]["system_prompt"]

        mock_evaluate_condition.reset_mock()
        should_test_file("different_file.py", "different content")
        second_call_prompt = mock_evaluate_condition.call_args[1]["system_prompt"]

        # System prompt should be identical
        assert first_call_prompt == second_call_prompt

    def test_should_test_file_content_formatting_consistency(
        self, mock_evaluate_condition
    ):
        """Test that content formatting is consistent."""
        mock_evaluate_condition.return_value = True

        test_cases = [
            ("file.py", "content"),
            ("path/to/file.js", "function test() {}"),
            ("", "empty path"),
            ("file.txt", ""),
        ]

        for file_path, content in test_cases:
            mock_evaluate_condition.reset_mock()
            should_test_file(file_path, content)

            call_args = mock_evaluate_condition.call_args
            content_arg = call_args[1]["content"]

            # Verify consistent formatting pattern
            expected_start = f"File path: {file_path}\n\nContent:\n"
            assert content_arg.startswith(expected_start)
            assert content_arg == f"{expected_start}{content}"

    def test_should_test_file_return_type_consistency(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that function always returns a boolean."""
        # Test with True return value
        mock_evaluate_condition.return_value = True
        result = should_test_file(sample_file_path, sample_code_content)
        assert isinstance(result, bool)
        assert result is True

        # Test with False return value
        mock_evaluate_condition.return_value = False
        result = should_test_file(sample_file_path, sample_code_content)
        assert isinstance(result, bool)
        assert result is False

        # Test with None return value
        mock_evaluate_condition.return_value = None
        result = should_test_file(sample_file_path, sample_code_content)
        assert isinstance(result, bool)
        assert result is False

    def test_should_test_file_integration_with_handle_exceptions_decorator(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Integration test to verify the decorator is properly applied."""
        # Test that the function has the decorator applied
        from utils.files.should_test_file import should_test_file as original_function

        # Check that the function is wrapped (has __wrapped__ attribute)
        assert hasattr(original_function, "__wrapped__")

        # Test that exceptions are handled according to decorator configuration
        mock_evaluate_condition.side_effect = Exception("Test exception")

        result = should_test_file(sample_file_path, sample_code_content)

        # Should return False (default_return_value) and not raise
        assert result is False

    def test_should_test_file_with_realistic_code_samples(
        self, mock_evaluate_condition
    ):
        """Test with realistic code samples that should/shouldn't be tested."""

        # Code that should be tested (complex logic)
        complex_code = """
class UserManager:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def create_user(self, username, email):
        if not username or not email:
            raise ValueError("Username and email are required")
        
        if self.user_exists(username):
            return None
            
        user_id = self.db.insert_user(username, email)
        return user_id
        
    def user_exists(self, username):
        return self.db.query_user(username) is not None
"""

        # Simple code that might not need tests
        simple_code = """
from app import main
if __name__ == "__main__":
    main()
"""

        # Test complex code
        mock_evaluate_condition.return_value = True
        result = should_test_file("user_manager.py", complex_code)
        assert result is True

        # Test simple code
        mock_evaluate_condition.return_value = False
        result = should_test_file("main.py", simple_code)
        assert result is False

    def test_should_test_file_mock_call_count_verification(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that evaluate_condition is called exactly once per function call."""
        mock_evaluate_condition.return_value = True

        # Single call
        should_test_file(sample_file_path, sample_code_content)
        assert mock_evaluate_condition.call_count == 1

        # Multiple calls should each call evaluate_condition once
        should_test_file(sample_file_path, sample_code_content)
        assert mock_evaluate_condition.call_count == 2

        should_test_file("another_file.py", "different content")
        assert mock_evaluate_condition.call_count == 3

    def test_should_test_file_with_unicode_file_paths(
        self, mock_evaluate_condition, sample_code_content
    ):
        """Test function behavior with unicode characters in file paths."""
        unicode_paths = [
            "测试文件.py",
            "файл.py",
            "ファイル.py",
            "archivo_español.py",
            "tệp_tiếng_việt.py",
        ]

        mock_evaluate_condition.return_value = True

        for file_path in unicode_paths:
            mock_evaluate_condition.reset_mock()
            result = should_test_file(file_path, sample_code_content)

            assert result is True
            mock_evaluate_condition.assert_called_once()

            # Verify unicode file path is preserved
            call_args = mock_evaluate_condition.call_args
            content_arg = call_args[1]["content"]
            assert f"File path: {file_path}" in content_arg

    def test_should_test_file_thread_safety_simulation(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that function calls don't interfere with each other (simulating thread safety)."""
        # Simulate concurrent calls with different return values
        call_results = []

        for i in range(5):
            mock_evaluate_condition.reset_mock()
            mock_evaluate_condition.return_value = i % 2 == 0  # Alternate True/False

            result = should_test_file(f"file_{i}.py", f"content_{i}")
            call_results.append(result)

        # Verify results match expected pattern
        expected_results = [True, False, True, False, True]
        assert call_results == expected_results

    def test_should_test_file_comprehensive_error_scenarios(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test various error scenarios to ensure robust error handling."""
        error_scenarios = [
            ValueError("Invalid input"),
            TypeError("Type mismatch"),
            AttributeError("Missing attribute"),
            KeyError("Missing key"),
            RuntimeError("Runtime error"),
            ConnectionError("Network error"),
            TimeoutError("Request timeout"),
        ]

        for error in error_scenarios:
            mock_evaluate_condition.reset_mock()
            mock_evaluate_condition.side_effect = error

            # Should handle all errors gracefully and return False
            result = should_test_file(sample_file_path, sample_code_content)
            assert result is False
            mock_evaluate_condition.assert_called_once()

    def test_should_test_file_function_signature_validation(self):
        """Test that the function has the correct signature."""
        import inspect
        from utils.files.should_test_file import should_test_file

        sig = inspect.signature(should_test_file)
        params = list(sig.parameters.keys())

        # Should have exactly 2 parameters
        assert len(params) == 2
        assert "file_path" in params
        assert "content" in params
