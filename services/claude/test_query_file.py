# pyright: reportCallIssue=false
import os
from unittest.mock import patch

from services.claude.query_file import query_file

# Use this repo's own file as test input
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REAL_FILE = "services/claude/query_file.py"


def make_base_args(clone_dir: str = REPO_ROOT):
    return {"clone_dir": clone_dir, "usage_id": 0}


@patch("services.claude.query_file.chat_with_claude_simple")
def test_query_file_returns_haiku_answer(mock_haiku):
    """Valid file sends content to Haiku and returns its answer."""
    mock_haiku.return_value = "This file defines a query_file tool for GitAuto."

    result = query_file(
        file_path=REAL_FILE,
        prompt="What does this file do?",
        base_args=make_base_args(),
    )

    assert result == "This file defines a query_file tool for GitAuto."
    mock_haiku.assert_called_once()
    call_kwargs = mock_haiku.call_args
    assert REAL_FILE in call_kwargs.kwargs["user_input"]
    assert "What does this file do?" in call_kwargs.kwargs["user_input"]


def test_query_file_nonexistent_returns_error():
    """Nonexistent file returns error without calling Haiku."""
    result = query_file(
        file_path="nonexistent/file.py",
        prompt="anything",
        base_args=make_base_args(),
    )

    assert (
        result
        == "File not found: 'nonexistent/file.py'. Check the file path and try again."
    )


@patch("services.claude.query_file.chat_with_claude_simple")
def test_query_file_passes_haiku_model(mock_haiku):
    """Verifies Haiku 4.5 model is used, not the default Sonnet."""
    mock_haiku.return_value = "answer"

    query_file(
        file_path=REAL_FILE,
        prompt="test",
        base_args=make_base_args(),
    )

    call_kwargs = mock_haiku.call_args.kwargs
    assert call_kwargs["model_id"] == "claude-haiku-4-5"
