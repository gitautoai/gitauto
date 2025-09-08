# Standard imports
from unittest.mock import Mock, patch

# Third party imports
import pytest
import requests

# Local imports
from services.github.search.search_remote_file_contents import (
    search_remote_file_contents,
)

# Local imports (Config)
from config import (
    GITHUB_API_URL,
    TIMEOUT,
)

@pytest.fixture
def mock_requests():
    """Mock requests module for testing."""
    with patch("services.github.search.search_remote_file_contents.requests") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    """Mock create_headers function for testing."""
    with patch(
        "services.github.search.search_remote_file_contents.create_headers"
    ) as mock:
        mock.return_value = {"Authorization": "Bearer test_token"}
        yield mock


@pytest.fixture
def mock_print():
    """Mock print function for testing."""
    with patch("builtins.print") as mock:
        yield mock


def test_search_remote_file_contents_success_regular_repo(
    mock_requests, mock_create_headers, mock_print, create_test_base_args
):
    """Test successful search in a regular (non-fork) repository."""
    # Setup
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        is_fork=False,
        token="test-token"
    )
    
    mock_response_data = {
        "items": [
            {"path": "src/main.py"},
            {"path": "tests/test_main.py"},
            {"path": "README.md"}
        ]
    }
    
    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response
    
    # Execute
    result = search_remote_file_contents("function_name", base_args)
    
    # Verify
    expected_msg = (
        "3 files found for the search query 'function_name':\n"
        "- src/main.py\n"
        "- tests/test_main.py\n"
        "- README.md\n"
    )
    
    assert result == expected_msg
    mock_print.assert_called_once_with(expected_msg)
    mock_create_headers.assert_called_once_with(token="test-token")
    
    # Verify request parameters
    mock_requests.get.assert_called_once_with(
        url=f"{GITHUB_API_URL}/search/code",
        headers={
            "Authorization": "Bearer test_token",
            "Accept": "application/vnd.github.text-match+json"
        },
        params={
            "q": "function_name repo:test-owner/test-repo",
            "per_page": 10,
            "page": 1
        },
        timeout=TIMEOUT
    )


def test_search_remote_file_contents_success_fork_repo(
    mock_requests, mock_create_headers, mock_print, create_test_base_args
):
    """Test successful search in a fork repository."""
    # Setup
    base_args = create_test_base_args(
        owner="fork-owner",
        repo="fork-repo",
        is_fork=True,
        token="fork-token"
    )
    
    mock_response_data = {
        "items": [
            {"path": "lib/utils.js"},
            {"path": "config/settings.json"}
        ]
    }
    
    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response
    
    # Execute
    result = search_remote_file_contents("search_term", base_args)
    
    # Verify
    expected_msg = (
        "2 files found for the search query 'search_term':\n"
        "- lib/utils.js\n"
        "- config/settings.json\n"
    )
    
    assert result == expected_msg
    mock_print.assert_called_once_with(expected_msg)
    
    # Verify fork-specific query parameter
    mock_requests.get.assert_called_once_with(
        url=f"{GITHUB_API_URL}/search/code",
        headers={
            "Authorization": "Bearer test_token",
            "Accept": "application/vnd.github.text-match+json"
        },
        params={
            "q": "search_term repo:fork-owner/fork-repo fork:true",
            "per_page": 10,
            "page": 1
        },
        timeout=TIMEOUT
    )


def test_search_remote_file_contents_empty_results(
    mock_requests, mock_create_headers, mock_print, create_test_base_args
):
    """Test search with no results found."""
    # Setup
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        is_fork=False,
        token="test-token"
    )
    
    mock_response_data = {"items": []}
    
    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response
    
    # Execute
    result = search_remote_file_contents("nonexistent_function", base_args)
    
    # Verify
    expected_msg = "0 files found for the search query 'nonexistent_function':\n- \n"
    
    assert result == expected_msg
    mock_print.assert_called_once_with(expected_msg)


def test_search_remote_file_contents_missing_items_key(
    mock_requests, mock_create_headers, mock_print, create_test_base_args
):
    """Test search when response doesn't contain 'items' key."""
    # Setup
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        is_fork=False,
        token="test-token"
    )
    
    mock_response_data = {"total_count": 0}  # No 'items' key
    
    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response
    
    # Execute
    result = search_remote_file_contents("query", base_args)
    
    # Verify
    expected_msg = "0 files found for the search query 'query':\n- \n"
    
    assert result == expected_msg
    mock_print.assert_called_once_with(expected_msg)


def test_search_remote_file_contents_single_file(
    mock_requests, mock_create_headers, mock_print, create_test_base_args
):
    """Test search returning a single file."""
    # Setup
    base_args = create_test_base_args(
        owner="single-owner",
        repo="single-repo",
        is_fork=False,
        token="single-token"
    )
    
    mock_response_data = {
        "items": [
            {"path": "unique_file.py"}
        ]
    }
    
    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response
    
    # Execute
    result = search_remote_file_contents("unique_function", base_args)
    
    # Verify
    expected_msg = (
        "1 files found for the search query 'unique_function':\n"
        "- unique_file.py\n"
    )
    
    assert result == expected_msg
    mock_print.assert_called_once_with(expected_msg)


