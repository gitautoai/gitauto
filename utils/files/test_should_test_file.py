import pytest
from unittest.mock import patch
from utils.files.should_test_file import should_test_file


class TestShouldTestFile:
    """Test suite for should_test_file function."""

    @pytest.fixture
    def mock_evaluate_condition(self):
        """Fixture to provide a mocked evaluate_condition."""
        with patch("utils.files.should_test_file.evaluate_condition") as mock:
            yield mock

    def test_should_test_file_returns_true(self, mock_evaluate_condition):
        """Test that function returns True when evaluate_condition returns True."""
        mock_evaluate_condition.return_value = True

        result = should_test_file(
            file_path="services/calculator.py",
            content="class Calculator:\n    def add(self, a, b):\n        return a + b",
        )

        assert result is True
        mock_evaluate_condition.assert_called_once()

    def test_should_test_file_returns_false(self, mock_evaluate_condition):
        """Test that function returns False when evaluate_condition returns False."""
        mock_evaluate_condition.return_value = False

        result = should_test_file(
            file_path="main.py",
            content="#!/usr/bin/env python\nfrom app import main\nmain()",
        )

        assert result is False

    def test_should_test_file_evaluation_fails(self, mock_evaluate_condition):
        """Test that function returns False when evaluation returns None."""
        mock_evaluate_condition.return_value = None

        result = should_test_file(file_path="test.py", content="some code")

        assert result is False

    def test_should_test_file_exception_handling(self, mock_evaluate_condition):
        """Test that function returns False when exception occurs (handled by decorator)."""
        mock_evaluate_condition.side_effect = Exception("API Error")

        result = should_test_file(file_path="test.py", content="some code")

        assert result is False

    def test_should_test_file_passes_correct_content(self, mock_evaluate_condition):
        """Test that the content is formatted and passed correctly to evaluate_condition."""
        mock_evaluate_condition.return_value = True

        file_path = "services/user.py"
        content = "def get_user(): return user"

        should_test_file(file_path, content)

        call_args = mock_evaluate_condition.call_args
        assert f"File path: {file_path}" in call_args[1]["content"]
        assert content in call_args[1]["content"]

    def test_should_test_file_uses_correct_prompt(self, mock_evaluate_condition):
        """Test that the correct system prompt is used."""
        mock_evaluate_condition.return_value = True

        should_test_file("test.py", "code")

        call_args = mock_evaluate_condition.call_args
        system_prompt = call_args[1]["system_prompt"]
        assert "experienced senior engineer" in system_prompt
        assert "practical and strict" in system_prompt
        assert "TRUE" in system_prompt
        assert "FALSE" in system_prompt

    def test_should_test_file_with_empty_file_path(self, mock_evaluate_condition):
        """Test behavior with empty file path."""
        mock_evaluate_condition.return_value = True

        result = should_test_file("", "def function(): pass")

        assert result is True
        call_args = mock_evaluate_condition.call_args
        assert "File path: " in call_args[1]["content"]

    def test_should_test_file_with_empty_content(self, mock_evaluate_condition):
        """Test behavior with empty content."""
        mock_evaluate_condition.return_value = False

        result = should_test_file("utils/empty.py", "")

        assert result is False
        call_args = mock_evaluate_condition.call_args
        assert "Content:\n" in call_args[1]["content"]

    def test_should_test_file_with_whitespace_only_content(self, mock_evaluate_condition):
        """Test behavior with whitespace-only content."""
        mock_evaluate_condition.return_value = False

        result = should_test_file("utils/whitespace.py", "   \n\t  \n  ")

        assert result is False

    def test_should_test_file_with_complex_file_path(self, mock_evaluate_condition):
        """Test with complex file path containing special characters."""
        mock_evaluate_condition.return_value = True

        file_path = "services/api/v1/users/user-management_service.py"
        content = "class UserService:\n    def create_user(self): pass"

        result = should_test_file(file_path, content)

        assert result is True
        call_args = mock_evaluate_condition.call_args
        assert file_path in call_args[1]["content"]

    def test_should_test_file_with_multiline_content(self, mock_evaluate_condition):
        """Test with realistic multiline code content."""
        mock_evaluate_condition.return_value = True

        content = """
from typing import Optional

class DatabaseManager:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
    
    def connect(self) -> bool:
        try:
            # Connection logic here
            return True
        except Exception:
            return False
    
    def execute_query(self, query: str) -> Optional[list]:
        if not self.connection:
            return None
        # Query execution logic
        return []
"""

        result = should_test_file("services/database.py", content)

        assert result is True
        call_args = mock_evaluate_condition.call_args
        assert "DatabaseManager" in call_args[1]["content"]
        assert "execute_query" in call_args[1]["content"]

    def test_should_test_file_content_formatting(self, mock_evaluate_condition):
        """Test that content is formatted correctly with file path and content sections."""
        mock_evaluate_condition.return_value = True

        file_path = "utils/helper.py"
        content = "def helper_function():\n    return 'help'"

        should_test_file(file_path, content)

        call_args = mock_evaluate_condition.call_args
        formatted_content = call_args[1]["content"]
        
        # Verify the exact format
        expected_content = f"File path: {file_path}\n\nContent:\n{content}"
        assert formatted_content == expected_content

    def test_should_test_file_system_prompt_content(self, mock_evaluate_condition):
        """Test the complete system prompt content."""
        mock_evaluate_condition.return_value = True

        should_test_file("test.py", "code")

        call_args = mock_evaluate_condition.call_args
        system_prompt = call_args[1]["system_prompt"]
        
        expected_prompt = """You are a very experienced senior engineer. Look at this code and decide if it needs unit tests.

Be practical and strict - only return TRUE if the code has actual logic worth testing.

Return FALSE for trivial code that doesn't need tests."""
        
        assert system_prompt == expected_prompt

    def test_should_test_file_with_various_return_types(self, mock_evaluate_condition):
        """Test behavior with different return types from evaluate_condition."""
        test_cases = [
            (True, True),
            (False, False),
            (None, False),
            ("true", "true"),  # Non-boolean return should be returned as-is if not None
            ("false", "false"),
            (1, 1),
            (0, 0),
        ]

        for mock_return, expected_result in test_cases:
            mock_evaluate_condition.return_value = mock_return
            
            result = should_test_file("test.py", "code")
            
            if mock_return is None:
                assert result is False
            else:
                assert result == expected_result

    def test_should_test_file_called_with_correct_parameters(self, mock_evaluate_condition):
        """Test that evaluate_condition is called with exactly the expected parameters."""
        mock_evaluate_condition.return_value = True

        file_path = "services/auth.py"
        content = "def authenticate(): pass"

        should_test_file(file_path, content)

        # Verify it was called exactly once with the right parameters
        mock_evaluate_condition.assert_called_once_with(
            content=f"File path: {file_path}\n\nContent:\n{content}",
            system_prompt="""You are a very experienced senior engineer. Look at this code and decide if it needs unit tests.

Be practical and strict - only return TRUE if the code has actual logic worth testing.

Return FALSE for trivial code that doesn't need tests.""",
        )

    def test_should_test_file_with_unicode_content(self, mock_evaluate_condition):
        """Test behavior with unicode characters in content."""
        mock_evaluate_condition.return_value = True

        content = "def greet():\n    return '你好世界! 🌍'"
        
        result = should_test_file("utils/greet.py", content)

        assert result is True
        call_args = mock_evaluate_condition.call_args
        assert "你好世界! 🌍" in call_args[1]["content"]

    def test_should_test_file_preserves_newlines_and_formatting(self, mock_evaluate_condition):
        """Test that newlines and formatting in content are preserved."""
        mock_evaluate_condition.return_value = True

        content = "def func():\n    # Comment\n    \n    return True\n\n\ndef another():\n    pass"
        
        should_test_file("test.py", content)

        call_args = mock_evaluate_condition.call_args
        passed_content = call_args[1]["content"]
        
        # Verify the original content formatting is preserved
        assert content in passed_content
        assert passed_content.count('\n') >= content.count('\n')