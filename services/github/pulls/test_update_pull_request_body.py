# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import patch, MagicMock
import pytest
import requests
from services.github.pulls.update_pull_request_body import update_pull_request_body

OWNER = "owner"
REPO = "repo"
PR_NUMBER = 42
TOKEN = "test_token_123"
EXPECTED_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls/{PR_NUMBER}"


@pytest.fixture
def mock_requests_patch():
    with patch("services.github.pulls.update_pull_request_body.requests.patch") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    with patch("services.github.pulls.update_pull_request_body.create_headers") as mock:
        mock.return_value = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        yield mock


@pytest.fixture
def sample_response_data():
    return {
        "id": 123456789,
        "number": 42,
        "title": "Test Pull Request",
        "body": "Updated pull request body",
        "state": "open",
        "user": {"login": "testuser", "id": 12345},
        "html_url": "https://github.com/owner/repo/pull/42",
    }


def test_update_pull_request_body_success(
    mock_requests_patch, mock_create_headers, sample_response_data
):
    mock_response = MagicMock()
    mock_response.json.return_value = sample_response_data
    mock_requests_patch.return_value = mock_response
    body = "Updated pull request body"

    result = update_pull_request_body(
        owner_name=OWNER, repo_name=REPO, pr_number=PR_NUMBER, token=TOKEN, body=body
    )

    assert result == sample_response_data
    mock_create_headers.assert_called_once_with(token=TOKEN)
    mock_requests_patch.assert_called_once_with(
        url=EXPECTED_URL,
        headers=mock_create_headers.return_value,
        json={"body": body},
        timeout=120,
    )
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()


def test_update_pull_request_body_with_empty_body(
    mock_requests_patch, mock_create_headers, sample_response_data
):
    mock_response = MagicMock()
    sample_response_data["body"] = ""
    mock_response.json.return_value = sample_response_data
    mock_requests_patch.return_value = mock_response
    body = ""

    result = update_pull_request_body(
        owner_name=OWNER, repo_name=REPO, pr_number=PR_NUMBER, token=TOKEN, body=body
    )

    assert result == sample_response_data
    mock_requests_patch.assert_called_once_with(
        url=EXPECTED_URL,
        headers=mock_create_headers.return_value,
        json={"body": body},
        timeout=120,
    )


def test_update_pull_request_body_with_multiline_body(
    mock_requests_patch, mock_create_headers, sample_response_data
):
    mock_response = MagicMock()
    multiline_body = "Line 1\nLine 2\n\nLine 4 with **markdown**"
    sample_response_data["body"] = multiline_body
    mock_response.json.return_value = sample_response_data
    mock_requests_patch.return_value = mock_response

    result = update_pull_request_body(
        owner_name=OWNER,
        repo_name=REPO,
        pr_number=PR_NUMBER,
        token=TOKEN,
        body=multiline_body,
    )

    assert result == sample_response_data
    mock_requests_patch.assert_called_once_with(
        url=EXPECTED_URL,
        headers=mock_create_headers.return_value,
        json={"body": multiline_body},
        timeout=120,
    )


def test_update_pull_request_body_with_special_characters(
    mock_requests_patch, mock_create_headers, sample_response_data
):
    mock_response = MagicMock()
    special_body = "Body with émojis 🚀 and special chars: <>&\"'"
    sample_response_data["body"] = special_body
    mock_response.json.return_value = sample_response_data
    mock_requests_patch.return_value = mock_response

    result = update_pull_request_body(
        owner_name=OWNER,
        repo_name=REPO,
        pr_number=PR_NUMBER,
        token=TOKEN,
        body=special_body,
    )

    assert result == sample_response_data
    mock_requests_patch.assert_called_once_with(
        url=EXPECTED_URL,
        headers=mock_create_headers.return_value,
        json={"body": special_body},
        timeout=120,
    )


def test_update_pull_request_body_http_error(mock_requests_patch, mock_create_headers):
    mock_response = MagicMock()
    http_error = requests.exceptions.HTTPError("404 Not Found")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 404
    http_error.response = mock_error_response
    mock_error_response.reason = "Not Found"
    mock_error_response.text = "Pull request not found"
    mock_response.raise_for_status.side_effect = http_error
    mock_error_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Used": "1",
    }
    mock_requests_patch.return_value = mock_response

    result = update_pull_request_body(
        owner_name=OWNER, repo_name=REPO, pr_number=999, token=TOKEN, body="Test body"
    )

    assert result is None
    mock_requests_patch.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


def test_update_pull_request_body_connection_error(
    mock_requests_patch, mock_create_headers
):
    mock_requests_patch.side_effect = requests.exceptions.ConnectionError(
        "Connection failed"
    )

    result = update_pull_request_body(
        owner_name=OWNER,
        repo_name=REPO,
        pr_number=PR_NUMBER,
        token=TOKEN,
        body="Test body",
    )

    assert result is None
    mock_requests_patch.assert_called_once()


def test_update_pull_request_body_timeout_error(
    mock_requests_patch, mock_create_headers
):
    mock_requests_patch.side_effect = requests.exceptions.Timeout("Request timed out")

    result = update_pull_request_body(
        owner_name=OWNER,
        repo_name=REPO,
        pr_number=PR_NUMBER,
        token=TOKEN,
        body="Test body",
    )

    assert result is None
    mock_requests_patch.assert_called_once()


