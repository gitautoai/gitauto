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
            params={"per_page": 100, "page": 1},
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

        assert not result


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


def test_get_review_inline_comments_paginates():
    """Verify pagination fetches all pages until a partial page is returned."""
    page1 = [{"id": i, "body": f"c{i}", "path": "a.py", "line": i} for i in range(100)]
    page2 = [{"id": 100, "body": "c100", "path": "b.py", "line": 1}]

    with patch(f"{MODULE}.requests.get") as mock_get, patch(
        f"{MODULE}.create_headers"
    ) as mock_headers:
        resp1 = MagicMock()
        resp1.json.return_value = page1
        resp2 = MagicMock()
        resp2.json.return_value = page2
        mock_get.side_effect = [resp1, resp2]
        mock_headers.return_value = {"Authorization": "Bearer token"}

        result = get_review_inline_comments("owner", "repo", 1, 100, "token")

        assert len(result) == 101
        assert result == page1 + page2
        assert mock_get.call_count == 2
        # Verify page params
        assert mock_get.call_args_list[0].kwargs["params"] == {
            "per_page": 100,
            "page": 1,
        }
        assert mock_get.call_args_list[1].kwargs["params"] == {
            "per_page": 100,
            "page": 2,
        }
