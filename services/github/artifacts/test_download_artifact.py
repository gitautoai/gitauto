import io
import zipfile
from unittest.mock import patch, MagicMock
import pytest
import requests

from services.github.artifacts.download_artifact import download_artifact


@pytest.fixture
def mock_response():
    """Fixture to provide a mocked response object."""
    response = MagicMock()
    response.content = b"mock_zip_content"
    return response


@pytest.fixture
def mock_zip_with_lcov():
    """Fixture to create a mock zip file containing lcov.info."""
    # Create a real zip file in memory with lcov.info
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr("lcov.info", "TN:\nSF:test.py\nLF:10\nLH:8\nend_of_record")
        zip_file.writestr("other_file.txt", "some other content")
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


@pytest.fixture
def mock_zip_without_lcov():
    """Fixture to create a mock zip file without lcov.info."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr("other_file.txt", "some content")
        zip_file.writestr("readme.md", "readme content")
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


@pytest.fixture
def mock_zip_empty():
    """Fixture to create an empty mock zip file."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w"):
        pass  # Empty zip
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


@pytest.fixture
def mock_headers():
    """Fixture to provide mock headers."""
    return {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": "Bearer test_token",
        "User-Agent": "GitAuto",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def test_download_artifact_success_with_lcov(mock_zip_with_lcov, mock_headers):
    """Test successful artifact download with lcov.info present."""
    with patch("services.github.artifacts.download_artifact.get") as mock_get, patch(
        "services.github.artifacts.download_artifact.create_headers"
    ) as mock_create_headers:

        # Setup mocks
        mock_response = MagicMock()
        mock_response.content = mock_zip_with_lcov
        mock_get.return_value = mock_response
        mock_create_headers.return_value = mock_headers

        # Call function
        result = download_artifact("owner", "repo", 123, "test_token")

        # Assertions
        assert result == "TN:\nSF:test.py\nLF:10\nLH:8\nend_of_record"
        mock_create_headers.assert_called_once_with(token="test_token")
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/owner/repo/actions/artifacts/123/zip",
            headers=mock_headers,
            timeout=120,
        )


def test_download_artifact_success_without_lcov(mock_zip_without_lcov, mock_headers):
    """Test artifact download when lcov.info is not present."""
    with patch("services.github.artifacts.download_artifact.get") as mock_get, patch(
        "services.github.artifacts.download_artifact.create_headers"
    ) as mock_create_headers:

        # Setup mocks
        mock_response = MagicMock()
        mock_response.content = mock_zip_without_lcov
        mock_get.return_value = mock_response
        mock_create_headers.return_value = mock_headers

        # Call function
        result = download_artifact("owner", "repo", 456, "test_token")

        # Assertions
        assert result is None
        mock_create_headers.assert_called_once_with(token="test_token")
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/owner/repo/actions/artifacts/456/zip",
            headers=mock_headers,
            timeout=120,
        )


def test_download_artifact_empty_zip(mock_zip_empty, mock_headers):
    """Test artifact download with empty zip file."""
    with patch("services.github.artifacts.download_artifact.get") as mock_get, patch(
        "services.github.artifacts.download_artifact.create_headers"
    ) as mock_create_headers:

        # Setup mocks
        mock_response = MagicMock()
        mock_response.content = mock_zip_empty
        mock_get.return_value = mock_response
        mock_create_headers.return_value = mock_headers

        # Call function
        result = download_artifact("owner", "repo", 789, "test_token")

        # Assertions
        assert result is None
        mock_create_headers.assert_called_once_with(token="test_token")


def test_download_artifact_with_different_parameters():
    """Test download_artifact with various parameter combinations."""
    test_cases = [
        ("test-owner", "test-repo", 1, "token1"),
        ("org", "my-repo", 999, "secret_token"),
        ("user123", "project_name", 42, "gh_token_xyz"),
    ]

    for owner, repo, artifact_id, token in test_cases:
        with patch(
            "services.github.artifacts.download_artifact.get"
        ) as mock_get, patch(
            "services.github.artifacts.download_artifact.create_headers"
        ) as mock_create_headers:

            # Setup mocks
            mock_response = MagicMock()
            mock_response.content = b"empty_zip"
            mock_get.return_value = mock_response
            mock_create_headers.return_value = {}

            # Mock zipfile to avoid actual zip processing
            with patch(
                "services.github.artifacts.download_artifact.zipfile.ZipFile"
            ) as mock_zipfile:
                mock_zip_instance = MagicMock()
                mock_zip_instance.namelist.return_value = []
                mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

                # Call function
                result = download_artifact(owner, repo, artifact_id, token)

                # Assertions
                expected_url = f"https://api.github.com/repos/{owner}/{repo}/actions/artifacts/{artifact_id}/zip"
                mock_get.assert_called_once_with(
                    url=expected_url, headers={}, timeout=120
                )
                mock_create_headers.assert_called_once_with(token=token)
                assert result is None


