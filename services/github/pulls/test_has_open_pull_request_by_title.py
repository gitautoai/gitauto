# pyright: reportUnusedVariable=false
from unittest.mock import MagicMock, patch

from services.github.pulls.has_open_pull_request_by_title import (
    has_open_pull_request_by_title,
)

MODULE = "services.github.pulls.has_open_pull_request_by_title"


class TestHasOpenPullRequestByTitle:
    @patch(f"{MODULE}.requests.get")
    def test_returns_true_when_pr_exists(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"number": 42, "title": "[GitAuto] Setup Configuration"},
            {"number": 10, "title": "Some other PR"},
        ]
        mock_get.return_value = mock_response

        result = has_open_pull_request_by_title(
            owner="owner", repo="repo", token="token", title="[GitAuto] Setup"
        )

        assert result is True

    @patch(f"{MODULE}.requests.get")
    def test_returns_false_when_no_matching_pr(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"number": 10, "title": "Some other PR"},
        ]
        mock_get.return_value = mock_response

        result = has_open_pull_request_by_title(
            owner="owner", repo="repo", token="token", title="[GitAuto] Setup"
        )

        assert result is False

    @patch(f"{MODULE}.requests.get")
    def test_returns_false_when_no_open_prs(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        result = has_open_pull_request_by_title(
            owner="owner", repo="repo", token="token", title="[GitAuto] Setup"
        )

        assert result is False

    @patch(f"{MODULE}.requests.get")
    def test_calls_correct_api_url(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        has_open_pull_request_by_title(
            owner="myowner", repo="myrepo", token="mytoken", title="Setup"
        )

        called_url = mock_get.call_args[1]["url"]
        assert called_url == "https://api.github.com/repos/myowner/myrepo/pulls"
        assert mock_get.call_args[1]["params"]["state"] == "open"
