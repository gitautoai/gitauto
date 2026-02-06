from unittest.mock import patch

import pytest

from services.claude.evaluate_condition import EvaluationResult
from services.claude.is_code_untestable import is_code_untestable


@pytest.fixture
def mock_evaluate():
    with patch("services.claude.is_code_untestable.evaluate_condition") as mock:
        yield mock


def test_returns_false_when_no_uncovered_code(mock_evaluate):
    eval_result = is_code_untestable(
        file_path="src/app.tsx",
        file_content="const x = 1;",
    )
    assert eval_result.result is False
    assert eval_result.reason == "No uncovered code provided"
    mock_evaluate.assert_not_called()


def test_extracts_uncovered_lines_from_file_content(mock_evaluate):
    mock_evaluate.return_value = EvaluationResult(True, "async error handler")
    file_content = """line 1
line 2
throw new Error('test');
line 4"""

    is_code_untestable(
        file_path="src/app.tsx",
        file_content=file_content,
        uncovered_lines="3",
    )

    call_args = mock_evaluate.call_args
    content = call_args.kwargs["content"]
    assert "3: throw new Error('test');" in content


def test_handles_multiple_uncovered_lines(mock_evaluate):
    mock_evaluate.return_value = EvaluationResult(False, "testable")
    file_content = "line1\nline2\nline3\nline4\nline5"

    is_code_untestable(
        file_path="src/app.tsx",
        file_content=file_content,
        uncovered_lines="2, 4",
    )

    call_args = mock_evaluate.call_args
    content = call_args.kwargs["content"]
    assert "2: line2" in content
    assert "4: line4" in content


def test_includes_uncovered_functions(mock_evaluate):
    mock_evaluate.return_value = EvaluationResult(False, "testable")

    is_code_untestable(
        file_path="src/app.py",
        file_content="def handleClick(): pass",
        uncovered_functions="handleClick, onSubmit",
    )

    call_args = mock_evaluate.call_args
    content = call_args.kwargs["content"]
    assert "Uncovered functions: handleClick, onSubmit" in content


def test_includes_uncovered_branches(mock_evaluate):
    mock_evaluate.return_value = EvaluationResult(False, "testable")

    is_code_untestable(
        file_path="src/app.go",
        file_content="if x { return 1 }",
        uncovered_branches="if@10, else@15",
    )

    call_args = mock_evaluate.call_args
    content = call_args.kwargs["content"]
    assert "Uncovered branches: if@10, else@15" in content


def test_includes_all_uncovered_types(mock_evaluate):
    mock_evaluate.return_value = EvaluationResult(True, "untestable")
    file_content = "line1\nthrow error\nline3"

    is_code_untestable(
        file_path="src/component.tsx",
        file_content=file_content,
        uncovered_lines="2",
        uncovered_functions="handleError",
        uncovered_branches="catch@5",
    )

    call_args = mock_evaluate.call_args
    content = call_args.kwargs["content"]
    assert "Uncovered lines:" in content
    assert "Uncovered functions: handleError" in content
    assert "Uncovered branches: catch@5" in content


def test_returns_evaluation_result(mock_evaluate):
    mock_evaluate.return_value = EvaluationResult(
        True, "async error in onClick handler"
    )

    eval_result = is_code_untestable(
        file_path="src/app.tsx",
        file_content="const handleClick = async () => {}",
        uncovered_functions="handleClick",
    )

    assert eval_result.result is True
    assert eval_result.reason == "async error in onClick handler"


def test_skips_invalid_line_numbers(mock_evaluate):
    mock_evaluate.return_value = EvaluationResult(False, "testable")
    file_content = "line1\nline2"

    is_code_untestable(
        file_path="src/app.tsx",
        file_content=file_content,
        uncovered_lines="1, 999",  # 999 is out of range
    )

    call_args = mock_evaluate.call_args
    content = call_args.kwargs["content"]
    assert "1: line1" in content
    assert "999" not in content