def test_update_pull_request_body_json_decode_error(
    mock_requests_patch, mock_create_headers
):
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_requests_patch.return_value = mock_response

    result = update_pull_request_body(
        owner_name=OWNER,
        repo_name=REPO,
        pr_number=PR_NUMBER,
        token=TOKEN,
        body="Test body",
    )

    assert result is None
    mock_requests_patch.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()


def test_update_pull_request_body_uses_correct_timeout(
    mock_requests_patch, mock_create_headers
):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 123}
    mock_requests_patch.return_value = mock_response

    update_pull_request_body(
        owner_name=OWNER, repo_name=REPO, pr_number=PR_NUMBER, token=TOKEN, body="body"
    )

    call_args = mock_requests_patch.call_args
    assert call_args.kwargs["timeout"] == 120


def test_update_pull_request_body_with_very_long_body(
    mock_requests_patch, mock_create_headers, sample_response_data
):
    mock_response = MagicMock()
    long_body = "A" * 10000
    sample_response_data["body"] = long_body
    mock_response.json.return_value = sample_response_data
    mock_requests_patch.return_value = mock_response

    result = update_pull_request_body(
        owner_name=OWNER,
        repo_name=REPO,
        pr_number=PR_NUMBER,
        token=TOKEN,
        body=long_body,
    )

    assert result == sample_response_data
    mock_requests_patch.assert_called_once_with(
        url=EXPECTED_URL,
        headers=mock_create_headers.return_value,
        json={"body": long_body},
        timeout=120,
    )


def test_update_pull_request_body_with_different_owner_repo(
    mock_requests_patch, mock_create_headers, sample_response_data
):
    mock_response = MagicMock()
    mock_response.json.return_value = sample_response_data
    mock_requests_patch.return_value = mock_response
    body = "Test body"

    result = update_pull_request_body(
        owner_name="org-name",
        repo_name="repo-name",
        pr_number=999,
        token=TOKEN,
        body=body,
    )

    assert result == sample_response_data
    mock_requests_patch.assert_called_once_with(
        url="https://api.github.com/repos/org-name/repo-name/pulls/999",
        headers=mock_create_headers.return_value,
        json={"body": body},
        timeout=120,
    )


def test_update_pull_request_body_headers_called_correctly(
    mock_requests_patch, mock_create_headers
):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 123}
    mock_requests_patch.return_value = mock_response
    token = "custom_test_token_456"

    update_pull_request_body(
        owner_name=OWNER,
        repo_name=REPO,
        pr_number=PR_NUMBER,
        token=token,
        body="Test body",
    )

    mock_create_headers.assert_called_once_with(token=token)


@pytest.mark.parametrize(
    "body_content",
    [
        "",
        "Simple body",
        "Body with\nmultiple\nlines",
        "Body with **markdown** and _formatting_",
        "Body with émojis 🚀 and unicode ñáéíóú",
        "Body with special chars: <>&\"'",
        None,
        "A" * 1000,
    ],
)
def test_update_pull_request_body_with_various_body_contents(
    mock_requests_patch, mock_create_headers, body_content
):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 123, "body": body_content}
    mock_requests_patch.return_value = mock_response

    result = update_pull_request_body(
        owner_name=OWNER,
        repo_name=REPO,
        pr_number=PR_NUMBER,
        token=TOKEN,
        body=body_content,
    )

    assert result == {"id": 123, "body": body_content}
    mock_requests_patch.assert_called_once_with(
        url=EXPECTED_URL,
        headers=mock_create_headers.return_value,
        json={"body": body_content},
        timeout=120,
    )

    mock_requests_patch.reset_mock()
    mock_create_headers.reset_mock()


def test_update_pull_request_body_request_structure(
    mock_requests_patch, mock_create_headers
):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 123}
    mock_requests_patch.return_value = mock_response

    expected_headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": "Bearer test_token",
        "User-Agent": "GitAuto",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    mock_create_headers.return_value = expected_headers
    body = "Test body content"

    update_pull_request_body(
        owner_name=OWNER, repo_name=REPO, pr_number=PR_NUMBER, token=TOKEN, body=body
    )

    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    assert call_args.kwargs["url"] == EXPECTED_URL
    assert call_args.kwargs["headers"] == expected_headers
    assert call_args.kwargs["json"] == {"body": body}
    assert call_args.kwargs["timeout"] == 120
    expected_kwargs = {"url", "headers", "json", "timeout"}
    assert set(call_args.kwargs.keys()) == expected_kwargs


def test_update_pull_request_body_response_processing(
    mock_requests_patch, mock_create_headers
):
    expected_response_data = {
        "id": 987654321,
        "number": 42,
        "title": "Updated PR",
        "body": "New body content",
        "state": "open",
        "html_url": "https://github.com/owner/repo/pull/42",
    }
    mock_response = MagicMock()
    mock_response.json.return_value = expected_response_data
    mock_requests_patch.return_value = mock_response

    result = update_pull_request_body(
        owner_name=OWNER, repo_name=REPO, pr_number=PR_NUMBER, token=TOKEN, body="body"
    )

    assert result == expected_response_data
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    assert result["id"] == 987654321
    assert result["number"] == 42
    assert result["body"] == "New body content"
