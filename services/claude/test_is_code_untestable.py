import json
from unittest.mock import patch

import pytest

from services.claude.is_code_untestable import is_code_untestable
from utils.formatting.format_with_line_numbers import (
    format_content_with_line_numbers,
)


def _build_expected_content(parts: list[str], file_path: str, file_content: str):
    """Reconstruct the content passed to claude so tests can assert exact equality."""
    numbered_file = format_content_with_line_numbers(
        file_path=file_path, content=file_content
    )
    parts_text = "\n".join(parts)
    return (
        f"{parts_text}\n\n{numbered_file}\n\n"
        "Is this code dead (unreachable/redundant) or genuinely untestable "
        "(reachable at runtime but impossible to test)?"
    )


@pytest.fixture
def mock_claude():
    with patch("services.claude.is_code_untestable.claude") as mock:
        yield mock


def _set_mock_response(mock_claude, result: bool, category: str, reason: str):
    """Configure the mock Claude client to return a CodeAnalysisResult."""

    mock_claude.beta.messages.create.return_value.content = [
        type(
            "TextBlock",
            (),
            {
                "text": json.dumps(
                    {"result": result, "category": category, "reason": reason}
                )
            },
        )()
    ]


def test_uses_opus_47_model(mock_claude):
    _set_mock_response(mock_claude, False, "testable", "testable")

    is_code_untestable(
        file_path="src/app.tsx",
        file_content="const x = 1;",
        uncovered_lines="1",
    )

    call_args = mock_claude.beta.messages.create.call_args
    assert call_args.kwargs["model"] == "claude-opus-4-7"


def test_call_kwargs_do_not_include_temperature(mock_claude):
    """Opus 4.7 deprecated temperature (AGENT-3J1/3HG-3J0 cluster on 2026-04-19).
    Including it raises BadRequestError 400."""
    _set_mock_response(mock_claude, False, "testable", "testable")

    is_code_untestable(
        file_path="src/app.tsx",
        file_content="const x = 1;",
        uncovered_lines="1",
    )

    call_args = mock_claude.beta.messages.create.call_args
    assert set(call_args.kwargs.keys()) == {
        "model",
        "max_tokens",
        "system",
        "messages",
        "betas",
        "output_config",
    }


def test_returns_testable_when_no_uncovered_code(mock_claude):
    result = is_code_untestable(
        file_path="src/app.tsx",
        file_content="const x = 1;",
    )
    assert result is not None
    assert result.result is False
    assert result.category == "testable"
    assert result.reason == "No uncovered code provided"
    mock_claude.beta.messages.create.assert_not_called()


def test_extracts_uncovered_lines_from_file_content(mock_claude):
    _set_mock_response(mock_claude, True, "dead_code", "Line 3 is dead code")
    file_content = """line 1
line 2
throw new Error('test');
line 4"""

    is_code_untestable(
        file_path="src/app.tsx",
        file_content=file_content,
        uncovered_lines="3",
    )

    call_args = mock_claude.beta.messages.create.call_args
    content = call_args.kwargs["messages"][0]["content"]
    assert content == _build_expected_content(
        parts=["Uncovered lines:\n```\n3: throw new Error('test');\n```"],
        file_path="src/app.tsx",
        file_content=file_content,
    )


def test_handles_multiple_uncovered_lines(mock_claude):
    _set_mock_response(mock_claude, False, "testable", "testable")
    file_content = "line1\nline2\nline3\nline4\nline5"

    is_code_untestable(
        file_path="src/app.tsx",
        file_content=file_content,
        uncovered_lines="2, 4",
    )

    call_args = mock_claude.beta.messages.create.call_args
    content = call_args.kwargs["messages"][0]["content"]
    assert content == _build_expected_content(
        parts=["Uncovered lines:\n```\n2: line2\n4: line4\n```"],
        file_path="src/app.tsx",
        file_content=file_content,
    )


def test_includes_uncovered_functions(mock_claude):
    _set_mock_response(mock_claude, False, "testable", "testable")
    file_content = "def handleClick(): pass"

    is_code_untestable(
        file_path="src/app.py",
        file_content=file_content,
        uncovered_functions="handleClick, onSubmit",
    )

    call_args = mock_claude.beta.messages.create.call_args
    content = call_args.kwargs["messages"][0]["content"]
    assert content == _build_expected_content(
        parts=["Uncovered functions: handleClick, onSubmit"],
        file_path="src/app.py",
        file_content=file_content,
    )


def test_includes_uncovered_branches(mock_claude):
    _set_mock_response(mock_claude, False, "testable", "testable")
    file_content = "if x { return 1 }"

    is_code_untestable(
        file_path="src/app.go",
        file_content=file_content,
        uncovered_branches="if@10, else@15",
    )

    call_args = mock_claude.beta.messages.create.call_args
    content = call_args.kwargs["messages"][0]["content"]
    assert content == _build_expected_content(
        parts=["Uncovered branches: if@10, else@15"],
        file_path="src/app.go",
        file_content=file_content,
    )


def test_includes_all_uncovered_types(mock_claude):
    _set_mock_response(mock_claude, True, "untestable", "async error handler")
    file_content = "line1\nthrow error\nline3"

    is_code_untestable(
        file_path="src/component.tsx",
        file_content=file_content,
        uncovered_lines="2",
        uncovered_functions="handleError",
        uncovered_branches="catch@5",
    )

    call_args = mock_claude.beta.messages.create.call_args
    content = call_args.kwargs["messages"][0]["content"]
    assert content == _build_expected_content(
        parts=[
            "Uncovered lines:\n```\n2: throw error\n```",
            "Uncovered functions: handleError",
            "Uncovered branches: catch@5",
        ],
        file_path="src/component.tsx",
        file_content=file_content,
    )


