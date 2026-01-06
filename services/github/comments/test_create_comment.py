from unittest.mock import patch, MagicMock

from services.github.comments.create_comment import create_comment


def test_create_comment_success(test_owner, test_repo, test_token):
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "url": "https://api.github.com/repos/owner/repo/issues/comments/123"
    }

    # Act
    with patch(
        "services.github.comments.create_comment.requests.post"
    ) as mock_post, patch(
        "services.github.comments.create_comment.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}
        mock_post.return_value = mock_response
        result = create_comment(
            owner=test_owner,
            repo=test_repo,
            token=test_token,
            issue_number=123,
            body="Test comment",
        )

    # Assert
    mock_post.assert_called_once()
    assert mock_post.call_args[1]["json"] == {"body": "Test comment"}
    assert result == "https://api.github.com/repos/owner/repo/issues/comments/123"


def test_create_comment_request_error(test_owner, test_repo, test_token):
    # Arrange
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("API error")

    # Act
    with patch("services.github.comments.create_comment.requests.post") as mock_post:
        mock_post.return_value = mock_response
        result = create_comment(
            owner=test_owner,
            repo=test_repo,
            token=test_token,
            issue_number=123,
            body="Test comment",
        )

    # Assert
    assert result is None