def test_search_remote_file_contents_complex_query(
    mock_requests, mock_create_headers, mock_print, create_test_base_args
):
    """Test search with complex query containing special characters."""
    # Setup
    base_args = create_test_base_args(
        owner="complex-owner",
        repo="complex-repo",
        is_fork=False,
        token="complex-token"
    )
    
    mock_response_data = {
        "items": [
            {"path": "src/api/endpoints.py"},
            {"path": "tests/api/test_endpoints.py"}
        ]
    }
    
    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response
    
    # Execute
    complex_query = "def get_user() AND class UserAPI"
    result = search_remote_file_contents(complex_query, base_args)
    
    # Verify
    expected_msg = (
        f"2 files found for the search query '{complex_query}':\n"
        "- src/api/endpoints.py\n"
        "- tests/api/test_endpoints.py\n"
    )
    
    assert result == expected_msg
    mock_print.assert_called_once_with(expected_msg)
    
    # Verify query parameter
    expected_query = f"{complex_query} repo:complex-owner/complex-repo"
    call_args = mock_requests.get.call_args
    assert call_args[1]["params"]["q"] == expected_query


def test_search_remote_file_contents_http_error_404(
    mock_requests, mock_create_headers, create_test_base_args
):
    """Test handling of 404 HTTP error."""
    # Setup
    base_args = create_test_base_args(
        owner="nonexistent-owner",
        repo="nonexistent-repo",
        is_fork=False,
        token="test-token"
    )
    
    mock_response = Mock()
    mock_response.status_code = 404
    http_error = requests.exceptions.HTTPError("404 Not Found")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    mock_requests.get.return_value = mock_response
    
    # Execute - should return default value due to handle_exceptions decorator
    result = search_remote_file_contents("query", base_args)
    
    # Verify
    assert result == ""  # Default return value from decorator


def test_search_remote_file_contents_http_error_403(
    mock_requests, mock_create_headers, create_test_base_args
):
    """Test handling of 403 HTTP error (rate limit or permission)."""
    # Setup
    base_args = create_test_base_args(
        owner="restricted-owner",
        repo="restricted-repo",
        is_fork=False,
        token="invalid-token"
    )
    
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.headers = {
        "X-RateLimit-Limit": "10",
        "X-RateLimit-Remaining": "5",
        "X-RateLimit-Used": "5"
    }
    http_error = requests.exceptions.HTTPError("403 Forbidden")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    mock_requests.get.return_value = mock_response
    
    # Execute - should return default value due to handle_exceptions decorator
    result = search_remote_file_contents("query", base_args)
    
    # Verify
    assert result == ""  # Default return value from decorator


def test_search_remote_file_contents_network_error(
    mock_requests, mock_create_headers, create_test_base_args
):
    """Test handling of network connection error."""
    # Setup
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        is_fork=False,
        token="test-token"
    )
    
    mock_requests.get.side_effect = requests.exceptions.ConnectionError("Network error")
    
    # Execute - should return default value due to handle_exceptions decorator
    result = search_remote_file_contents("query", base_args)
    
    # Verify
    assert result == ""  # Default return value from decorator


def test_search_remote_file_contents_timeout_error(
    mock_requests, mock_create_headers, create_test_base_args
):
    """Test handling of timeout error."""
    # Setup
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        is_fork=False,
        token="test-token"
    )
    
    mock_requests.get.side_effect = requests.exceptions.Timeout("Request timeout")
    
    # Execute - should return default value due to handle_exceptions decorator
    result = search_remote_file_contents("query", base_args)
    
    # Verify
    assert result == ""  # Default return value from decorator


def test_search_remote_file_contents_json_decode_error(
    mock_requests, mock_create_headers, create_test_base_args
):
    """Test handling of JSON decode error."""
    # Setup
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        is_fork=False,
        token="test-token"
    )
    
    mock_response = Mock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response
    
    # Execute - should return default value due to handle_exceptions decorator
    result = search_remote_file_contents("query", base_args)
    
    # Verify
    assert result == ""  # Default return value from decorator


def test_search_remote_file_contents_headers_configuration(
    mock_requests, mock_create_headers, create_test_base_args
):
    """Test that headers are correctly configured."""
    # Setup
    base_args = create_test_base_args(
        owner="test-owner",
        repo="test-repo",
        is_fork=False,
        token="custom-token"
    )
    
    mock_response_data = {"items": []}
    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response
    
    # Execute
    search_remote_file_contents("query", base_args)
    
    # Verify headers creation and modification
    mock_create_headers.assert_called_once_with(token="custom-token")
    
    # Verify the Accept header was added for text-match
    call_args = mock_requests.get.call_args
    headers = call_args[1]["headers"]
    assert headers["Accept"] == "application/vnd.github.text-match+json"
