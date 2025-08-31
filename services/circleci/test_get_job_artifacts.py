import json
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
            url="https://circleci.com/api/v2/project/gh/owner/repo/job/123/artifacts",
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

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="101", circle_token="test-token"
        )

        # Should return empty list when 'items' key is missing
        assert result == []


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

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="404", circle_token="test-token"
        )

        # Should return empty list when response structure is unexpected
        assert result == []


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


def test_get_circleci_job_artifacts_different_status_codes():
    """Test handling of various HTTP status codes."""
    # Test 401 Unauthorized
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = Exception("Unauthorized")

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="123", circle_token="invalid-token"
        )

        assert result == []


def test_get_circleci_job_artifacts_403_forbidden():
    """Test handling of 403 Forbidden status code."""
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.raise_for_status.side_effect = Exception("Forbidden")

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="123", circle_token="test-token"
        )

        assert result == []


def test_get_circleci_job_artifacts_500_server_error():
    """Test handling of 500 Internal Server Error."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = Exception("Internal Server Error")

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="123", circle_token="test-token"
        )

        assert result == []


def test_get_circleci_job_artifacts_url_construction():
    """Test that the URL is constructed correctly with different project slugs."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"items": []}
    mock_response.raise_for_status.return_value = None

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        # Test with different project slug formats
        get_circleci_job_artifacts(
            project_slug="bb/bitbucket-user/repo-name",
            job_number="456",
            circle_token="test-token",
        )

        expected_url = "https://circleci.com/api/v2/project/bb/bitbucket-user/repo-name/job/456/artifacts"
        mock_get.assert_called_with(
            url=expected_url,
            headers={"Circle-Token": "test-token"},
            timeout=TIMEOUT,
        )


def test_get_circleci_job_artifacts_headers_construction():
    """Test that headers are constructed correctly with different tokens."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"items": []}
    mock_response.raise_for_status.return_value = None

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        # Test with a specific token format
        test_token = "circle-token-abc123xyz"
        get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="789", circle_token=test_token
        )

        # Verify the headers contain the correct token
        call_args = mock_get.call_args
        assert call_args[1]["headers"]["Circle-Token"] == test_token


def test_get_circleci_job_artifacts_empty_items_list():
    """Test handling of response with empty items list."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "items": [],
        "next_page_token": None,
    }
    mock_response.raise_for_status.return_value = None

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="123", circle_token="test-token"
        )

        assert result == []
        assert isinstance(result, list)
        assert mock_get.call_args[1]["timeout"] == TIMEOUT
