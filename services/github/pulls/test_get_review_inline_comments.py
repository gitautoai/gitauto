# Standard imports
from unittest.mock import MagicMock, patch

# Third party imports
import requests

# Local imports
from services.github.pulls.get_review_inline_comments import get_review_inline_comments

MODULE = "services.github.pulls.get_review_inline_comments"


def test_get_review_inline_comments_success():
    mock_data = [
        {"id": 1, "body": "Fix this line", "path": "src/main.py", "line": 10},
        {"id": 2, "body": "Typo here", "path": "src/utils.py", "line": 5},
    ]
    with patch(f"{MODULE}.requests.get") as mock_get, patch(
        f"{MODULE}.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_data
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer token"}

        result = get_review_inline_comments("owner", "repo", 1, 100, "token")

        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/owner/repo/pulls/1/reviews/100/comments",
            headers={"Authorization": "Bearer token"},
            timeout=120,
        )
        mock_response.raise_for_status.assert_called_once()
        assert result == mock_data
        assert len(result) == 2


def test_get_review_inline_comments_empty():
    with patch(f"{MODULE}.requests.get") as mock_get, patch(
        f"{MODULE}.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer token"}

        result = get_review_inline_comments("owner", "repo", 1, 100, "token")

        assert result == []


def test_get_review_inline_comments_http_error():
    with patch(f"{MODULE}.requests.get") as mock_get, patch(
        f"{MODULE}.create_headers"
    ) as mock_headers:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404"
        )
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer token"}

        result = get_review_inline_comments("owner", "repo", 1, 999, "token")

        assert result is None


def test_get_review_inline_comments_network_error():
    with patch(f"{MODULE}.requests.get") as mock_get, patch(
        f"{MODULE}.create_headers"
    ) as mock_headers:
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        mock_headers.return_value = {"Authorization": "Bearer token"}

        result = get_review_inline_comments("owner", "repo", 1, 100, "token")

        assert result is None
