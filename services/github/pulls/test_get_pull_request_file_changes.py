# pylint: disable=redefined-outer-name

# Standard imports
from unittest.mock import patch, Mock

# Third-party imports
import pytest
import requests

# Local imports
from services.github.pulls.get_pull_request_file_changes import get_pull_request_file_changes
from config import TIMEOUT, PER_PAGE


@pytest.fixture
def mock_requests_get():
    """Mock requests.get function."""
    with patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get:
        yield mock_get


@pytest.fixture
def mock_create_headers():
    """Mock create_headers function."""
    with patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_headers:
        mock_headers.return_value = {"Authorization": "Bearer test_token"}
        yield mock_headers


@pytest.fixture
def sample_file_response():
    """Sample file response from GitHub API."""
    return [
        {
            "filename": "src/main.py",
            "status": "modified",
            "patch": "@@ -1,3 +1,4 @@\n def main():\n+    print('hello')\n     pass"
        },
        {
            "filename": "README.md",
            "status": "added",
            "patch": "@@ -0,0 +1,2 @@\n+# Project\n+Description"
        }
    ]


@pytest.fixture
def sample_file_without_patch():
    """Sample file response without patch field."""
    return [
        {
            "filename": "binary_file.png",
            "status": "added"
            # No patch field for binary files
        }
    ]


