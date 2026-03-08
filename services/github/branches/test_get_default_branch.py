# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import json
from unittest.mock import patch, MagicMock

import pytest
import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.branches.get_default_branch import RepoInfo, get_default_branch


@pytest.fixture
def mock_requests_get():
    with patch("services.github.branches.get_default_branch.requests.get") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    with patch("services.github.branches.get_default_branch.create_headers") as mock:
        mock.return_value = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test-token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        yield mock


@pytest.fixture
def sample_repo_response():
    return {
        "id": 123456789,
        "name": "test-repo",
        "full_name": "test-owner/test-repo",
        "default_branch": "main",
        "private": False,
        "size": 108,
        "archived": False,
    }


@pytest.fixture
def sample_empty_repo_response():
    return {
        "id": 123456789,
        "name": "test-repo",
        "full_name": "test-owner/test-repo",
        "default_branch": "main",
        "private": False,
        "size": 0,
        "archived": False,
    }


@pytest.fixture
def sample_archived_repo_response():
    return {
        "id": 123456789,
        "name": "test-repo",
        "full_name": "test-owner/test-repo",
        "default_branch": "main",
        "private": False,
        "size": 108,
        "archived": True,
    }


class TestGetDefaultBranch:
    def test_successful_request(
        self, mock_requests_get, mock_create_headers, sample_repo_response
    ):
        repo_response = MagicMock()
        repo_response.json.return_value = sample_repo_response
        repo_response.raise_for_status.return_value = None
        mock_requests_get.return_value = repo_response

        result = get_default_branch("test-owner", "test-repo", "test-token")

        assert result == RepoInfo(
            default_branch="main", is_empty=False, is_archived=False
        )
        mock_requests_get.assert_called_once()
        call_args = mock_requests_get.call_args
        assert call_args[1]["url"] == f"{GITHUB_API_URL}/repos/test-owner/test-repo"
        assert call_args[1]["timeout"] == TIMEOUT

    def test_empty_repository(
        self, mock_requests_get, mock_create_headers, sample_empty_repo_response
    ):
        repo_response = MagicMock()
        repo_response.json.return_value = sample_empty_repo_response
        repo_response.raise_for_status.return_value = None
        mock_requests_get.return_value = repo_response

        result = get_default_branch("test-owner", "test-repo", "test-token")

        assert result == RepoInfo(
            default_branch="main", is_empty=True, is_archived=False
        )

    def test_archived_repository(
        self, mock_requests_get, mock_create_headers, sample_archived_repo_response
    ):
        repo_response = MagicMock()
        repo_response.json.return_value = sample_archived_repo_response
        repo_response.raise_for_status.return_value = None
        mock_requests_get.return_value = repo_response

        result = get_default_branch("test-owner", "test-repo", "test-token")

        assert result == RepoInfo(
            default_branch="main", is_empty=False, is_archived=True
        )

    def test_different_default_branch(self, mock_requests_get, mock_create_headers):
        repo_response_data = {
            "id": 123456789,
            "name": "test-repo",
            "full_name": "test-owner/test-repo",
            "default_branch": "develop",
            "private": False,
            "size": 500,
            "archived": False,
        }
        repo_response = MagicMock()
        repo_response.json.return_value = repo_response_data
        repo_response.raise_for_status.return_value = None
        mock_requests_get.return_value = repo_response

        result = get_default_branch("test-owner", "test-repo", "test-token")

        assert result == RepoInfo(
            default_branch="develop", is_empty=False, is_archived=False
        )

    def test_http_error(self, mock_requests_get, mock_create_headers):
        http_error = requests.exceptions.HTTPError("404 Not Found")
        http_error.response = MagicMock()
        http_error.response.status_code = 404
        http_error.response.reason = "Not Found"
        http_error.response.text = "Repository not found"

        repo_response = MagicMock()
        repo_response.raise_for_status.side_effect = http_error
        mock_requests_get.return_value = repo_response

        with pytest.raises(requests.exceptions.HTTPError):
            get_default_branch("test-owner", "nonexistent-repo", "test-token")

    def test_json_decode_error(self, mock_requests_get, mock_create_headers):
        repo_response = MagicMock()
        repo_response.raise_for_status.return_value = None
        repo_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_requests_get.return_value = repo_response

        with pytest.raises(json.JSONDecodeError):
            get_default_branch("test-owner", "test-repo", "test-token")

    def test_missing_default_branch_key(self, mock_requests_get, mock_create_headers):
        repo_response_data = {
            "id": 123456789,
            "name": "test-repo",
            "full_name": "test-owner/test-repo",
            "private": False,
            "size": 100,
        }
        repo_response = MagicMock()
        repo_response.json.return_value = repo_response_data
        repo_response.raise_for_status.return_value = None
        mock_requests_get.return_value = repo_response

        with pytest.raises(KeyError):
            get_default_branch("test-owner", "test-repo", "test-token")

    def test_missing_size_key(self, mock_requests_get, mock_create_headers):
        repo_response_data = {
            "id": 123456789,
            "name": "test-repo",
            "full_name": "test-owner/test-repo",
            "default_branch": "main",
            "private": False,
        }
        repo_response = MagicMock()
        repo_response.json.return_value = repo_response_data
        repo_response.raise_for_status.return_value = None
        mock_requests_get.return_value = repo_response

        with pytest.raises(KeyError):
            get_default_branch("test-owner", "test-repo", "test-token")

    def test_return_type(
        self, mock_requests_get, mock_create_headers, sample_repo_response
    ):
        repo_response = MagicMock()
        repo_response.json.return_value = sample_repo_response
        repo_response.raise_for_status.return_value = None
        mock_requests_get.return_value = repo_response

        result = get_default_branch("test-owner", "test-repo", "test-token")

        assert isinstance(result, RepoInfo)
        assert isinstance(result.default_branch, str)
        assert isinstance(result.is_empty, bool)
        assert isinstance(result.is_archived, bool)

    @pytest.mark.parametrize(
        "owner,repo,expected_url",
        [
            ("test-owner", "test-repo", f"{GITHUB_API_URL}/repos/test-owner/test-repo"),
            ("org-name", "my-project", f"{GITHUB_API_URL}/repos/org-name/my-project"),
            (
                "user123",
                "repo-with-dashes",
                f"{GITHUB_API_URL}/repos/user123/repo-with-dashes",
            ),
        ],
    )
    def test_url_construction(
        self,
        mock_requests_get,
        mock_create_headers,
        sample_repo_response,
        owner,
        repo,
        expected_url,
    ):
        repo_response = MagicMock()
        repo_response.json.return_value = sample_repo_response
        repo_response.raise_for_status.return_value = None
        mock_requests_get.return_value = repo_response

        get_default_branch(owner, repo, "test-token")

        call_args = mock_requests_get.call_args
        assert call_args[1]["url"] == expected_url

    @pytest.mark.parametrize(
        "default_branch,size,archived,expected",
        [
            ("main", 100, False, RepoInfo("main", False, False)),
            ("master", 0, False, RepoInfo("master", True, False)),
            ("develop", 500, True, RepoInfo("develop", False, True)),
            ("feature-branch", 0, True, RepoInfo("feature-branch", True, True)),
        ],
    )
    def test_various_branch_names_and_sizes(
        self,
        mock_requests_get,
        mock_create_headers,
        default_branch,
        size,
        archived,
        expected,
    ):
        repo_response_data = {
            "id": 123456789,
            "name": "test-repo",
            "full_name": "test-owner/test-repo",
            "default_branch": default_branch,
            "private": False,
            "size": size,
            "archived": archived,
        }
        repo_response = MagicMock()
        repo_response.json.return_value = repo_response_data
        repo_response.raise_for_status.return_value = None
        mock_requests_get.return_value = repo_response

        result = get_default_branch("test-owner", "test-repo", "test-token")

        assert result == expected

    def test_missing_archived_key_defaults_false(
        self, mock_requests_get, mock_create_headers
    ):
        repo_response_data = {
            "id": 123456789,
            "name": "test-repo",
            "full_name": "test-owner/test-repo",
            "default_branch": "main",
            "private": False,
            "size": 100,
        }
        repo_response = MagicMock()
        repo_response.json.return_value = repo_response_data
        repo_response.raise_for_status.return_value = None
        mock_requests_get.return_value = repo_response

        result = get_default_branch("test-owner", "test-repo", "test-token")

        assert result.is_archived is False
