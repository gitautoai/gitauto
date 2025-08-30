from unittest.mock import Mock, patch
import pytest
import requests
from services.github.pulls.get_pull_request_files import get_pull_request_files


@pytest.fixture
def mock_requests():
    with patch("services.github.pulls.get_pull_request_files.requests") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    with patch("services.github.pulls.get_pull_request_files.create_headers") as mock:
        mock.return_value = {"Authorization": "token test_token"}
        yield mock


def test_get_pull_request_files_success(mock_requests, mock_create_headers):
    """Test successful retrieval of pull request files"""
    mock_response_data = [
        {"filename": "file1.py", "status": "modified"},
        {"filename": "file2.js", "status": "added"},
        {"filename": "file3.txt", "status": "removed"},
    ]
    # Setup mock response
    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    # Mock for empty second page (pagination)
    empty_response = Mock()
    empty_response.json.return_value = []

    mock_requests.get.side_effect = [mock_response, empty_response]

    # Call function
    result = get_pull_request_files(
        "https://api.github.com/repos/test/test/pulls/1/files", "token123"
    )

    # Verify result
    expected = [
        {"filename": "file1.py", "status": "modified"},
        {"filename": "file2.js", "status": "added"},
        {"filename": "file3.txt", "status": "removed"},
    ]

    assert result == expected
    mock_create_headers.assert_called_once_with(token="token123")
    assert mock_requests.get.call_count == 2


def test_get_pull_request_files_pagination():
    """Test pagination handling"""
    page1_data = [{"filename": "file1.py", "status": "modified"}]
    page2_data = [{"filename": "file2.js", "status": "added"}]

    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response1 = Mock()
        mock_response1.json.return_value = page1_data
        mock_response1.raise_for_status.return_value = None

        mock_response2 = Mock()
        mock_response2.json.return_value = page2_data
        mock_response2.raise_for_status.return_value = None

        mock_response3 = Mock()
        mock_response3.json.return_value = []  # Empty page ends pagination
        mock_response3.raise_for_status.return_value = None

        mock_get.side_effect = [mock_response1, mock_response2, mock_response3]

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        expected = [
            {"filename": "file1.py", "status": "modified"},
            {"filename": "file2.js", "status": "added"},
        ]

        assert result == expected
        assert mock_get.call_count == 3


def test_get_pull_request_files_missing_fields():
    """Test handling of files with missing filename or status fields"""
    mock_response_data = [
        {"filename": "file1.py", "status": "modified"},
        {"filename": "file2.js"},  # Missing status
        {"status": "added"},  # Missing filename
        {"filename": "file3.txt", "status": "removed"},
    ]

    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        expected = [
            {"filename": "file1.py", "status": "modified"},
            {"filename": "file3.txt", "status": "removed"},
        ]

        assert result == expected


def test_get_pull_request_files_http_error():
    """Test handling of HTTP errors"""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_get.return_value = mock_response

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        assert result == []


def test_get_pull_request_files_empty_response():
    """Test handling of empty response"""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        assert result == []
