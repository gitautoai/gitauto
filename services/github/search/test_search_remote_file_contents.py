# Standard imports
from unittest.mock import Mock, patch

# Third-party imports
import pytest
import requests

# Local imports
from services.github.search.search_remote_file_contents import (
    search_remote_file_contents,
)


@pytest.fixture
def mock_response_success():
    """Mock successful GitHub API response with multiple files."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "total_count": 2,
        "incomplete_results": False,
        "items": [
            {
                "name": "test_file1.py",
                "path": "src/test_file1.py",
                "sha": "abc123",
                "url": "https://api.github.com/repos/owner/repo/contents/src/test_file1.py",
                "git_url": "https://api.github.com/repos/owner/repo/git/blobs/abc123",
                "html_url": "https://github.com/owner/repo/blob/main/src/test_file1.py",
                "repository": {"id": 123456, "name": "repo", "full_name": "owner/repo"},
            },
            {
                "name": "test_file2.py",
                "path": "tests/test_file2.py",
                "sha": "def456",
                "url": "https://api.github.com/repos/owner/repo/contents/tests/test_file2.py",
                "git_url": "https://api.github.com/repos/owner/repo/git/blobs/def456",
                "html_url": "https://github.com/owner/repo/blob/main/tests/test_file2.py",
                "repository": {"id": 123456, "name": "repo", "full_name": "owner/repo"},
            },
        ],
    }
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def mock_response_empty():
    """Mock GitHub API response with no results."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "total_count": 0,
        "incomplete_results": False,
        "items": [],
    }
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def mock_response_single_file():
    """Mock GitHub API response with single file result."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "total_count": 1,
        "incomplete_results": False,
        "items": [
            {
                "name": "config.py",
                "path": "config.py",
                "sha": "xyz789",
                "url": "https://api.github.com/repos/owner/repo/contents/config.py",
                "git_url": "https://api.github.com/repos/owner/repo/git/blobs/xyz789",
                "html_url": "https://github.com/owner/repo/blob/main/config.py",
                "repository": {"id": 123456, "name": "repo", "full_name": "owner/repo"},
            }
        ],
    }
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def mock_response_many_files():
    """Mock GitHub API response with many files (testing pagination limit)."""
    items = []
    for i in range(10):  # per_page limit is 10
        items.append(
            {
                "name": f"file_{i}.py",
                "path": f"src/file_{i}.py",
                "sha": f"sha{i:03d}",
                "url": f"https://api.github.com/repos/owner/repo/contents/src/file_{i}.py",
                "git_url": f"https://api.github.com/repos/owner/repo/git/blobs/sha{i:03d}",
                "html_url": f"https://github.com/owner/repo/blob/main/src/file_{i}.py",
                "repository": {"id": 123456, "name": "repo", "full_name": "owner/repo"},
            }
        )

    mock_response = Mock()
    mock_response.json.return_value = {
        "total_count": 10,
        "incomplete_results": False,
        "items": items,
    }
    mock_response.raise_for_status.return_value = None
    return mock_response


class TestSearchRemoteFileContents:
    """Test cases for search_remote_file_contents function."""

    @patch("services.github.search.search_remote_file_contents.requests.get")
    @patch("services.github.search.search_remote_file_contents.create_headers")
    def test_successful_search_multiple_files(
        self,
        mock_create_headers,
        mock_get,
        create_test_base_args,
        mock_response_success,
        capsys,
    ):
        """Test successful search returning multiple files."""
        # Arrange
        mock_create_headers.return_value = {
            "Authorization": "Bearer test-token",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "test-app",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        mock_get.return_value = mock_response_success

        base_args = create_test_base_args(
            owner="test-owner", repo="test-repo", is_fork=False, token="test-token"
        )
        query = "def search_function"

        # Act
        result = search_remote_file_contents(query, base_args)

        # Assert
        assert "2 files found for the search query 'def search_function':" in result
        assert "src/test_file1.py" in result
        assert "tests/test_file2.py" in result
        assert result.endswith("\n")

        # Verify API call parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]["url"] == "https://api.github.com/search/code"
        assert (
            call_args[1]["params"]["q"]
            == "def search_function repo:test-owner/test-repo"
        )
        assert call_args[1]["params"]["per_page"] == 10
        assert call_args[1]["params"]["page"] == 1
        assert call_args[1]["timeout"] == 120

        # Verify headers were set correctly
        headers = call_args[1]["headers"]
        assert headers["Accept"] == "application/vnd.github.text-match+json"

        # Verify console output
        captured = capsys.readouterr()
        assert (
            "2 files found for the search query 'def search_function':" in captured.out
        )

    @patch("services.github.search.search_remote_file_contents.requests.get")
    @patch("services.github.search.search_remote_file_contents.create_headers")
    def test_successful_search_fork_repository(
        self,
        mock_create_headers,
        mock_get,
        create_test_base_args,
        mock_response_single_file,
    ):
        """Test successful search in a forked repository."""
        # Arrange
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_response_single_file

        base_args = create_test_base_args(
            owner="fork-owner", repo="fork-repo", is_fork=True, token="test-token"
        )
        query = "import config"

        # Act
        result = search_remote_file_contents(query, base_args)

        # Assert
        assert "1 files found for the search query 'import config':" in result
        assert "config.py" in result

        # Verify fork-specific query parameter
        call_args = mock_get.call_args
        assert (
            call_args[1]["params"]["q"]
            == "import config repo:fork-owner/fork-repo fork:true"
        )

    @patch("services.github.search.search_remote_file_contents.requests.get")
    @patch("services.github.search.search_remote_file_contents.create_headers")
    def test_search_no_results(
        self,
        mock_create_headers,
        mock_get,
        create_test_base_args,
        mock_response_empty,
        capsys,
    ):
        """Test search returning no results."""
        # Arrange
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_response_empty

        base_args = create_test_base_args(
            owner="test-owner", repo="test-repo", is_fork=False, token="test-token"
        )
        query = "nonexistent_function"

        # Act
        result = search_remote_file_contents(query, base_args)

        # Assert
        assert "0 files found for the search query 'nonexistent_function':" in result
        assert result.endswith("\n")

        # Verify console output
        captured = capsys.readouterr()
        assert (
            "0 files found for the search query 'nonexistent_function':" in captured.out
        )

    @patch("services.github.search.search_remote_file_contents.requests.get")
    @patch("services.github.search.search_remote_file_contents.create_headers")
    def test_search_single_file_result(
        self,
        mock_create_headers,
        mock_get,
        create_test_base_args,
        mock_response_single_file,
    ):
        """Test search returning exactly one file."""
        # Arrange
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_response_single_file

        base_args = create_test_base_args(
            owner="test-owner", repo="test-repo", is_fork=False, token="test-token"
        )
        query = "class Config"

        # Act
        result = search_remote_file_contents(query, base_args)

        # Assert
        assert "1 files found for the search query 'class Config':" in result
        assert "config.py" in result
        assert result.count("\n- ") == 1  # Only one file listed

    @patch("services.github.search.search_remote_file_contents.requests.get")
    @patch("services.github.search.search_remote_file_contents.create_headers")
    def test_search_many_files_pagination_limit(
        self,
        mock_create_headers,
        mock_get,
        create_test_base_args,
        mock_response_many_files,
    ):
        """Test search with maximum per_page results (10 files)."""
        # Arrange
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_response_many_files

        base_args = create_test_base_args(
            owner="test-owner", repo="test-repo", is_fork=False, token="test-token"
        )
        query = "def function"

        # Act
        result = search_remote_file_contents(query, base_args)

        # Assert
        assert "10 files found for the search query 'def function':" in result
        for i in range(10):
            assert f"src/file_{i}.py" in result

    @patch("services.github.search.search_remote_file_contents.requests.get")
    @patch("services.github.search.search_remote_file_contents.create_headers")
    def test_http_error_handling(
        self, mock_create_headers, mock_get, create_test_base_args
    ):
        """Test handling of HTTP errors (should return empty string due to decorator)."""
        # Arrange
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        base_args = create_test_base_args(
            owner="test-owner",
            repo="nonexistent-repo",
            is_fork=False,
            token="test-token",
        )
        query = "test query"

        # Act
        result = search_remote_file_contents(query, base_args)

        # Assert - decorator should return empty string on error
        assert result == ""

    @patch("services.github.search.search_remote_file_contents.requests.get")
    @patch("services.github.search.search_remote_file_contents.create_headers")
    def test_json_decode_error_handling(
        self, mock_create_headers, mock_get, create_test_base_args
    ):
        """Test handling of JSON decode errors (should return empty string due to decorator)."""
        # Arrange
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        base_args = create_test_base_args(token="test-token")
        query = "test query"

        # Act
        result = search_remote_file_contents(query, base_args)

        # Assert - decorator should return empty string on error
        assert result == ""

    @patch("services.github.search.search_remote_file_contents.requests.get")
    @patch("services.github.search.search_remote_file_contents.create_headers")
    def test_requests_exception_handling(
        self, mock_create_headers, mock_get, create_test_base_args
    ):
        """Test handling of requests exceptions (should return empty string due to decorator)."""
        # Arrange
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.side_effect = requests.RequestException("Network error")

        base_args = create_test_base_args(token="test-token")
        query = "test query"

        # Act
        result = search_remote_file_contents(query, base_args)

        # Assert - decorator should return empty string on error
        assert result == ""

    @patch("services.github.search.search_remote_file_contents.requests.get")
    @patch("services.github.search.search_remote_file_contents.create_headers")
    def test_missing_items_key_in_response(
        self, mock_create_headers, mock_get, create_test_base_args
    ):
        """Test handling when 'items' key is missing from response."""
        # Arrange
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_response = Mock()
        mock_response.json.return_value = {
            "total_count": 0,
            "incomplete_results": False,
            # Missing 'items' key
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        base_args = create_test_base_args(token="test-token")
        query = "test query"

        # Act
        result = search_remote_file_contents(query, base_args)

        # Assert - should handle missing 'items' gracefully
        assert "0 files found for the search query 'test query':" in result

    @patch("services.github.search.search_remote_file_contents.requests.get")
    @patch("services.github.search.search_remote_file_contents.create_headers")
    def test_malformed_item_structure(
        self, mock_create_headers, mock_get, create_test_base_args
    ):
        """Test handling when item structure is malformed (missing 'path' key)."""
        # Arrange
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_response = Mock()
        mock_response.json.return_value = {
            "total_count": 1,
            "incomplete_results": False,
            "items": [
                {
                    "name": "test_file.py",
                    # Missing 'path' key
                    "sha": "abc123",
                }
            ],
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        base_args = create_test_base_args(token="test-token")
        query = "test query"

        # Act
        result = search_remote_file_contents(query, base_args)

        # Assert - decorator should return empty string on KeyError
        assert result == ""

    @patch("services.github.search.search_remote_file_contents.requests.get")
    @patch("services.github.search.search_remote_file_contents.create_headers")
    def test_create_headers_called_correctly(
        self,
        mock_create_headers,
        mock_get,
        create_test_base_args,
        mock_response_success,
    ):
        """Test that create_headers is called with correct token."""
        # Arrange
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_response_success

        base_args = create_test_base_args(token="specific-test-token")
        query = "test query"

        # Act
        search_remote_file_contents(query, base_args)

        # Assert
        mock_create_headers.assert_called_once_with(token="specific-test-token")

    @patch("services.github.search.search_remote_file_contents.requests.get")
    @patch("services.github.search.search_remote_file_contents.create_headers")
    def test_headers_accept_override(
        self,
        mock_create_headers,
        mock_get,
        create_test_base_args,
        mock_response_success,
    ):
        """Test that Accept header is correctly overridden for text-match."""
        # Arrange
        mock_create_headers.return_value = {
            "Authorization": "Bearer test-token",
            "Accept": "application/vnd.github.v3+json",  # This should be overridden
        }
        mock_get.return_value = mock_response_success

        base_args = create_test_base_args(token="test-token")
        query = "test query"

        # Act
        search_remote_file_contents(query, base_args)

        # Assert
        call_args = mock_get.call_args
        headers = call_args[1]["headers"]
        assert headers["Accept"] == "application/vnd.github.text-match+json"

    @pytest.mark.parametrize(
        "query,expected_in_result",
        [
            ("simple query", "simple query"),
            ("query with spaces", "query with spaces"),
            ("query-with-dashes", "query-with-dashes"),
            ("query_with_underscores", "query_with_underscores"),
            ("query.with.dots", "query.with.dots"),
            ("query/with/slashes", "query/with/slashes"),
            ("", ""),
        ],
    )
    @patch("services.github.search.search_remote_file_contents.requests.get")
    @patch("services.github.search.search_remote_file_contents.create_headers")
    def test_various_query_formats(
        self,
        mock_create_headers,
        mock_get,
        create_test_base_args,
        mock_response_empty,
        query,
        expected_in_result,
    ):
        """Test function with various query formats."""
        # Arrange
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_response_empty

        base_args = create_test_base_args(token="test-token")

        # Act
        result = search_remote_file_contents(query, base_args)

        # Assert
        assert f"0 files found for the search query '{expected_in_result}':" in result

    @pytest.mark.parametrize(
        "is_fork,expected_fork_param",
        [
            (True, "fork:true"),
            (False, ""),
        ],
    )
    @patch("services.github.search.search_remote_file_contents.requests.get")
    @patch("services.github.search.search_remote_file_contents.create_headers")
    def test_fork_parameter_handling(
        self,
        mock_create_headers,
        mock_get,
        create_test_base_args,
        mock_response_empty,
        is_fork,
        expected_fork_param,
    ):
        """Test that fork parameter is handled correctly."""
        # Arrange
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_response_empty

        base_args = create_test_base_args(
            owner="test-owner", repo="test-repo", is_fork=is_fork, token="test-token"
        )
        query = "test query"

        # Act
        search_remote_file_contents(query, base_args)

        # Assert
        call_args = mock_get.call_args
        q_param = call_args[1]["params"]["q"]

        if expected_fork_param:
            assert expected_fork_param in q_param
            assert (
                q_param == f"test query repo:test-owner/test-repo {expected_fork_param}"
            )
        else:
            assert "fork:" not in q_param
            assert q_param == "test query repo:test-owner/test-repo"

    def test_function_has_proper_docstring(self):
        """Test that the function has proper documentation."""
        assert search_remote_file_contents.__doc__ is not None
        docstring = search_remote_file_contents.__doc__
        assert "Only the default branch is considered" in docstring
        assert "Only files smaller than 384 KB are searchable" in docstring
        assert "10 requests per minute" in docstring
        assert "https://docs.github.com/en/rest/search/search" in docstring

    def test_function_has_handle_exceptions_decorator(self):
        """Test that the function is properly decorated with handle_exceptions."""
        # The function should have the decorator applied
        assert hasattr(search_remote_file_contents, "__wrapped__")

        # Test that it returns empty string on error (default_return_value="")
        # This is implicitly tested in the error handling test cases above
