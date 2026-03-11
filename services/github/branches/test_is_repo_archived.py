# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import patch, MagicMock

import pytest

from services.github.branches.is_repo_archived import is_repo_archived


@pytest.fixture
def mock_requests_get():
    with patch("services.github.branches.is_repo_archived.requests.get") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    with patch("services.github.branches.is_repo_archived.create_headers") as mock:
        mock.return_value = {"Authorization": "Bearer test-token"}
        yield mock


class TestIsRepoArchived:
    def test_returns_false_for_active_repo(
        self, mock_requests_get, mock_create_headers
    ):
        response = MagicMock()
        response.json.return_value = {"archived": False}
        response.raise_for_status.return_value = None
        mock_requests_get.return_value = response

        assert is_repo_archived("owner", "repo", "token") is False

    def test_returns_true_for_archived_repo(
        self, mock_requests_get, mock_create_headers
    ):
        response = MagicMock()
        response.json.return_value = {"archived": True}
        response.raise_for_status.return_value = None
        mock_requests_get.return_value = response

        assert is_repo_archived("owner", "repo", "token") is True

    def test_defaults_false_when_key_missing(
        self, mock_requests_get, mock_create_headers
    ):
        response = MagicMock()
        response.json.return_value = {"name": "repo"}
        response.raise_for_status.return_value = None
        mock_requests_get.return_value = response

        assert is_repo_archived("owner", "repo", "token") is False
