# pylint: disable=unused-argument,too-many-instance-attributes
import inspect
from unittest.mock import MagicMock, patch

import pytest
import requests
from faker import Faker

from config import TIMEOUT
from services.github.comments.get_all_comments import get_all_comments

fake = Faker()


@pytest.fixture
def owner():
    return fake.user_name()


@pytest.fixture
def repo():
    return fake.slug()


@pytest.fixture
def token():
    return fake.sha256()


@pytest.fixture
def mock_requests_get():
    with patch("services.github.comments.get_all_comments.get") as mock:
        yield mock


@pytest.fixture
def mock_create_headers(token):
    with patch("services.github.comments.get_all_comments.create_headers") as mock:
        mock.return_value = {"Authorization": f"Bearer {token}"}
        yield mock


def test_get_all_comments_success(
    owner, repo, token, mock_requests_get, mock_create_headers
):
    expected_comments = [
        {"id": 1, "body": "First comment", "user": {"login": "user1"}},
        {"id": 2, "body": "Second comment", "user": {"login": "user2"}},
    ]
    mock_response = MagicMock()
    mock_response.json.return_value = expected_comments
    mock_requests_get.return_value = mock_response

    result = get_all_comments(owner=owner, repo=repo, issue_number=123, token=token)

    assert result == expected_comments
    mock_create_headers.assert_called_once_with(token=token)
    mock_requests_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


def test_get_all_comments_empty_response(owner, repo, token, mock_requests_get):
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response

    result = get_all_comments(owner=owner, repo=repo, issue_number=123, token=token)

    assert result == []
    mock_requests_get.assert_called_once()


def test_get_all_comments_correct_url_construction(
    owner, repo, token, mock_requests_get
):
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response

    get_all_comments(owner=owner, repo=repo, issue_number=123, token=token)

    expected_url = f"https://api.github.com/repos/{owner}/{repo}/issues/123/comments"
    call_args = mock_requests_get.call_args
    assert call_args[1]["url"] == expected_url


def test_get_all_comments_timeout_parameter(owner, repo, token, mock_requests_get):
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response

    get_all_comments(owner=owner, repo=repo, issue_number=123, token=token)

    call_args = mock_requests_get.call_args
    assert "timeout" in call_args[1]
    assert call_args[1]["timeout"] == TIMEOUT


def test_get_all_comments_http_error(owner, repo, token, mock_requests_get):
    mock_response = MagicMock()
    http_error = requests.exceptions.HTTPError("404 Not Found")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 404
    mock_error_response.reason = "Not Found"
    mock_error_response.text = "Repository not found"
    http_error.response = mock_error_response
    mock_response.raise_for_status.side_effect = http_error
    mock_requests_get.return_value = mock_response

    result = get_all_comments(owner=owner, repo=repo, issue_number=123, token=token)

    assert result == []


def test_get_all_comments_network_error(owner, repo, token, mock_requests_get):
    mock_requests_get.side_effect = requests.exceptions.ConnectionError("Network error")

    result = get_all_comments(owner=owner, repo=repo, issue_number=123, token=token)

    assert result == []


def test_get_all_comments_uses_github_api_url_constant(
    owner, repo, token, mock_requests_get
):
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response

    with patch(
        "services.github.comments.get_all_comments.GITHUB_API_URL",
        "https://custom.api.github.com",
    ):
        get_all_comments(owner=owner, repo=repo, issue_number=123, token=token)

    expected_url = (
        f"https://custom.api.github.com/repos/{owner}/{repo}/issues/123/comments"
    )
    call_args = mock_requests_get.call_args
    assert call_args[1]["url"] == expected_url


def test_get_all_comments_decorator_configuration():
    assert hasattr(get_all_comments, "__wrapped__")


def test_get_all_comments_function_signature_compliance():
    sig = inspect.signature(get_all_comments)
    params = list(sig.parameters.keys())
    expected_params = ["owner", "repo", "issue_number", "token"]
    assert params == expected_params
