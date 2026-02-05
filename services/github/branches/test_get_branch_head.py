from unittest.mock import MagicMock, patch

from config import TIMEOUT
from services.github.branches.get_branch_head import get_branch_head


def test_get_branch_head_returns_sha():
    """Test get_branch_head returns the HEAD commit SHA."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"commit": {"sha": "abc1234567890def"}}

    with patch(
        "services.github.branches.get_branch_head.create_headers"
    ) as mock_headers, patch(
        "services.github.branches.get_branch_head.requests.get"
    ) as mock_get:
        mock_headers.return_value = {"Authorization": "Bearer fake-token"}
        mock_get.return_value = mock_response

        result = get_branch_head(
            owner="test-owner", repo="test-repo", branch="main", token="fake-token"
        )

        assert result == "abc1234567890def"
        mock_headers.assert_called_once_with(token="fake-token")
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args.kwargs
        assert "test-owner" in call_kwargs["url"]
        assert "test-repo" in call_kwargs["url"]
        assert "main" in call_kwargs["url"]
        assert call_kwargs["timeout"] == TIMEOUT


def test_get_branch_head_returns_none_on_missing_commit():
    """Test get_branch_head returns None when commit data is missing."""
    mock_response = MagicMock()
    mock_response.json.return_value = {}

    with patch("services.github.branches.get_branch_head.requests.get") as mock_get:
        mock_get.return_value = mock_response

        result = get_branch_head(
            owner="test-owner", repo="test-repo", branch="main", token="fake-token"
        )

        assert result is None


def test_get_branch_head_returns_none_on_error():
    """Test get_branch_head returns None when request fails."""
    with patch("services.github.branches.get_branch_head.requests.get") as mock_get:
        mock_get.side_effect = Exception("API error")

        result = get_branch_head(
            owner="test-owner", repo="test-repo", branch="main", token="fake-token"
        )

        assert result is None
