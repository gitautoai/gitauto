from unittest.mock import MagicMock, patch

import requests

from services.github.issues.create_issue import create_issue
from tests.constants import OWNER, REPO, TOKEN
from tests.helpers.create_test_base_args import create_test_base_args


def test_create_issue_success_with_assignees():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "id": 123,
        "html_url": "https://github.com/owner/repo/issues/123",
    }

    base_args = create_test_base_args(owner=OWNER, repo=REPO, token=TOKEN)

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.return_value = mock_response

        result = create_issue("Test Title", "Test Body", ["user1", "user2"], base_args)

    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args.kwargs["json"]["title"] == "Test Title"
    assert call_args.kwargs["json"]["body"] == "Test Body"
    assert call_args.kwargs["json"]["labels"] == ["test-product-id"]
    assert call_args.kwargs["json"]["assignees"] == ["user1", "user2"]
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    assert result == {"id": 123, "html_url": "https://github.com/owner/repo/issues/123"}


def test_create_issue_success_without_assignees():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "id": 456,
        "html_url": "https://github.com/owner/repo/issues/456",
    }

    base_args = create_test_base_args(owner=OWNER, repo=REPO, token=TOKEN)

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.return_value = mock_response

        result = create_issue("Test Title", "Test Body", [], base_args)

    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args.kwargs["json"]["title"] == "Test Title"
    assert call_args.kwargs["json"]["body"] == "Test Body"
    assert call_args.kwargs["json"]["labels"] == ["test-product-id"]
    assert "assignees" not in call_args.kwargs["json"]
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    assert result == {"id": 456, "html_url": "https://github.com/owner/repo/issues/456"}


def test_create_issue_success_with_empty_assignees_list():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "id": 789,
        "html_url": "https://github.com/owner/repo/issues/789",
    }

    base_args = create_test_base_args(owner=OWNER, repo=REPO, token=TOKEN)

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.return_value = mock_response

        result = create_issue("Test Title", "Test Body", [], base_args)

    call_args = mock_post.call_args
    assert "assignees" not in call_args.kwargs["json"]
    mock_response.json.assert_called_once()
    assert result == {"id": 789, "html_url": "https://github.com/owner/repo/issues/789"}


def test_create_issue_http_error():
    mock_response = MagicMock()
    # Create a proper HTTPError with a response object
    http_error = requests.HTTPError("404 Not Found")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 404
    mock_error_response.reason = "Not Found"
    mock_error_response.text = "Repository not found"
    http_error.response = mock_error_response
    mock_response.raise_for_status.side_effect = http_error

    base_args = create_test_base_args(owner=OWNER, repo=REPO, token=TOKEN)

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.return_value = mock_response

        result = create_issue("Test Title", "Test Body", ["user1"], base_args)

    mock_response.raise_for_status.assert_called_once()
    assert result is None


def test_create_issue_request_exception():
    base_args = create_test_base_args(owner=OWNER, repo=REPO, token=TOKEN)

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.side_effect = requests.RequestException("Connection error")

        result = create_issue("Test Title", "Test Body", ["user1"], base_args)

    assert result is None


def test_create_issue_with_none_assignees():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "id": 101,
        "html_url": "https://github.com/owner/repo/issues/101",
    }

    base_args = create_test_base_args(owner=OWNER, repo=REPO, token=TOKEN)

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.return_value = mock_response

        result = create_issue("Test Title", "Test Body", None, base_args)

    call_args = mock_post.call_args
    assert "assignees" not in call_args.kwargs["json"]
    mock_response.json.assert_called_once()
    assert result == {"id": 101, "html_url": "https://github.com/owner/repo/issues/101"}


def test_create_issue_api_url_construction():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "id": 202,
        "html_url": "https://github.com/test-owner/test-repo/issues/202",
    }

    base_args = create_test_base_args(
        owner="test-owner", repo="test-repo", token="test-token"
    )

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.GITHUB_API_URL", "https://api.github.com"
    ), patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_post.return_value = mock_response

        create_issue("Test Title", "Test Body", ["user1"], base_args)

    call_args = mock_post.call_args
    assert (
        call_args.kwargs["url"]
        == "https://api.github.com/repos/test-owner/test-repo/issues"
    )


def test_create_issue_timeout_parameter():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "id": 303,
        "html_url": "https://github.com/owner/repo/issues/303",
    }

    base_args = create_test_base_args(owner=OWNER, repo=REPO, token=TOKEN)

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.TIMEOUT", 60
    ), patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.return_value = mock_response

        create_issue("Test Title", "Test Body", ["user1"], base_args)

    call_args = mock_post.call_args
    assert call_args.kwargs["timeout"] == 60


def test_create_issue_headers_creation():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "id": 404,
        "html_url": "https://github.com/owner/repo/issues/404",
    }

    base_args = create_test_base_args(owner=OWNER, repo=REPO, token="test-token-123")

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": "Bearer test-token-123"}
        mock_post.return_value = mock_response

        create_issue("Test Title", "Test Body", [], base_args)

    mock_create_headers.assert_called_once_with(token="test-token-123")
    call_args = mock_post.call_args
    assert call_args.kwargs["headers"] == {"Authorization": "Bearer test-token-123"}