def test_download_artifact_lcov_with_unicode_content():
    """Test download_artifact with Unicode content in lcov.info."""
    # Create zip with Unicode content
    unicode_content = (
        "TN:\nSF:test.py\n# Comment with émojis 🚀\nLF:5\nLH:3\nend_of_record"
    )
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr("lcov.info", unicode_content.encode("utf-8"))
    zip_buffer.seek(0)
    zip_content = zip_buffer.getvalue()

    with patch("services.github.artifacts.download_artifact.get") as mock_get, patch(
        "services.github.artifacts.download_artifact.create_headers"
    ) as mock_create_headers:

        # Setup mocks
        mock_response = MagicMock()
        mock_response.content = zip_content
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {}

        # Call function
        result = download_artifact("owner", "repo", 123, "token")

        # Assertions
        assert result == unicode_content


def test_download_artifact_lcov_with_binary_content():
    """Test download_artifact with binary content that needs UTF-8 decoding."""
    # Create zip with binary content that represents UTF-8 text
    binary_content = "TN:\nSF:test.py\nLF:10\nLH:8\nend_of_record".encode("utf-8")
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr("lcov.info", binary_content)
    zip_buffer.seek(0)
    zip_content = zip_buffer.getvalue()

    with patch("services.github.artifacts.download_artifact.get") as mock_get, patch(
        "services.github.artifacts.download_artifact.create_headers"
    ) as mock_create_headers:

        # Setup mocks
        mock_response = MagicMock()
        mock_response.content = zip_content
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {}

        # Call function
        result = download_artifact("owner", "repo", 123, "token")

        # Assertions
        assert result == "TN:\nSF:test.py\nLF:10\nLH:8\nend_of_record"


def test_download_artifact_multiple_files_with_lcov():
    """Test download_artifact with multiple files including lcov.info."""
    # Create zip with multiple files
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr("README.md", "# Test Project")
        zip_file.writestr("lcov.info", "TN:\nSF:main.py\nLF:20\nLH:18\nend_of_record")
        zip_file.writestr("package.json", '{"name": "test"}')
        zip_file.writestr("src/utils.py", "def helper(): pass")
    zip_buffer.seek(0)
    zip_content = zip_buffer.getvalue()

    with patch("services.github.artifacts.download_artifact.get") as mock_get, patch(
        "services.github.artifacts.download_artifact.create_headers"
    ) as mock_create_headers:

        # Setup mocks
        mock_response = MagicMock()
        mock_response.content = zip_content
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {}

        # Call function
        result = download_artifact("owner", "repo", 123, "token")

        # Assertions
        assert result == "TN:\nSF:main.py\nLF:20\nLH:18\nend_of_record"


def test_download_artifact_exception_handling():
    """Test that exceptions are handled by the decorator."""
    with patch("services.github.artifacts.download_artifact.get") as mock_get, patch(
        "services.github.artifacts.download_artifact.create_headers"
    ) as mock_create_headers:

        # Setup mocks to raise a general exception that will be caught by the decorator
        mock_get.side_effect = Exception("Network error")
        mock_create_headers.return_value = {}

        # Call function - should return default value due to @handle_exceptions decorator
        result = download_artifact("owner", "repo", 123, "token")

        # Assertions
        assert result == ""  # Default return value from decorator


def test_download_artifact_request_timeout():
    """Test that request timeout is handled by the decorator."""
    with patch("services.github.artifacts.download_artifact.get") as mock_get, patch(
        "services.github.artifacts.download_artifact.create_headers"
    ) as mock_create_headers:

        # Setup mocks to raise timeout error
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        mock_create_headers.return_value = {}

        # Call function - should return default value due to @handle_exceptions decorator
        result = download_artifact("owner", "repo", 123, "token")

        # Assertions
        assert result == ""  # Default return value from decorator


