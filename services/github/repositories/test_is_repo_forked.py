from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError, JSONDecodeError, Timeout
from services.github.repositories.is_repo_forked import is_repo_forked


def test_is_repo_forked_true(test_owner, test_repo, test_token):
    """Test is_repo_forked returns True for a forked repository."""
    with patch("services.github.repositories.is_repo_forked.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"fork": True}
        mock_get.return_value = mock_response

        result = is_repo_forked(test_owner, test_repo, test_token)

        assert result is True
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_is_repo_forked_false(test_owner, test_repo, test_token):
    """Test is_repo_forked returns False for a non-forked repository."""
    with patch("services.github.repositories.is_repo_forked.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"fork": False}
        mock_get.return_value = mock_response

        result = is_repo_forked(test_owner, test_repo, test_token)

        assert result is False
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_is_repo_forked_http_error(test_owner, test_token):
    """Test is_repo_forked returns False when an HTTPError occurs."""
    with patch("services.github.repositories.is_repo_forked.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Repository not found"
        mock_response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Used": "1",
        }

        http_error = HTTPError("404 Client Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error

        mock_get.return_value = mock_response

        result = is_repo_forked(test_owner, "non-existent-repo", test_token)

        assert result is False
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_is_repo_forked_json_decode_error(test_owner, test_repo, test_token):
    """Test is_repo_forked returns False when a JSONDecodeError occurs."""
    with patch("services.github.repositories.is_repo_forked.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "{", 0)
        mock_get.return_value = mock_response

        result = is_repo_forked(test_owner, test_repo, test_token)

        assert result is False
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_is_repo_forked_timeout(test_owner, test_repo, test_token):
    """Test is_repo_forked returns False when a Timeout occurs."""
    with patch("services.github.repositories.is_repo_forked.get") as mock_get:
        mock_get.side_effect = Timeout("Request timed out")

        result = is_repo_forked(test_owner, test_repo, test_token)

        assert result is False
        mock_get.assert_called_once()


def test_is_repo_forked_key_error(test_owner, test_repo, test_token):
    """Test is_repo_forked returns False when a KeyError occurs."""
    with patch("services.github.repositories.is_repo_forked.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {}  # Missing 'fork' key
        mock_get.return_value = mock_response

        result = is_repo_forked(test_owner, test_repo, test_token)

        assert result is False
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
