# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import MagicMock, patch

from services.github.pulls.reopen_pull_request import reopen_pull_request

MODULE = "services.github.pulls.reopen_pull_request"


@patch(f"{MODULE}.requests.patch")
def test_reopens_pr(mock_patch):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_patch.return_value = mock_response

    result = reopen_pull_request(owner="owner", repo="repo", pr_number=42, token="tok")

    assert result is True
    call_kwargs = mock_patch.call_args[1]
    assert call_kwargs["json"] == {"state": "open"}


@patch(f"{MODULE}.requests.patch")
def test_returns_false_on_error(mock_patch):
    mock_patch.side_effect = Exception("API error")

    result = reopen_pull_request(owner="owner", repo="repo", pr_number=42, token="tok")

    assert result is False
