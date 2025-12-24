from unittest.mock import MagicMock, patch

import requests

from services.github.issues.create_issue import create_issue


def test_create_issue_success_with_assignees(test_owner, test_repo, test_token):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 123,
        "html_url": "https://github.com/owner/repo/issues/123",
    }

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}
        mock_post.return_value = mock_response

        status_code, result = create_issue(
            owner=test_owner,
            repo=test_repo,
            token=test_token,
            title="Test Title",
            body="Test Body",
            assignees=["user1", "user2"],
        )

    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args.kwargs["json"]["title"] == "Test Title"
    assert call_args.kwargs["json"]["body"] == "Test Body"
    assert call_args.kwargs["json"]["labels"] == ["test-product-id"]
    assert call_args.kwargs["json"]["assignees"] == ["user1", "user2"]
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    assert status_code == 200
    assert result == {"id": 123, "html_url": "https://github.com/owner/repo/issues/123"}


def test_create_issue_success_without_assignees(test_owner, test_repo, test_token):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 456,
        "html_url": "https://github.com/owner/repo/issues/456",
    }

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}
        mock_post.return_value = mock_response

        status_code, result = create_issue(
            owner=test_owner,
            repo=test_repo,
            token=test_token,
            title="Test Title",
            body="Test Body",
            assignees=[],
        )

    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args.kwargs["json"]["title"] == "Test Title"
    assert call_args.kwargs["json"]["body"] == "Test Body"
    assert call_args.kwargs["json"]["labels"] == ["test-product-id"]
    assert "assignees" not in call_args.kwargs["json"]
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    assert status_code == 200
    assert result == {"id": 456, "html_url": "https://github.com/owner/repo/issues/456"}


def test_create_issue_success_with_empty_assignees_list(
    test_owner, test_repo, test_token
):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 789,
        "html_url": "https://github.com/owner/repo/issues/789",
    }

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}
        mock_post.return_value = mock_response

        status_code, result = create_issue(
            owner=test_owner,
            repo=test_repo,
            token=test_token,
            title="Test Title",
            body="Test Body",
            assignees=[],
        )

    call_args = mock_post.call_args
    assert "assignees" not in call_args.kwargs["json"]
    mock_response.json.assert_called_once()
    assert status_code == 200
    assert result == {"id": 789, "html_url": "https://github.com/owner/repo/issues/789"}


def test_create_issue_http_error(test_owner, test_repo, test_token):
    mock_response = MagicMock()
    # Create a proper HTTPError with a response object
    http_error = requests.HTTPError("404 Not Found")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 404
    mock_error_response.reason = "Not Found"
    mock_error_response.text = "Repository not found"
    http_error.response = mock_error_response
    mock_response.raise_for_status.side_effect = http_error

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}
        mock_post.return_value = mock_response

        status_code, result = create_issue(
            owner=test_owner,
            repo=test_repo,
            token=test_token,
            title="Test Title",
            body="Test Body",
            assignees=["user1"],
        )

    mock_response.raise_for_status.assert_called_once()
    assert status_code == 500
    assert result is None


def test_create_issue_request_exception(test_owner, test_repo, test_token):
    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}
        mock_post.side_effect = requests.RequestException("Connection error")

        status_code, result = create_issue(
            owner=test_owner,
            repo=test_repo,
            token=test_token,
            title="Test Title",
            body="Test Body",
            assignees=["user1"],
        )

    assert status_code == 500
    assert result is None


def test_create_issue_with_none_assignees(test_owner, test_repo, test_token):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 101,
        "html_url": "https://github.com/owner/repo/issues/101",
    }

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}
        mock_post.return_value = mock_response

        status_code, result = create_issue(
            owner=test_owner,
            repo=test_repo,
            token=test_token,
            title="Test Title",
            body="Test Body",
            assignees=[],
        )

    call_args = mock_post.call_args
    assert "assignees" not in call_args.kwargs["json"]
    mock_response.json.assert_called_once()
    assert status_code == 200
    assert result == {"id": 101, "html_url": "https://github.com/owner/repo/issues/101"}


def test_create_issue_api_url_construction():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 202,
        "html_url": "https://github.com/test-owner/test-repo/issues/202",
    }

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.GITHUB_API_URL", "https://api.github.com"
    ), patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_post.return_value = mock_response

        create_issue(
            owner="test-owner",
            repo="test-repo",
            token="test-token",
            title="Test Title",
            body="Test Body",
            assignees=["user1"],
        )

    call_args = mock_post.call_args
    assert (
        call_args.kwargs["url"]
        == "https://api.github.com/repos/test-owner/test-repo/issues"
    )


