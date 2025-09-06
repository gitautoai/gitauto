# pylint: disable=redefined-outer-name
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
