# pylint: disable=redefined-outer-name

import pytest
from unittest.mock import patch

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
            file_path=sample_file_path,
            content=sample_code_content
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
            file_path=sample_file_path,
            content=sample_code_content
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
        assert content_arg.count('\n') >= multiline_content.count('\n')

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
            "README.md"
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

    def test_should_test_file_with_none_file_path(
        self, mock_evaluate_condition, sample_code_content
    ):
        """Test function behavior when file_path is None (edge case)."""
        mock_evaluate_condition.return_value = True

        # This should work due to f-string handling None
        result = should_test_file(None, sample_code_content)

        assert result is True
        mock_evaluate_condition.assert_called_once()
        
        # Verify None file path is converted to string
        call_args = mock_evaluate_condition.call_args
        content_arg = call_args[1]["content"]
        assert "File path: None" in content_arg

    def test_should_test_file_with_none_content(
        self, mock_evaluate_condition, sample_file_path
    ):
        """Test function behavior when content is None (edge case)."""
        mock_evaluate_condition.return_value = False

        # This should work due to f-string handling None
        result = should_test_file(sample_file_path, None)

        assert result is False
        mock_evaluate_condition.assert_called_once()
        
        # Verify None content is converted to string
        call_args = mock_evaluate_condition.call_args
        content_arg = call_args[1]["content"]
        assert "Content:\nNone" in content_arg

    def test_should_test_file_with_very_long_content(
        self, mock_evaluate_condition, sample_file_path
    ):
        """Test function behavior with very long content."""
        long_content = "def function():\n    pass\n" * 1000  # Very long content
        mock_evaluate_condition.return_value = True

        result = should_test_file(sample_file_path, long_content)

        assert result is True
        mock_evaluate_condition.assert_called_once()
        
        # Verify long content is passed correctly
        call_args = mock_evaluate_condition.call_args
        content_arg = call_args[1]["content"]
        assert long_content in content_arg

    def test_should_test_file_system_prompt_exact_content(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that the exact system prompt is used."""
        mock_evaluate_condition.return_value = True

        should_test_file(sample_file_path, sample_code_content)

        call_args = mock_evaluate_condition.call_args
        system_prompt = call_args[1]["system_prompt"]
        
        expected_prompt = """You are a very experienced senior engineer. Look at this code and decide if it needs unit tests.

Be practical and strict - only return TRUE if the code has actual logic worth testing.

Return FALSE for trivial code that doesn't need tests."""
        
        assert system_prompt == expected_prompt

    def test_should_test_file_content_format_exact(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test the exact format of content passed to evaluate_condition."""
        mock_evaluate_condition.return_value = True

        should_test_file(sample_file_path, sample_code_content)

        call_args = mock_evaluate_condition.call_args
        content_arg = call_args[1]["content"]
        
        expected_content = f"File path: {sample_file_path}\n\nContent:\n{sample_code_content}"
        assert content_arg == expected_content

    def test_should_test_file_handles_http_error_exception(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that function handles HTTP errors gracefully."""
        import requests
        mock_evaluate_condition.side_effect = requests.HTTPError("HTTP 500 Error")

        result = should_test_file(sample_file_path, sample_code_content)

        # Should return False when HTTP exception occurs (handled by decorator)
        assert result is False
        mock_evaluate_condition.assert_called_once()

    def test_should_test_file_handles_json_decode_error(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that function handles JSON decode errors gracefully."""
        import json
        mock_evaluate_condition.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        result = should_test_file(sample_file_path, sample_code_content)

        # Should return False when JSON decode exception occurs (handled by decorator)
        assert result is False
        mock_evaluate_condition.assert_called_once()

    def test_should_test_file_handles_attribute_error(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that function handles attribute errors gracefully."""
        mock_evaluate_condition.side_effect = AttributeError("'NoneType' object has no attribute 'text'")

        result = should_test_file(sample_file_path, sample_code_content)

        # Should return False when attribute exception occurs (handled by decorator)
        assert result is False
        mock_evaluate_condition.assert_called_once()

    def test_should_test_file_handles_key_error(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that function handles key errors gracefully."""
        mock_evaluate_condition.side_effect = KeyError("missing key")

        result = should_test_file(sample_file_path, sample_code_content)

        # Should return False when key exception occurs (handled by decorator)
        assert result is False
        mock_evaluate_condition.assert_called_once()

    def test_should_test_file_handles_type_error(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that function handles type errors gracefully."""
        mock_evaluate_condition.side_effect = TypeError("unsupported operand type(s)")

        result = should_test_file(sample_file_path, sample_code_content)

        # Should return False when type exception occurs (handled by decorator)
        assert result is False
        mock_evaluate_condition.assert_called_once()

    def test_should_test_file_with_whitespace_only_content(
        self, mock_evaluate_condition, sample_file_path
    ):
        """Test function behavior with whitespace-only content."""
        whitespace_content = "   \n\t\n   \n"
        mock_evaluate_condition.return_value = False

        result = should_test_file(sample_file_path, whitespace_content)

        assert result is False
        mock_evaluate_condition.assert_called_once()
        
        # Verify whitespace content is preserved
        call_args = mock_evaluate_condition.call_args
        content_arg = call_args[1]["content"]
        assert whitespace_content in content_arg

    def test_should_test_file_with_binary_like_content(
        self, mock_evaluate_condition, sample_file_path
    ):
        """Test function behavior with binary-like content."""
        binary_content = "\\x00\\x01\\x02\\xff"
        mock_evaluate_condition.return_value = False

        result = should_test_file(sample_file_path, binary_content)

        assert result is False
        mock_evaluate_condition.assert_called_once()
        
        # Verify binary-like content is passed correctly
        call_args = mock_evaluate_condition.call_args
        content_arg = call_args[1]["content"]
        assert binary_content in content_arg

    def test_should_test_file_return_value_type_consistency(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that function always returns boolean type."""
        test_cases = [True, False, None, "true", "false", 1, 0, [], {}]
        
        for return_value in test_cases:
            mock_evaluate_condition.return_value = return_value
            result = should_test_file(sample_file_path, sample_code_content)
            
            # Should always return a boolean
            assert isinstance(result, bool)
            
            # Should return the actual value for True/False, False for everything else
            if return_value is True:
                assert result is True
            else:
                assert result is False