# pylint: disable=unused-argument
from typing import cast
from unittest.mock import patch

from services.github.types.github_types import BaseArgs
from services.tsc.create_tsc_issue import create_tsc_issue


def _make_base_args():
    return cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "token": "test-token",
        },
    )


@patch("services.tsc.create_tsc_issue.issue_exists", return_value=False)
@patch("services.tsc.create_tsc_issue.create_issue")
def test_creates_issue_when_none_exists(mock_create_issue, mock_exists):
    mock_create_issue.return_value = (200, {"html_url": "https://github.com/test/1"})

    create_tsc_issue(
        base_args=_make_base_args(),
        unrelated_errors=["src/a.ts(10,5): error TS2339: Property 'x' does not exist"],
    )

    mock_create_issue.assert_called_once()
    call_kwargs = mock_create_issue.call_args.kwargs
    assert call_kwargs["labels"] == []
    assert "Pre-existing TypeScript" in call_kwargs["body"]
    assert "src/a.ts" in call_kwargs["body"]


@patch("services.tsc.create_tsc_issue.issue_exists", return_value=True)
@patch("services.tsc.create_tsc_issue.create_issue")
def test_skips_when_issue_exists(mock_create_issue, mock_exists):
    create_tsc_issue(
        base_args=_make_base_args(),
        unrelated_errors=["src/a.ts(10,5): error TS2339: Property 'x' does not exist"],
    )

    mock_create_issue.assert_not_called()


@patch("services.tsc.create_tsc_issue.issue_exists", return_value=False)
@patch("services.tsc.create_tsc_issue.create_issue")
def test_caps_errors_at_50(mock_create_issue, mock_exists):
    mock_create_issue.return_value = (200, {"html_url": "https://github.com/test/1"})

    errors = [f"file{i}.ts(1,1): error TS0000: msg" for i in range(100)]
    create_tsc_issue(
        base_args=_make_base_args(),
        unrelated_errors=errors,
    )

    call_kwargs = mock_create_issue.call_args.kwargs
    assert "100 total" in call_kwargs["body"]
    assert "... and 50 more" in call_kwargs["body"]


@patch("services.tsc.create_tsc_issue.issue_exists", return_value=False)
@patch("services.tsc.create_tsc_issue.create_issue")
def test_handles_issues_disabled(mock_create_issue, mock_exists):
    mock_create_issue.return_value = (410, None)

    create_tsc_issue(
        base_args=_make_base_args(),
        unrelated_errors=["src/a.ts(10,5): error TS2339: msg"],
    )

    mock_create_issue.assert_called_once()
