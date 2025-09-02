import json
from requests import HTTPError, ConnectionError, Timeout
import pytest
from unittest.mock import patch, MagicMock
from services.circleci.get_job_artifacts import get_circleci_job_artifacts
from config import TIMEOUT


def test_get_circleci_job_artifacts_success():
    """Test successful retrieval of CircleCI job artifacts."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "items": [
            {"path": "coverage/lcov.info", "url": "https://example.com/lcov.info"},
            {"path": "test-results.xml", "url": "https://example.com/test-results.xml"},
        ],
        "next_page_token": None,
    }
    mock_response.raise_for_status.return_value = None

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="123", circle_token="test-token"
        )

        assert len(result) == 2
        assert result[0]["path"] == "coverage/lcov.info"
        assert result[1]["path"] == "test-results.xml"

        mock_get.assert_called_once_with(
            url="https://circleci.com/api/v2/project/gh/owner/repo/123/artifacts",
            headers={"Circle-Token": "test-token"},
            timeout=120,
        )


def test_get_circleci_job_artifacts_empty_response():
    """Test handling of empty response from CircleCI API."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"items": []}
    mock_response.raise_for_status.return_value = None

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="456", circle_token="test-token"
        )

        assert result == []


def test_get_circleci_job_artifacts_http_error():
    """Test handling of HTTP errors when retrieving CircleCI job artifacts."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("HTTP 404")

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="999", circle_token="test-token"
        )

        assert result == []


def test_get_circleci_job_artifacts_404_response():
    """Test handling of 404 response which should return an empty list."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.return_value = None

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="789", circle_token="test-token"
        )

        assert result == []


def test_get_circleci_job_artifacts_missing_items_key():
    """Test handling of response without 'items' key."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "next_page_token": None,
        # No 'items' key
    }
    mock_response.raise_for_status.return_value = None

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="101", circle_token="test-token"
        )


def test_get_circleci_job_artifacts_connection_error():
    """Test handling of connection errors through the handle_exceptions decorator."""
    # Mock the requests.get function to raise a ConnectionError
    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.side_effect = ConnectionError("Failed to establish a connection")

        # Call the function and verify it returns the default empty list
        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="202", circle_token="test-token"
        )

        # Verify the result is an empty list (default_return_value from handle_exceptions)
        assert result == []

        # Verify the get function was called with the expected parameters
        mock_get.assert_called_once()


def test_get_circleci_job_artifacts_json_decode_error():
    """Test handling of JSON decode errors through the handle_exceptions decorator."""
    mock_response = MagicMock()
    # Set up the json method to raise a JSONDecodeError
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "{invalid", 0)
    mock_response.raise_for_status.return_value = None

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        # Call the function and verify it returns the default empty list
        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="303", circle_token="test-token"
        )

        # Verify the result is an empty list (default_return_value from handle_exceptions)
        assert result == []
        assert "gh/owner/repo" in mock_get.call_args[1]["url"]


def test_get_circleci_job_artifacts_unexpected_response_structure():
    """Test handling of unexpected response structure."""
    mock_response = MagicMock()
    # Return a response with an unexpected structure
    mock_response.json.return_value = {
        "data": [  # Using 'data' instead of 'items'
            {
                "file_path": "coverage/lcov.info",
                "download_url": "https://example.com/lcov.info",
            },
        ]
    }
    mock_response.raise_for_status.return_value = None

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="404", circle_token="test-token"
        )


def test_get_circleci_job_artifacts_timeout_parameter():
    """Test that the timeout parameter is correctly passed to the requests.get function."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "items": [
            {"path": "coverage/lcov.info", "url": "https://example.com/lcov.info"},
        ],
    }
    mock_response.raise_for_status.return_value = None

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="505", circle_token="test-token"
        )

        # Verify the timeout parameter is correctly passed
        assert mock_get.call_args[1]["timeout"] == TIMEOUT

def test_get_circleci_job_artifacts_with_node_index():
    """Test successful retrieval with artifacts containing node_index."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "items": [
            {
                "path": "coverage/lcov.info",
                "url": "https://example.com/lcov.info",
                "node_index": 0,
            },
            {
                "path": "test-results.xml",
                "url": "https://example.com/test-results.xml",
                "node_index": 1,
            },
        ],
        "next_page_token": "next-token-123",
    }
    mock_response.raise_for_status.return_value = None

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="123", circle_token="test-token"
        )

        assert len(result) == 2
        assert result[0]["node_index"] == 0
        assert result[1]["node_index"] == 1
        assert result[0]["path"] == "coverage/lcov.info"
        assert result[1]["path"] == "test-results.xml"


def test_get_circleci_job_artifacts_with_next_page_token():
    """Test response with next_page_token (pagination)."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "items": [
            {"path": "artifact1.txt", "url": "https://example.com/artifact1.txt"},
        ],
        "next_page_token": "next-token-456",
    }
    mock_response.raise_for_status.return_value = None

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="789", circle_token="test-token"
        )

        assert len(result) == 1
        assert result[0]["path"] == "artifact1.txt"


def test_get_circleci_job_artifacts_timeout_error():
    """Test handling of timeout errors through the handle_exceptions decorator."""
    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.side_effect = Timeout("Request timed out")

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="606", circle_token="test-token"
        )

        assert result == []
        mock_get.assert_called_once()


def test_get_circleci_job_artifacts_http_error_500():
    """Test handling of HTTP 500 errors."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    http_error = HTTPError("Internal Server Error")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="707", circle_token="test-token"
        )

        assert result == []


def test_get_circleci_job_artifacts_http_error_401():
    """Test handling of HTTP 401 Unauthorized errors."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.reason = "Unauthorized"
    mock_response.text = "Invalid token"
    http_error = HTTPError("Unauthorized")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="808", circle_token="invalid-token"
        )

        assert result == []


def test_get_circleci_job_artifacts_url_construction():
    """Test that the URL is constructed correctly with different project slugs."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"items": []}