def test_create_issue_timeout_parameter(test_owner, test_repo, test_token):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 303,
        "html_url": "https://github.com/owner/repo/issues/303",
    }

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.TIMEOUT", 60
    ), patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}
        mock_post.return_value = mock_response

        create_issue(
            owner=test_owner,
            repo=test_repo,
            token=test_token,
            title="Test Title",
            body="Test Body",
            assignees=["user1"],
        )

    call_args = mock_post.call_args
    assert call_args.kwargs["timeout"] == 60


def test_create_issue_headers_creation(test_owner, test_repo):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 404,
        "html_url": "https://github.com/owner/repo/issues/404",
    }

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": "Bearer test-token-123"}
        mock_post.return_value = mock_response

        create_issue(
            owner=test_owner,
            repo=test_repo,
            token="test-token-123",
            title="Test Title",
            body="Test Body",
            assignees=[],
        )

    mock_create_headers.assert_called_once_with(token="test-token-123")
    call_args = mock_post.call_args
    assert call_args.kwargs["headers"] == {"Authorization": "Bearer test-token-123"}


def test_create_issue_retry_on_invalid_assignees(test_owner, test_repo, test_token):
    # Mock first response with 422 error
    mock_first_response = MagicMock()
    mock_first_response.status_code = 422
    mock_first_response.text = '{"message":"Validation Failed","errors":[{"value":["Copilot"],"resource":"Issue","field":"assignees","code":"invalid"}]}'

    # Mock second response (successful retry)
    mock_second_response = MagicMock()
    mock_second_response.raise_for_status.return_value = None
    mock_second_response.status_code = 200
    mock_second_response.json.return_value = {
        "id": 555,
        "html_url": "https://github.com/owner/repo/issues/555",
    }

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}
        # First call returns 422, second call succeeds
        mock_post.side_effect = [mock_first_response, mock_second_response]

        status_code, result = create_issue(
            owner=test_owner,
            repo=test_repo,
            token=test_token,
            title="Test Title",
            body="Test Body",
            assignees=["Copilot"],
        )

    # Should make two calls - first with assignees, second without
    assert mock_post.call_count == 2

    # First call should have assignees
    first_call_args = mock_post.call_args_list[0]
    assert first_call_args.kwargs["json"]["assignees"] == ["Copilot"]

    # Second call should not have assignees
    second_call_args = mock_post.call_args_list[1]
    assert "assignees" not in second_call_args.kwargs["json"]
    assert second_call_args.kwargs["json"]["title"] == "Test Title"
    assert second_call_args.kwargs["json"]["body"] == "Test Body"
    assert second_call_args.kwargs["json"]["labels"] == ["test-product-id"]

    mock_second_response.raise_for_status.assert_called_once()
    mock_second_response.json.assert_called_once()
    assert status_code == 200
    assert result == {"id": 555, "html_url": "https://github.com/owner/repo/issues/555"}


def test_create_issue_410_issues_disabled(test_owner, test_repo, test_token):
    """Test that create_issue handles 410 Gone (issues disabled) correctly."""
    mock_response = MagicMock()
    mock_response.status_code = 410
    mock_response.raise_for_status.return_value = None  # Won't be called for 410

    with patch("services.github.issues.create_issue.requests.post") as mock_post, patch(
        "services.github.issues.create_issue.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.create_issue.PRODUCT_ID", "test-product-id"
    ), patch(
        "services.github.issues.create_issue.logging"
    ) as mock_logging:
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}
        mock_post.return_value = mock_response

        status_code, result = create_issue(
            owner=test_owner,
            repo=test_repo,
            token=test_token,
            title="Test Title",
            body="Test Body",
            assignees=["user1"],
        )

    # Verify the function returns 410 status and None
    assert status_code == 410
    assert result is None

    # Verify that raise_for_status was NOT called (we handle 410 specially)
    mock_response.raise_for_status.assert_not_called()

    # Verify that a warning was logged
    mock_logging.warning.assert_called_once()
    call_args = mock_logging.warning.call_args
    warning_msg = call_args[0][0]
    warning_args = call_args[0][1:]
    assert "Issues are disabled" in warning_msg
    assert warning_args == (test_owner, test_repo)
