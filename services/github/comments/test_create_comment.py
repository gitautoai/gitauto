from unittest.mock import MagicMock, patch

from services.github.comments.create_comment import create_comment


def test_create_comment_success(
    test_owner, test_repo, test_token, create_test_base_args
):
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "url": "https://api.github.com/repos/owner/repo/issues/comments/123"
    }
    comment_args = create_test_base_args(
        owner=test_owner,
        repo=test_repo,
        token=test_token,
        pr_number=123,
    )

    # Act
    with patch(
        "services.github.comments.create_comment.requests.post"
    ) as mock_post, patch(
        "services.github.comments.create_comment.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}
        mock_post.return_value = mock_response
        result = create_comment(body="Test comment", base_args=comment_args)

    # Assert
    mock_post.assert_called_once()
    assert mock_post.call_args[1]["json"] == {"body": "Test comment"}
    assert result == "https://api.github.com/repos/owner/repo/issues/comments/123"


def test_create_comment_request_error(
    test_owner, test_repo, test_token, create_test_base_args
):
    # Arrange
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("API error")
    comment_args = create_test_base_args(
        owner=test_owner,
        repo=test_repo,
        token=test_token,
        pr_number=123,
    )

    # Act
    with patch("services.github.comments.create_comment.requests.post") as mock_post:
        mock_post.return_value = mock_response
        result = create_comment(body="Test comment", base_args=comment_args)

    # Assert
    assert result is None


def test_create_comment_returns_none_when_url_is_not_str(
    test_owner, test_repo, test_token, create_test_base_args
):
    """If GitHub returns a non-string url field, the helper should return None."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"url": 12345}
    comment_args = create_test_base_args(
        owner=test_owner,
        repo=test_repo,
        token=test_token,
        pr_number=123,
    )

    with patch(
        "services.github.comments.create_comment.requests.post"
    ) as mock_post, patch(
        "services.github.comments.create_comment.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}
        mock_post.return_value = mock_response
        result = create_comment(body="Test", base_args=comment_args)

    assert result is None
