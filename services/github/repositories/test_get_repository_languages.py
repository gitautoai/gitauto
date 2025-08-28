from unittest.mock import MagicMock, patch

from requests.exceptions import HTTPError, JSONDecodeError, Timeout
from requests.exceptions import ConnectionError as RequestsConnectionError
from services.github.repositories.get_repository_languages import (
    get_repository_languages,
)


def test_get_repository_languages_success(test_owner, test_repo, test_token):
    """Test get_repository_languages returns correct language data for a successful request."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Python": 12345,
            "JavaScript": 6789,
            "TypeScript": 3456,
        }
        mock_get.return_value = mock_response

        result = get_repository_languages(test_owner, test_repo, test_token)

        assert result == {"Python": 12345, "JavaScript": 6789, "TypeScript": 3456}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_get_repository_languages_empty_response(test_owner, test_repo, test_token):
    """Test get_repository_languages returns empty dict for repository with no languages."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        result = get_repository_languages(test_owner, test_repo, test_token)

        assert result == {}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_get_repository_languages_single_language(test_owner, test_repo, test_token):
    """Test get_repository_languages returns correct data for single language repository."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"Python": 98765}
        mock_get.return_value = mock_response

        result = get_repository_languages(test_owner, test_repo, test_token)

        assert result == {"Python": 98765}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_get_repository_languages_http_error_404(test_owner, test_token):
    """Test get_repository_languages returns empty dict when repository not found (404)."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
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

        result = get_repository_languages(test_owner, "non-existent-repo", test_token)

        assert result == {}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_get_repository_languages_http_error_403(test_token):
    """Test get_repository_languages returns empty dict when access forbidden (403)."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"
        mock_response.text = "Repository access blocked"
        mock_response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Used": "1",
        }

        http_error = HTTPError("403 Client Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error

        mock_get.return_value = mock_response

        result = get_repository_languages("private-owner", "private-repo", test_token)

        assert result == {}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_get_repository_languages_json_decode_error(test_owner, test_repo, test_token):
    """Test get_repository_languages returns empty dict when JSON decode fails."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "{", 0)
        mock_get.return_value = mock_response

        result = get_repository_languages(test_owner, test_repo, test_token)

        assert result == {}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_get_repository_languages_timeout(test_owner, test_repo, test_token):
    """Test get_repository_languages returns empty dict when request times out."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_get.side_effect = Timeout("Request timed out")

        result = get_repository_languages(test_owner, test_repo, test_token)

        assert result == {}
        mock_get.assert_called_once()


def test_get_repository_languages_connection_error(test_owner, test_repo, test_token):
    """Test get_repository_languages returns empty dict when connection fails."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_get.side_effect = RequestsConnectionError("Connection failed")

        result = get_repository_languages(test_owner, test_repo, test_token)

        assert result == {}
        mock_get.assert_called_once()


def test_get_repository_languages_api_call_parameters(
    test_owner, test_repo, test_token
):
    """Test get_repository_languages makes correct API call with proper parameters."""
    with patch(
        "services.github.repositories.get_repository_languages.get"
    ) as mock_get, patch(
        "services.github.repositories.get_repository_languages.create_headers"
    ) as mock_create_headers:

        mock_response = MagicMock()
        mock_response.json.return_value = {"Python": 12345}
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}

        result = get_repository_languages(test_owner, test_repo, test_token)

        # Verify the API call was made with correct parameters
        mock_create_headers.assert_called_once_with(token=test_token)
        mock_get.assert_called_once()

        # Check the call arguments
        call_args = mock_get.call_args
        assert "url" in call_args.kwargs
        assert f"/repos/{test_owner}/{test_repo}/languages" in call_args.kwargs["url"]
        assert "headers" in call_args.kwargs
        assert "timeout" in call_args.kwargs

        assert result == {"Python": 12345}


def test_get_repository_languages_with_create_headers_mock(
    test_owner, test_repo, test_token
):
    """Test get_repository_languages with mocked create_headers function."""
    with patch(
        "services.github.repositories.get_repository_languages.get"
    ) as mock_get, patch(
        "services.github.repositories.get_repository_languages.create_headers"
    ) as mock_create_headers:

        mock_response = MagicMock()
        mock_response.json.return_value = {"Python": 12345}
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}

        result = get_repository_languages(test_owner, test_repo, test_token)

        # Verify the API call was made with correct parameters
        mock_create_headers.assert_called_once_with(token=test_token)
        mock_get.assert_called_once()

        assert result == {"Python": 12345}


def test_get_repository_languages_large_repository(test_owner, test_repo, test_token):
    """Test get_repository_languages with a large repository having many languages."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Python": 1234567,
            "JavaScript": 987654,
            "TypeScript": 456789,
            "HTML": 234567,
            "CSS": 123456,
            "Shell": 12345,
            "Dockerfile": 1234,
            "YAML": 567,
        }
        mock_get.return_value = mock_response

        result = get_repository_languages(test_owner, test_repo, test_token)

        assert len(result) == 8
        assert result["Python"] == 1234567
        assert result["JavaScript"] == 987654
        assert isinstance(result, dict)
        assert all(isinstance(k, str) and isinstance(v, int) for k, v in result.items())


def test_get_repository_languages_http_error_500(test_owner, test_repo, test_token):
    """Test get_repository_languages returns empty dict when server error occurs (500)."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Internal server error"
        mock_response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Used": "1",
        }

        http_error = HTTPError("500 Server Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error

        mock_get.return_value = mock_response

        result = get_repository_languages(test_owner, test_repo, test_token)

        assert result == {}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_get_repository_languages_attribute_error(test_owner, test_repo, test_token):
    """Test get_repository_languages returns empty dict when AttributeError occurs."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.side_effect = AttributeError(
            "'NoneType' object has no attribute 'json'"
        )
        mock_get.return_value = mock_response

        result = get_repository_languages(test_owner, test_repo, test_token)

        assert result == {}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_get_repository_languages_key_error(test_owner, test_repo, test_token):
    """Test get_repository_languages returns empty dict when KeyError occurs."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.side_effect = KeyError("Missing key in response")
        mock_get.return_value = mock_response

        result = get_repository_languages(test_owner, test_repo, test_token)

        assert result == {}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
