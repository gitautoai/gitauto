from unittest.mock import patch
from utils.files.should_test_file import should_test_file


def test_should_test_file_returns_true():
    with patch("utils.files.should_test_file.evaluate_condition") as mock_evaluate:
        mock_evaluate.return_value = True

        result = should_test_file(
            file_path="services/calculator.py",
            content="class Calculator:\n    def add(self, a, b):\n        return a + b",
        )

        assert result is True
        mock_evaluate.assert_called_once()


def test_should_test_file_returns_false():
    with patch("utils.files.should_test_file.evaluate_condition") as mock_evaluate:
        mock_evaluate.return_value = False

        result = should_test_file(
            file_path="main.py",
            content="#!/usr/bin/env python\nfrom app import main\nmain()",
        )

        assert result is False


def test_should_test_file_evaluation_fails():
    with patch("utils.files.should_test_file.evaluate_condition") as mock_evaluate:
        mock_evaluate.return_value = None

        result = should_test_file(file_path="test.py", content="some code")

        # Should return False when evaluation fails (avoid generating garbage)
        assert result is False


def test_should_test_file_exception_handling():
    with patch("utils.files.should_test_file.evaluate_condition") as mock_evaluate:
        mock_evaluate.side_effect = Exception("API Error")

        result = should_test_file(file_path="test.py", content="some code")

        # Should return False when exception occurs (handled by decorator)
        assert result is False


def test_should_test_file_passes_correct_content():
    with patch("utils.files.should_test_file.evaluate_condition") as mock_evaluate:
        mock_evaluate.return_value = True

        file_path = "services/user.py"
        content = "def get_user(): return user"

        should_test_file(file_path, content)

        # Verify the content is passed correctly with file path
        call_args = mock_evaluate.call_args
        assert f"File path: {file_path}" in call_args[1]["content"]
        assert content in call_args[1]["content"]


def test_should_test_file_uses_correct_prompt():
    with patch("utils.files.should_test_file.evaluate_condition") as mock_evaluate:
        mock_evaluate.return_value = True

        should_test_file("test.py", "code")

        # Verify the system prompt is correct
        call_args = mock_evaluate.call_args
        system_prompt = call_args[1]["system_prompt"]
        assert "experienced senior engineer" in system_prompt
        assert "practical and strict" in system_prompt
        assert "TRUE" in system_prompt
        assert "FALSE" in system_prompt
