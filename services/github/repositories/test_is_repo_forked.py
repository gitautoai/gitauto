from unittest.mock import Mock, patch
import pytest
import requests
from services.github.repositories.is_repo_forked import is_repo_forked
from tests.constants import OWNER, REPO, FORKED_REPO, TOKEN


def test_is_repo_forked_returns_true_for_forked_repo():
    with patch("services.github.repositories.is_repo_forked.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"fork": True}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = is_repo_forked(OWNER, FORKED_REPO, TOKEN)
        
        assert result is True
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()


def test_is_repo_forked_returns_false_for_non_forked_repo():
    with patch("services.github.repositories.is_repo_forked.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"fork": False}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = is_repo_forked(OWNER, REPO, TOKEN)
        
        assert result is False
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()


def test_is_repo_forked_with_correct_url_and_headers():
    with patch("services.github.repositories.is_repo_forked.get") as mock_get, \
         patch("services.github.repositories.is_repo_forked.create_headers") as mock_create_headers:
        
        mock_headers = {"Authorization": f"Bearer {TOKEN}"}
        mock_create_headers.return_value = mock_headers
        
        mock_response = Mock()
        mock_response.json.return_value = {"fork": True}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        is_repo_forked(OWNER, REPO, TOKEN)
        
        mock_create_headers.assert_called_once_with(token=TOKEN)
        mock_get.assert_called_once_with(
            url=f"https://api.github.com/repos/{OWNER}/{REPO}",
            headers=mock_headers,
            timeout=120
        )


def test_is_repo_forked_handles_http_error():
    with patch("services.github.repositories.is_repo_forked.get") as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        result = is_repo_forked(OWNER, REPO, TOKEN)
        
        assert result is False
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_is_repo_forked_handles_json_decode_error():
    with patch("services.github.repositories.is_repo_forked.get") as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = requests.exceptions.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response
        
        result = is_repo_forked(OWNER, REPO, TOKEN)
        
        assert result is False
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()


def test_is_repo_forked_handles_key_error():
    with patch("services.github.repositories.is_repo_forked.get") as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"name": "test-repo"}
        mock_get.return_value = mock_response
        
        result = is_repo_forked(OWNER, REPO, TOKEN)
        
        assert result is False
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()


def test_is_repo_forked_handles_connection_error():
    with patch("services.github.repositories.is_repo_forked.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = is_repo_forked(OWNER, REPO, TOKEN)
        
        assert result is False
        mock_get.assert_called_once()


def test_is_repo_forked_handles_timeout_error():
    with patch("services.github.repositories.is_repo_forked.get") as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        result = is_repo_forked(OWNER, REPO, TOKEN)
        
        assert result is False
        mock_get.assert_called_once()


def test_is_repo_forked_with_empty_strings():
    with patch("services.github.repositories.is_repo_forked.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"fork": False}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = is_repo_forked("", "", "")
        
        assert result is False
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos//",
            headers=mock_get.call_args[1]["headers"],
            timeout=120
        )
