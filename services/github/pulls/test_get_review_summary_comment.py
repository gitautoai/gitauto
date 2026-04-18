# Standard imports
from unittest.mock import MagicMock, patch

# Third party imports
import requests

# Local imports
from services.github.pulls.get_review_summary_comment import get_review_summary_comment

MODULE = "services.github.pulls.get_review_summary_comment"


def test_get_review_summary_comment_success():
    mock_data = {"id": 100, "body": "Looks good overall", "state": "commented"}
    with patch(f"{MODULE}.requests.get") as mock_get, patch(
        f"{MODULE}.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_data
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer token"}

        result = get_review_summary_comment("owner", "repo", 1, 100, "token")

        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/owner/repo/pulls/1/reviews/100",
            headers={"Authorization": "Bearer token"},
            timeout=120,
        )
        mock_response.raise_for_status.assert_called_once()
        assert result == "Looks good overall"


def test_get_review_summary_comment_http_error():
    with patch(f"{MODULE}.requests.get") as mock_get, patch(
        f"{MODULE}.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404"
        )
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer token"}

        result = get_review_summary_comment("owner", "repo", 1, 999, "token")

        assert result is None


def test_get_review_summary_comment_network_error():
    with patch(f"{MODULE}.requests.get") as mock_get, patch(
        f"{MODULE}.create_headers"
    ) as mock_headers:
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        mock_headers.return_value = {"Authorization": "Bearer token"}

        result = get_review_summary_comment("owner", "repo", 1, 100, "token")

        assert result is None
