from unittest.mock import patch, MagicMock
import pytest
from requests.exceptions import HTTPError, JSONDecodeError, Timeout, ConnectionError
from services.github.repositories.get_repository_languages import get_repository_languages
from tests.constants import OWNER, REPO, TOKEN


def test_get_repository_languages_success():
    """Test get_repository_languages returns correct language data for a successful request."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Python": 12345,
            "JavaScript": 6789,
            "TypeScript": 3456
        }
        mock_get.return_value = mock_response
        
        result = get_repository_languages(OWNER, REPO, TOKEN)
        
        assert result == {
            "Python": 12345,
            "JavaScript": 6789,
            "TypeScript": 3456
        }
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_get_repository_languages_empty_response():
    """Test get_repository_languages returns empty dict for repository with no languages."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        
        result = get_repository_languages(OWNER, REPO, TOKEN)
        
        assert result == {}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_get_repository_languages_single_language():
    """Test get_repository_languages returns correct data for single language repository."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"Python": 98765}
        mock_get.return_value = mock_response
        
        result = get_repository_languages(OWNER, REPO, TOKEN)
        
        assert result == {"Python": 98765}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_get_repository_languages_http_error_404():
    """Test get_repository_languages returns empty dict when repository not found (404)."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Repository not found"
        mock_response.headers = {"X-RateLimit-Limit": "5000", "X-RateLimit-Remaining": "4999", "X-RateLimit-Used": "1"}
        
        http_error = HTTPError("404 Client Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        
        mock_get.return_value = mock_response
        
        result = get_repository_languages(OWNER, "non-existent-repo", TOKEN)
        
        assert result == {}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_get_repository_languages_http_error_403():
    """Test get_repository_languages returns empty dict when access forbidden (403)."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"
        mock_response.text = "Repository access blocked"
        mock_response.headers = {"X-RateLimit-Limit": "5000", "X-RateLimit-Remaining": "4999", "X-RateLimit-Used": "1"}
        
        http_error = HTTPError("403 Client Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        
        mock_get.return_value = mock_response
        
        result = get_repository_languages("private-owner", "private-repo", TOKEN)
        
        assert result == {}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_get_repository_languages_json_decode_error():
    """Test get_repository_languages returns empty dict when JSON decode fails."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "{", 0)
        mock_get.return_value = mock_response
        
        result = get_repository_languages(OWNER, REPO, TOKEN)
        
        assert result == {}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_get_repository_languages_timeout():
    """Test get_repository_languages returns empty dict when request times out."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_get.side_effect = Timeout("Request timed out")
        
        result = get_repository_languages(OWNER, REPO, TOKEN)
        
        assert result == {}
        mock_get.assert_called_once()


def test_get_repository_languages_connection_error():
    """Test get_repository_languages returns empty dict when connection fails."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_get.side_effect = ConnectionError("Connection failed")
        
        result = get_repository_languages(OWNER, REPO, TOKEN)
        
        assert result == {}
        mock_get.assert_called_once()


def test_get_repository_languages_api_call_parameters():
    """Test get_repository_languages makes correct API call with proper parameters."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get, \
         patch("services.github.repositories.get_repository_languages.create_headers") as mock_create_headers:
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"Python": 12345}
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        
        result = get_repository_languages(OWNER, REPO, TOKEN)
        
        # Verify the API call was made with correct parameters
        mock_create_headers.assert_called_once_with(token=TOKEN)
        mock_get.assert_called_once()
        
        # Check the call arguments
        call_args = mock_get.call_args
        assert "url" in call_args.kwargs
        assert f"/repos/{OWNER}/{REPO}/languages" in call_args.kwargs["url"]
        assert "headers" in call_args.kwargs
        assert "timeout" in call_args.kwargs
        
        assert result == {"Python": 12345}


def test_get_repository_languages_with_create_headers_mock():
    """Test get_repository_languages with mocked create_headers function."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get, \
         patch("services.github.repositories.get_repository_languages.create_headers") as mock_create_headers:
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"Python": 12345}
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        
        result = get_repository_languages(OWNER, REPO, TOKEN)
        
        # Verify the API call was made with correct parameters
        mock_create_headers.assert_called_once_with(token=TOKEN)
        mock_get.assert_called_once()
        
        assert result == {"Python": 12345}


def test_get_repository_languages_large_repository():
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
            "YAML": 567
        }
        mock_get.return_value = mock_response
        
        result = get_repository_languages(OWNER, REPO, TOKEN)
        
        assert len(result) == 8
        assert result["Python"] == 1234567
        assert result["JavaScript"] == 987654
        assert isinstance(result, dict)


def test_get_repository_languages_http_error_500():
    """Test get_repository_languages returns empty dict when server error occurs (500)."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Internal server error"
        mock_response.headers = {"X-RateLimit-Limit": "5000", "X-RateLimit-Remaining": "4999", "X-RateLimit-Used": "1"}
        
        http_error = HTTPError("500 Server Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        
        mock_get.return_value = mock_response
        
        result = get_repository_languages(OWNER, REPO, TOKEN)
        
        assert result == {}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_get_repository_languages_attribute_error():
    """Test get_repository_languages returns empty dict when AttributeError occurs."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.side_effect = AttributeError("'NoneType' object has no attribute 'json'")
        mock_get.return_value = mock_response
        
        result = get_repository_languages(OWNER, REPO, TOKEN)
        
        assert result == {}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_get_repository_languages_key_error():
    """Test get_repository_languages returns empty dict when KeyError occurs."""
    with patch("services.github.repositories.get_repository_languages.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.side_effect = KeyError("Missing key in response")
        mock_get.return_value = mock_response
        
        result = get_repository_languages(OWNER, REPO, TOKEN)
        
        assert result == {}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