def test_returns_dead_code_result(mock_claude):
    _set_mock_response(
        mock_claude,
        True,
        "dead_code",
        "Line 38 is dead - !x already catches empty strings",
    )

    result = is_code_untestable(
        file_path="src/app.tsx",
        file_content="const handleClick = async () => {}",
        uncovered_functions="handleClick",
    )

    assert result is not None
    assert result.result is True
    assert result.category == "dead_code"
    assert result.reason == "Line 38 is dead - !x already catches empty strings"


def test_returns_untestable_result(mock_claude):
    reason = "async error from onClick handler"
    _set_mock_response(mock_claude, True, "untestable", reason)

    result = is_code_untestable(
        file_path="src/app.tsx",
        file_content="const handleClick = async () => {}",
        uncovered_functions="handleClick",
    )

    assert result is not None
    assert result.result is True
    assert result.category == "untestable"
    assert result.reason == reason


def test_skips_invalid_line_numbers(mock_claude):
    _set_mock_response(mock_claude, False, "testable", "testable")
    file_content = "line1\nline2"

    is_code_untestable(
        file_path="src/app.tsx",
        file_content=file_content,
        uncovered_lines="1, 999",  # 999 is out of range
    )

    call_args = mock_claude.beta.messages.create.call_args
    content = call_args.kwargs["messages"][0]["content"]
    assert content == _build_expected_content(
        parts=["Uncovered lines:\n```\n1: line1\n```"],
        file_path="src/app.tsx",
        file_content=file_content,
    )


def test_schema_includes_category_enum(mock_claude):
    _set_mock_response(mock_claude, True, "dead_code", "unreachable")

    is_code_untestable(
        file_path="src/app.tsx",
        file_content="code",
        uncovered_lines="1",
    )

    call_args = mock_claude.beta.messages.create.call_args
    schema = call_args.kwargs["output_config"]["format"]["schema"]
    assert schema["properties"]["category"] == {
        "type": "string",
        "enum": ["dead_code", "untestable", "testable"],
    }


# Skip: Calls real Claude API - run manually to verify dead code detection works
@pytest.mark.skip(reason="Integration test - calls Claude API, costs money")
def test_detects_logic_based_dead_code():
    """Test if Claude detects logic-based dead code with correct category.

    This is the actual code from foxden-shared-lib PR #564:
    - Line 35: if (!resourceParts[2] || !targetParts[2]) return false;
    - Line 38: if (resourceParts[2] === '' || targetParts[2] === '') return false;

    Line 38 is dead code because !x on line 35 already catches empty strings
    ('' is falsy in JavaScript). So line 38 can never execute.
    """
    file_content = """import { AuthorizationError } from '../../errors/authorization-error';
import { User } from '../../tenancy/user';
import { Permission, Role } from '..';
import { AuthorizationHandler } from '.';

export class AgencyAuthorizationHandler implements AuthorizationHandler {
  canHandleResource(resource: string): boolean {
    if (!resource) {
      return false;
    }
    // Matches "/agency/{agencyId}/..."
    const regex = /^\\/agency\\/([a-fA-F0-9]+|\\*)(\\/.*)?$/;
    const testResult = regex.test(resource);
    return testResult;
  }

  private resourceMatches(resource: string, target: string): boolean {
    if (!resource || !target) {
      return false;
    }
    // For now, this will just match on the string with no clever processing.
    // E.g. "/agency/{agencyId}/policy/{policyId}"
    const resourceParts = resource.split('/');
    const targetParts = target.split('/');

    if (resourceParts.length < 2 || targetParts.length < 2) {
      return false;
    }

    if (resourceParts[1] === 'platform') return true;
    if (resourceParts[1] !== 'agency') return false;

    // Check for empty agency ID (e.g., "/agency//something")
    // Note: !resourceParts[2] catches empty strings since '' is falsy
    if (!resourceParts[2] || !targetParts[2]) return false;

    // THIS LINE IS DEAD CODE - the check above already catches empty strings
    if (resourceParts[2] === '' || targetParts[2] === '') return false;

    return resourceParts[2] === '*' || resourceParts[2] === targetParts[2];
  }
}"""

    result = is_code_untestable(
        file_path="src/authorization/authorizers/agencyAuthorizationHandler.handler.ts",
        file_content=file_content,
        uncovered_lines="38",
    )

    assert result is not None
    assert result.result is True, (
        f"Expected Claude to detect dead code. "
        f"Got result={result.result}, reason={result.reason}"
    )
    assert result.category == "dead_code", (
        f"Expected category 'dead_code' but got '{result.category}'. "
        f"Reason: {result.reason}"
    )


# Skip: Calls real Claude API - run manually to verify dead code detection works
@pytest.mark.skip(reason="Integration test - calls Claude API, costs money")
def test_detects_logic_based_dead_code_simple():
    """Test dead code detection with minimal example."""
    file_content = """function check(x: string | undefined): boolean {
  if (!x) return false;
  if (x === '') return false;  // DEAD - !x already caught ''
  return true;
}"""

    result = is_code_untestable(
        file_path="src/utils.ts",
        file_content=file_content,
        uncovered_lines="3",
    )

    assert result is not None
    assert (
        result.result is True
    ), f"Expected dead code detection. Got result={result.result}, reason={result.reason}"
    assert result.category == "dead_code", (
        f"Expected category 'dead_code' but got '{result.category}'. "
        f"Reason: {result.reason}"
    )
