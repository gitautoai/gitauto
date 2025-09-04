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
        """Test function behavior when file_path is None."""
        mock_evaluate_condition.return_value = True

        # This should handle None gracefully due to f-string conversion
        result = should_test_file(None, sample_code_content)

        assert result is True
        mock_evaluate_condition.assert_called_once()
        
        # Verify None is converted to string in f-string
        call_args = mock_evaluate_condition.call_args
        content_arg = call_args[1]["content"]
        assert "File path: None\n\nContent:\n" in content_arg

    def test_should_test_file_with_none_content(
        self, mock_evaluate_condition, sample_file_path
    ):
        """Test function behavior when content is None."""
        mock_evaluate_condition.return_value = False

        # This should handle None gracefully due to f-string conversion
        result = should_test_file(sample_file_path, None)

        assert result is False
        mock_evaluate_condition.assert_called_once()
        
        # Verify None is converted to string in f-string
        call_args = mock_evaluate_condition.call_args
        content_arg = call_args[1]["content"]
        assert f"File path: {sample_file_path}\n\nContent:\nNone" == content_arg

    def test_should_test_file_return_type_consistency(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that function always returns a boolean type."""
        test_cases = [True, False, None, "true", "false", 1, 0, [], {}]
        
        for return_value in test_cases:
            mock_evaluate_condition.return_value = return_value
            result = should_test_file(sample_file_path, sample_code_content)
            
            # Should always return a boolean
            assert isinstance(result, bool)
            
            # Should return False for any non-True value (including None)
            if return_value is True:
                assert result is True
            else:

    def test_should_test_file_system_prompt_immutability(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that the system prompt is consistent across multiple calls."""
        mock_evaluate_condition.return_value = True
        
        # Make multiple calls
        should_test_file(sample_file_path, sample_code_content)
        first_call_prompt = mock_evaluate_condition.call_args[1]["system_prompt"]
        
        should_test_file("different_file.py", "different content")
        second_call_prompt = mock_evaluate_condition.call_args[1]["system_prompt"]
        
        # System prompt should be identical across calls
        assert first_call_prompt == second_call_prompt
        assert mock_evaluate_condition.call_count == 2

    def test_should_test_file_large_content_handling(
        self, mock_evaluate_condition, sample_file_path
    ):
        """Test function behavior with very large content."""
        # Create a large content string (simulating a large file)
        large_content = "def function_{}():\n    return {}\n\n".format("x", "x") * 1000
        mock_evaluate_condition.return_value = True

        result = should_test_file(sample_file_path, large_content)

        assert result is True
        mock_evaluate_condition.assert_called_once()
        
        # Verify large content is passed correctly
        call_args = mock_evaluate_condition.call_args
        content_arg = call_args[1]["content"]
        assert large_content in content_arg
        assert len(content_arg) > len(large_content)  # Should include file path prefix

    def test_should_test_file_unicode_file_path(
        self, mock_evaluate_condition, sample_code_content
    ):
        """Test function behavior with unicode characters in file path."""
        unicode_file_path = "services/测试文件.py"
        mock_evaluate_condition.return_value = True

        result = should_test_file(unicode_file_path, sample_code_content)

        assert result is True
        mock_evaluate_condition.assert_called_once()
        
        # Verify unicode file path is preserved
        call_args = mock_evaluate_condition.call_args
        content_arg = call_args[1]["content"]
        assert f"File path: {unicode_file_path}" in content_arg

    def test_should_test_file_whitespace_only_content(
        self, mock_evaluate_condition, sample_file_path
    ):
        """Test function behavior with whitespace-only content."""
        whitespace_content = "   \n\t\n   \n\t\t  \n"
        mock_evaluate_condition.return_value = False

        result = should_test_file(sample_file_path, whitespace_content)

        assert result is False
        mock_evaluate_condition.assert_called_once()
        
        # Verify whitespace content is preserved exactly

        call_args = mock_evaluate_condition.call_args
        content_arg = call_args[1]["content"]
        assert whitespace_content in content_arg
    def test_should_test_file_mock_reset_between_tests(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that mock is properly reset between test calls."""
        # First call
        mock_evaluate_condition.return_value = True
        result1 = should_test_file(sample_file_path, sample_code_content)
        assert result1 is True
        assert mock_evaluate_condition.call_count == 1
        
        # Reset mock and make second call
        mock_evaluate_condition.reset_mock()
        mock_evaluate_condition.return_value = False
        result2 = should_test_file(sample_file_path, sample_code_content)
        assert result2 is False
        assert mock_evaluate_condition.call_count == 1  # Should be 1 after reset

    def test_should_test_file_content_format_edge_cases(
        self, mock_evaluate_condition
    ):
        """Test content formatting with various edge case inputs."""
        test_cases = [
            ("", ""),  # Both empty
            ("file.py", ""),  # Empty content
            ("", "content"),  # Empty file path
            ("file with spaces.py", "content with\nnewlines"),  # Spaces and newlines
            ("file.py", "content\r\nwith\r\nwindows\r\nline\r\nendings"),  # Windows line endings
        ]
        
        mock_evaluate_condition.return_value = True
        
        for file_path, content in test_cases:
            should_test_file(file_path, content)
            
            call_args = mock_evaluate_condition.call_args
            content_arg = call_args[1]["content"]
            
            # Verify format is always consistent
            expected_start = f"File path: {file_path}\n\nContent:\n"
            assert content_arg.startswith(expected_start)
            assert content_arg == f"{expected_start}{content}"
            
            mock_evaluate_condition.reset_mock()

    def test_should_test_file_function_signature_compliance(
        self, mock_evaluate_condition, sample_file_path, sample_code_content
    ):
        """Test that function signature is correctly typed and behaves as expected."""
        mock_evaluate_condition.return_value = True
        
        # Test with proper types
        result = should_test_file(sample_file_path, sample_code_content)
        assert isinstance(result, bool)
        assert result is True
        
        # Test return type annotation compliance
        import inspect
        from utils.files.should_test_file import should_test_file as func
        
        sig = inspect.signature(func)
        assert sig.return_annotation == bool
        
        # Check parameter annotations
        params = sig.parameters
        assert params['file_path'].annotation == str
        assert params['content'].annotation == str

    def test_should_test_file_integration_with_real_scenarios(
        self, mock_evaluate_condition
    ):
        """Test function with realistic file scenarios."""
        realistic_scenarios = [
            ("utils/helpers.py", "def format_date(date):\n    return date.strftime('%Y-%m-%d')"),
            ("models/user.py", "class User:\n    def __init__(self, name):\n        self.name = name"),
            ("config.py", "DEBUG = True\nDATABASE_URL = 'sqlite:///app.db'"),
            ("__init__.py", ""),
            ("main.py", "if __name__ == '__main__':\n    app.run()"),
        ]
        
        for file_path, content in realistic_scenarios:
            # Test both True and False scenarios
            for expected_result in [True, False]:
                mock_evaluate_condition.return_value = expected_result
                result = should_test_file(file_path, content)
                
                assert result == expected_result
                mock_evaluate_condition.assert_called_once()
                
                # Verify content is formatted correctly for each scenario
                call_args = mock_evaluate_condition.call_args
                content_arg = call_args[1]["content"]
                assert f"File path: {file_path}" in content_arg
                assert content in content_arg
                