def test_download_artifact_invalid_zip_content():
    """Test download_artifact with invalid zip content."""
    with patch("services.github.artifacts.download_artifact.get") as mock_get, patch(
        "services.github.artifacts.download_artifact.create_headers"
    ) as mock_create_headers:

        # Setup mocks with invalid zip content
        mock_response = MagicMock()
        mock_response.content = b"not_a_zip_file"
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {}

        # Call function - should return default value due to @handle_exceptions decorator
        result = download_artifact("owner", "repo", 123, "token")

        # Assertions
        assert result == ""  # Default return value from decorator


def test_download_artifact_url_construction():
    """Test that the GitHub API URL is constructed correctly."""
    with patch("services.github.artifacts.download_artifact.get") as mock_get, patch(
        "services.github.artifacts.download_artifact.create_headers"
    ) as mock_create_headers, patch(
        "services.github.artifacts.download_artifact.zipfile.ZipFile"
    ) as mock_zipfile:

        # Setup mocks
        mock_response = MagicMock()
        mock_response.content = b"zip_content"
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {"Authorization": "Bearer token"}

        mock_zip_instance = MagicMock()
        mock_zip_instance.namelist.return_value = []
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        # Call function
        download_artifact("test-owner", "test-repo", 999, "test-token")

        # Verify URL construction
        expected_url = "https://api.github.com/repos/test-owner/test-repo/actions/artifacts/999/zip"
        mock_get.assert_called_once_with(
            url=expected_url, headers={"Authorization": "Bearer token"}, timeout=120
        )


def test_download_artifact_prints_file_list(mock_zip_with_lcov, capsys):
    """Test that the function prints the file list from the zip."""
    with patch("services.github.artifacts.download_artifact.get") as mock_get, patch(
        "services.github.artifacts.download_artifact.create_headers"
    ) as mock_create_headers:

        # Setup mocks
        mock_response = MagicMock()
        mock_response.content = mock_zip_with_lcov
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {}

        # Call function
        download_artifact("owner", "repo", 123, "token")

        # Check printed output
        captured = capsys.readouterr()
        assert "File list:" in captured.out
        assert "lcov.info" in captured.out
        assert "other_file.txt" in captured.out


@pytest.mark.parametrize(
    "owner,repo,artifact_id,token",
    [
        ("", "repo", 123, "token"),  # Empty owner
        ("owner", "", 123, "token"),  # Empty repo
        ("owner", "repo", 0, "token"),  # Zero artifact_id
        ("owner", "repo", 123, ""),  # Empty token
        ("owner", "repo", -1, "token"),  # Negative artifact_id
    ],
)
def test_download_artifact_edge_case_parameters(owner, repo, artifact_id, token):
    """Test download_artifact with edge case parameters."""
    with patch("services.github.artifacts.download_artifact.get") as mock_get, patch(
        "services.github.artifacts.download_artifact.create_headers"
    ) as mock_create_headers, patch(
        "services.github.artifacts.download_artifact.zipfile.ZipFile"
    ) as mock_zipfile:

        # Setup mocks
        mock_response = MagicMock()
        mock_response.content = b"zip_content"
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {}

        mock_zip_instance = MagicMock()
        mock_zip_instance.namelist.return_value = []
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        # Call function
        result = download_artifact(owner, repo, artifact_id, token)

        # Should still construct URL and make request
        expected_url = f"https://api.github.com/repos/{owner}/{repo}/actions/artifacts/{artifact_id}/zip"
        mock_get.assert_called_once_with(url=expected_url, headers={}, timeout=120)
        assert result is None


def test_download_artifact_large_lcov_content():
    """Test download_artifact with large lcov.info content."""
    # Create large lcov content
    large_content = "TN:\n"
    for i in range(1000):
        large_content += f"SF:file_{i}.py\nLF:100\nLH:80\n"
    large_content += "end_of_record"

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr("lcov.info", large_content.encode("utf-8"))
    zip_buffer.seek(0)
    zip_content = zip_buffer.getvalue()

    with patch("services.github.artifacts.download_artifact.get") as mock_get, patch(
        "services.github.artifacts.download_artifact.create_headers"
    ) as mock_create_headers:

        # Setup mocks
        mock_response = MagicMock()
        mock_response.content = zip_content
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {}

        # Call function
        result = download_artifact("owner", "repo", 123, "token")

        # Assertions
        assert result == large_content
        assert result is not None and len(result) > 10000  # Verify it's actually large