class TestGetPullRequestFileChanges:
    """Test cases for get_pull_request_file_changes function."""

    def test_successful_single_page_response(self, mock_requests_get, mock_create_headers, sample_file_response):
        """Test successful retrieval of file changes with single page response."""
        # Setup
        test_url = "https://api.github.com/repos/owner/repo/pulls/123/files"
        test_token = "test_token_123"
        
        mock_response = Mock()
        mock_response.json.return_value = sample_file_response
        mock_requests_get.return_value = mock_response

        # Execute
        result = get_pull_request_file_changes(test_url, test_token)

        # Verify
        expected_changes = [
            {
                "filename": "src/main.py",
                "status": "modified",
                "patch": "@@ -1,3 +1,4 @@\n def main():\n+    print('hello')\n     pass"
            },
            {
                "filename": "README.md",
                "status": "added",
                "patch": "@@ -0,0 +1,2 @@\n+# Project\n+Description"
            }
        ]
        assert result == expected_changes
        mock_create_headers.assert_called_once_with(token=test_token)
        mock_requests_get.assert_called_once_with(
            url=test_url,
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": PER_PAGE, "page": 1},
            timeout=TIMEOUT
        )
        mock_response.raise_for_status.assert_called_once()

    def test_successful_multiple_page_response(self, mock_requests_get, mock_create_headers):
        """Test successful retrieval with pagination."""
        # Setup
        test_url = "https://api.github.com/repos/owner/repo/pulls/456/files"
        test_token = "multi_page_token"
        
        first_page_response = [
            {
                "filename": "file1.py",
                "status": "added",
                "patch": "@@ -0,0 +1 @@\n+print('file1')"
            }
        ]
        second_page_response = [
            {
                "filename": "file2.py",
                "status": "modified",
                "patch": "@@ -1 +1,2 @@\n print('old')\n+print('new')"
            }
        ]
        third_page_response = []  # Empty response to end pagination

        def mock_get_side_effect(url, headers, params, timeout):
            mock_response = Mock()
            if params["page"] == 1:
                mock_response.json.return_value = first_page_response
            elif params["page"] == 2:
                mock_response.json.return_value = second_page_response
            else:
                mock_response.json.return_value = third_page_response
            return mock_response

        mock_requests_get.side_effect = mock_get_side_effect

        # Execute
        result = get_pull_request_file_changes(test_url, test_token)

        # Verify
        expected_changes = [
            {
                "filename": "file1.py",
                "status": "added",
                "patch": "@@ -0,0 +1 @@\n+print('file1')"
            },
            {
                "filename": "file2.py",
                "status": "modified",
                "patch": "@@ -1 +1,2 @@\n print('old')\n+print('new')"
            }
        ]
        assert result == expected_changes
        assert mock_requests_get.call_count == 3
        mock_create_headers.assert_called_once_with(token=test_token)

    def test_empty_response_returns_empty_list(self, mock_requests_get, mock_create_headers):
        """Test that empty response returns empty list."""
        # Setup
        test_url = "https://api.github.com/repos/owner/repo/pulls/789/files"
        test_token = "empty_token"
        
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_requests_get.return_value = mock_response

        # Execute
        result = get_pull_request_file_changes(test_url, test_token)

        # Verify
        assert result == []
        mock_create_headers.assert_called_once_with(token=test_token)
        mock_requests_get.assert_called_once()

    def test_files_without_patch_are_skipped(self, mock_requests_get, mock_create_headers, sample_file_without_patch):
        """Test that files without patch field are skipped."""
        # Setup
        test_url = "https://api.github.com/repos/owner/repo/pulls/101/files"
        test_token = "binary_token"
        
        mock_response = Mock()
        mock_response.json.return_value = sample_file_without_patch
        mock_requests_get.return_value = mock_response

        # Execute
        result = get_pull_request_file_changes(test_url, test_token)

        # Verify
        assert result == []  # Binary file without patch should be skipped
        mock_create_headers.assert_called_once_with(token=test_token)

    def test_mixed_files_with_and_without_patch(self, mock_requests_get, mock_create_headers):
        """Test handling of mixed files with and without patch."""
        # Setup
        test_url = "https://api.github.com/repos/owner/repo/pulls/202/files"
        test_token = "mixed_token"
        
        mixed_response = [
            {
                "filename": "src/code.py",
                "status": "modified",
                "patch": "@@ -1 +1,2 @@\n old_code\n+new_code"
            },
            {
                "filename": "image.jpg",
                "status": "added"
                # No patch field
            },
            {
                "filename": "docs.md",
                "status": "removed",
                "patch": "@@ -1,2 +0,0 @@\n-# Documentation\n-Content"
            }
        ]
        
        mock_response = Mock()
        mock_response.json.return_value = mixed_response
        mock_requests_get.return_value = mock_response

        # Execute
        result = get_pull_request_file_changes(test_url, test_token)

        # Verify
        expected_changes = [
            {
                "filename": "src/code.py",
                "status": "modified",
                "patch": "@@ -1 +1,2 @@\n old_code\n+new_code"
            },
            {
                "filename": "docs.md",
                "status": "removed",
                "patch": "@@ -1,2 +0,0 @@\n-# Documentation\n-Content"
            }
        ]
        assert result == expected_changes

    def test_various_file_statuses(self, mock_requests_get, mock_create_headers):
        """Test handling of various file statuses."""
        # Setup
        test_url = "https://api.github.com/repos/owner/repo/pulls/303/files"
        test_token = "status_token"
        
        status_response = [
            {
                "filename": "added_file.py",
                "status": "added",
                "patch": "@@ -0,0 +1 @@\n+new_content"
            },
            {
                "filename": "modified_file.py",
                "status": "modified",
                "patch": "@@ -1 +1 @@\n-old\n+new"
            },
            {
                "filename": "removed_file.py",
                "status": "removed",
                "patch": "@@ -1 +0,0 @@\n-deleted_content"
            },
            {
                "filename": "renamed_file.py",
                "status": "renamed",
                "patch": "@@ -1 +1 @@\n-old_name_content\n+new_name_content"
            }
        ]
        
        mock_response = Mock()
        mock_response.json.return_value = status_response
        mock_requests_get.return_value = mock_response

        # Execute
        result = get_pull_request_file_changes(test_url, test_token)

        # Verify
        assert len(result) == 4
        statuses = [change["status"] for change in result]
        assert "added" in statuses
        assert "modified" in statuses
        assert "removed" in statuses
        assert "renamed" in statuses

    def test_large_patch_content(self, mock_requests_get, mock_create_headers):
        """Test handling of files with large patch content."""
        # Setup
        test_url = "https://api.github.com/repos/owner/repo/pulls/404/files"
        test_token = "large_patch_token"
        
        large_patch = "@@ -1,100 +1,200 @@\n" + "\n".join([f"+line_{i}" for i in range(200)])
        large_response = [
            {
                "filename": "large_file.py",
                "status": "modified",
                "patch": large_patch
            }
        ]
        
        mock_response = Mock()
        mock_response.json.return_value = large_response
        mock_requests_get.return_value = mock_response

        # Execute
        result = get_pull_request_file_changes(test_url, test_token)

        # Verify
        assert len(result) == 1
        assert result[0]["filename"] == "large_file.py"
        assert result[0]["patch"] == large_patch

    def test_special_characters_in_filenames(self, mock_requests_get, mock_create_headers):
        """Test handling of filenames with special characters."""
        # Setup
        test_url = "https://api.github.com/repos/owner/repo/pulls/505/files"
        test_token = "special_chars_token"
        
        special_response = [
            {
                "filename": "file with spaces.py",
                "status": "added",
                "patch": "@@ -0,0 +1 @@\n+content"
            },
            {
                "filename": "file-with-dashes.py",
                "status": "modified",
                "patch": "@@ -1 +1 @@\n-old\n+new"
            },
            {
                "filename": "file_with_underscores.py",
                "status": "removed",
                "patch": "@@ -1 +0,0 @@\n-content"
            },
            {
                "filename": "file.with.dots.py",
                "status": "modified",
                "patch": "@@ -1 +1 @@\n-old\n+new"
            },
            {
                "filename": "файл-с-unicode.py",
                "status": "added",
                "patch": "@@ -0,0 +1 @@\n+unicode_content"
            }
        ]
        
        mock_response = Mock()
        mock_response.json.return_value = special_response
        mock_requests_get.return_value = mock_response

        # Execute
        result = get_pull_request_file_changes(test_url, test_token)

        # Verify
        assert len(result) == 5
        filenames = [change["filename"] for change in result]
        assert "file with spaces.py" in filenames
        assert "file-with-dashes.py" in filenames
        assert "file_with_underscores.py" in filenames
        assert "file.with.dots.py" in filenames
        assert "файл-с-unicode.py" in filenames

    def test_http_error_404_returns_none(self, mock_requests_get, mock_create_headers):
        """Test that 404 HTTP error returns None due to handle_exceptions decorator."""
        # Setup
        test_url = "https://api.github.com/repos/owner/repo/pulls/999/files"
        test_token = "not_found_token"
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Not Found"
        
        http_error = requests.exceptions.HTTPError("404 Client Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        
        mock_requests_get.return_value = mock_response

        # Execute
        result = get_pull_request_file_changes(test_url, test_token)

        # Verify
        assert result is None  # Default return value from handle_exceptions decorator
        mock_create_headers.assert_called_once_with(token=test_token)

    def test_http_error_403_returns_none(self, mock_requests_get, mock_create_headers):
        """Test that 403 HTTP error returns None due to handle_exceptions decorator."""
        # Setup
        test_url = "https://api.github.com/repos/private/repo/pulls/123/files"
        test_token = "forbidden_token"
        
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"
        mock_response.text = "Forbidden"
        
        http_error = requests.exceptions.HTTPError("403 Client Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        
        mock_requests_get.return_value = mock_response

        # Execute
        result = get_pull_request_file_changes(test_url, test_token)

        # Verify
        assert result is None  # Default return value from handle_exceptions decorator

    def test_connection_error_returns_none(self, mock_requests_get, mock_create_headers):
        """Test that connection error returns None due to handle_exceptions decorator."""
        # Setup
        test_url = "https://api.github.com/repos/owner/repo/pulls/123/files"
        test_token = "connection_error_token"
        
        mock_requests_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        # Execute
        result = get_pull_request_file_changes(test_url, test_token)

        # Verify
        assert result is None  # Default return value from handle_exceptions decorator
        mock_create_headers.assert_called_once_with(token=test_token)

    def test_timeout_error_returns_none(self, mock_requests_get, mock_create_headers):
        """Test that timeout error returns None due to handle_exceptions decorator."""
        # Setup
        test_url = "https://api.github.com/repos/owner/repo/pulls/123/files"
        test_token = "timeout_token"
        
        mock_requests_get.side_effect = requests.exceptions.Timeout("Request timed out")

        # Execute
        result = get_pull_request_file_changes(test_url, test_token)

        # Verify
        assert result is None  # Default return value from handle_exceptions decorator

    def test_json_decode_error_returns_none(self, mock_requests_get, mock_create_headers):
        """Test that JSON decode error returns None due to handle_exceptions decorator."""
        # Setup
        test_url = "https://api.github.com/repos/owner/repo/pulls/123/files"
        test_token = "json_error_token"
        
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_requests_get.return_value = mock_response

        # Execute
        result = get_pull_request_file_changes(test_url, test_token)

        # Verify
        assert result is None  # Default return value from handle_exceptions decorator

    def test_uses_correct_timeout_and_per_page(self, mock_requests_get, mock_create_headers):
        """Test that function uses correct TIMEOUT and PER_PAGE values from config."""
        # Setup
        test_url = "https://api.github.com/repos/owner/repo/pulls/123/files"
        test_token = "config_test_token"
        
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_requests_get.return_value = mock_response

        # Execute
        get_pull_request_file_changes(test_url, test_token)

        # Verify
        mock_requests_get.assert_called_once_with(
            url=test_url,
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": PER_PAGE, "page": 1},
            timeout=TIMEOUT
        )

    def test_pagination_parameters_increment_correctly(self, mock_requests_get, mock_create_headers):
        """Test that pagination parameters increment correctly."""
        # Setup
        test_url = "https://api.github.com/repos/owner/repo/pulls/123/files"
        test_token = "pagination_token"
        
        def mock_get_side_effect(url, headers, params, timeout):
            mock_response = Mock()
            if params["page"] <= 2:
                mock_response.json.return_value = [
                    {
                        "filename": f"file_page_{params['page']}.py",
                        "status": "added",
                        "patch": f"@@ -0,0 +1 @@\n+page_{params['page']}_content"
                    }
                ]
            else:
                mock_response.json.return_value = []
            return mock_response

        mock_requests_get.side_effect = mock_get_side_effect

        # Execute
        result = get_pull_request_file_changes(test_url, test_token)

        # Verify
        assert len(result) == 2
        assert mock_requests_get.call_count == 3  # Pages 1, 2, and 3 (empty)
        
        # Check that page parameters were incremented correctly
        call_args_list = mock_requests_get.call_args_list
        assert call_args_list[0].kwargs["params"]["page"] == 1
        assert call_args_list[1].kwargs["params"]["page"] == 2
        assert call_args_list[2].kwargs["params"]["page"] == 3

    def test_create_headers_called_with_correct_token(self, mock_requests_get, mock_create_headers):
        """Test that create_headers is called with the correct token."""
        # Setup
        test_url = "https://api.github.com/repos/owner/repo/pulls/123/files"
        test_token = "specific_test_token_123"
        
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_requests_get.return_value = mock_response

        # Execute
        get_pull_request_file_changes(test_url, test_token)

        # Verify
        mock_create_headers.assert_called_once_with(token=test_token)

    def test_various_url_formats(self, mock_requests_get, mock_create_headers):
        """Test that function works with various URL formats."""
        # Setup
        test_urls = [
            "https://api.github.com/repos/owner/repo/pulls/123/files",
            "https://api.github.com/repos/org-name/repo-name/pulls/456/files",
            "https://api.github.com/repos/user_name/repo_name/pulls/789/files",
            "https://api.github.com/repos/owner/repo.name/pulls/101/files",
        ]
        test_token = "url_format_token"
        
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_requests_get.return_value = mock_response

        for test_url in test_urls:
            # Execute
            result = get_pull_request_file_changes(test_url, test_token)

            # Verify
            assert result == []

        # Verify all URLs were called
        assert mock_requests_get.call_count == len(test_urls)

    def test_empty_patch_content(self, mock_requests_get, mock_create_headers):
        """Test handling of files with empty patch content."""
        # Setup
        test_url = "https://api.github.com/repos/owner/repo/pulls/123/files"
        test_token = "empty_patch_token"
        
        empty_patch_response = [
            {
                "filename": "empty_patch.py",
                "status": "modified",
                "patch": ""
            }
        ]
        
        mock_response = Mock()
        mock_response.json.return_value = empty_patch_response
        mock_requests_get.return_value = mock_response

        # Execute
        result = get_pull_request_file_changes(test_url, test_token)

        # Verify
        assert len(result) == 1
        assert result[0]["filename"] == "empty_patch.py"
        assert result[0]["patch"] == ""

    def test_malformed_file_objects_are_handled(self, mock_requests_get, mock_create_headers):
        """Test that malformed file objects are handled gracefully."""
        # Setup
        test_url = "https://api.github.com/repos/owner/repo/pulls/123/files"
        test_token = "malformed_token"
        
        malformed_response = [
            {
                "filename": "good_file.py",
                "status": "added",
                "patch": "@@ -0,0 +1 @@\n+content"
            },
            {
                # Missing filename
                "status": "modified",
                "patch": "@@ -1 +1 @@\n-old\n+new"
            },
            {
                "filename": "missing_status.py",
                # Missing status
                "patch": "@@ -1 +1 @@\n-old\n+new"
            },
            {
                "filename": "complete_file.py",
                "status": "removed",
                "patch": "@@ -1 +0,0 @@\n-content"
            }
        ]
        
        mock_response = Mock()
        mock_response.json.return_value = malformed_response
        mock_requests_get.return_value = mock_response

        # Execute
        result = get_pull_request_file_changes(test_url, test_token)

        # Verify - only well-formed files should be included
        assert len(result) == 2
        filenames = [change["filename"] for change in result]
        assert "good_file.py" in filenames
        assert "complete_file.py" in filenames

    @pytest.mark.parametrize(
        "url,token",
        [
            ("https://api.github.com/repos/owner/repo/pulls/1/files", "token1"),
            ("https://api.github.com/repos/org/project/pulls/999/files", "token999"),
            ("https://api.github.com/repos/user/repo-name/pulls/42/files", "secret_token"),
        ],
    )
    def test_parametrized_url_token_combinations(self, mock_requests_get, mock_create_headers, url, token):
        """Test various URL and token combinations."""
        # Setup
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_requests_get.return_value = mock_response

        # Execute
        result = get_pull_request_file_changes(url, token)

        # Verify
        assert result == []
        mock_create_headers.assert_called_with(token=token)
        mock_requests_get.assert_called_with(
            url=url,
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": PER_PAGE, "page": 1},
            timeout=TIMEOUT
        )

    def test_handle_exceptions_decorator_configuration(self):
        """Test that the function has the correct handle_exceptions decorator configuration."""
        # This test verifies the decorator is applied with correct parameters
        # by checking the function's behavior when an exception occurs
        with patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get:
            mock_get.side_effect = Exception("Test exception")
            
            result = get_pull_request_file_changes("test_url", "test_token")
            
            # Should return None (default_return_value) and not raise exception (raise_on_error=False)
            assert result is None
