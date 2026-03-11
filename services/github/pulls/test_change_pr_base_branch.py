# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import patch, MagicMock

import pytest

from services.github.pulls.change_pr_base_branch import change_pr_base_branch
from services.github.types.github_types import BaseArgs


@pytest.fixture
def base_args():
    return cast(
        BaseArgs,
        {
            "owner": "test_owner",
            "repo": "test_repo",
            "token": "test_token",
            "pr_number": 42,
        },
    )


class TestChangePrBaseBranch:
    @patch("services.github.pulls.change_pr_base_branch.requests.patch")
    def test_changes_base_branch(self, mock_patch, base_args):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_response

        result = change_pr_base_branch(base_args=base_args, new_base_branch="develop")

        assert result == "Changed base branch of PR #42 to 'develop'"
        mock_patch.assert_called_once_with(
            url="https://api.github.com/repos/test_owner/test_repo/pulls/42",
            headers=mock_patch.call_args[1]["headers"],
            json={"base": "develop"},
            timeout=120,
        )

    @patch("services.github.pulls.change_pr_base_branch.requests.patch")
    def test_calls_correct_url(self, mock_patch, base_args):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_response

        change_pr_base_branch(base_args=base_args, new_base_branch="staging")

        call_kwargs = mock_patch.call_args[1]
        assert (
            call_kwargs["url"]
            == "https://api.github.com/repos/test_owner/test_repo/pulls/42"
        )
        assert call_kwargs["json"] == {"base": "staging"}

    @patch("services.github.pulls.change_pr_base_branch.requests.patch")
    def test_returns_none_on_error(self, mock_patch, base_args):
        mock_patch.side_effect = Exception("API error")

        result = change_pr_base_branch(base_args=base_args, new_base_branch="develop")

        assert result is None
