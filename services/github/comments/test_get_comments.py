from unittest.mock import patch, MagicMock

from services.github.comments.get_comments import get_comments
from config import GITHUB_APP_IDS


def test_get_comments_success(test_owner, test_repo, test_token):
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"body": "Comment 1", "performed_via_github_app": None},
        {"body": "Comment 2", "performed_via_github_app": None},
    ]

    base_args = {"owner": test_owner, "repo": test_repo, "token": test_token}

    # Act
    with patch("services.github.comments.get_comments.requests.get") as mock_get, patch(
        "services.github.comments.get_comments.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}
        mock_get.return_value = mock_response
        result = get_comments(123, base_args)

    # Assert
    mock_get.assert_called_once()
    assert result == ["Comment 1", "Comment 2"]


def test_get_comments_with_app_comments_excluded(test_owner, test_repo, test_token):
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"body": "Comment 1", "performed_via_github_app": None},
        {"body": "Comment 2", "performed_via_github_app": {"id": GITHUB_APP_IDS[0]}},
        {
            "body": "Comment 3",
            "performed_via_github_app": {"id": 999999},
        },  # Not in GITHUB_APP_IDS
    ]

    base_args = {"owner": test_owner, "repo": test_repo, "token": test_token}

    # Act
    with patch("services.github.comments.get_comments.requests.get") as mock_get:
        mock_get.return_value = mock_response
        result = get_comments(123, base_args, includes_me=False)

    # Assert
    mock_get.assert_called_once()
    # Should exclude comments from our app (GITHUB_APP_IDS)
    assert result == ["Comment 1", "Comment 3"]


def test_get_comments_with_app_comments_included(test_owner, test_repo, test_token):
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"body": "Comment 1", "performed_via_github_app": None},
        {"body": "Comment 2", "performed_via_github_app": {"id": GITHUB_APP_IDS[0]}},
        {"body": "Comment 3", "performed_via_github_app": {"id": 999999}},
    ]

    base_args = {"owner": test_owner, "repo": test_repo, "token": test_token}

    # Act
    with patch("services.github.comments.get_comments.requests.get") as mock_get:
        mock_get.return_value = mock_response
        result = get_comments(123, base_args, includes_me=True)

    # Assert
    mock_get.assert_called_once()
    # Should include all comments when includes_me=True
    assert result == ["Comment 1", "Comment 2", "Comment 3"]


def test_get_comments_request_error(test_owner, test_repo, test_token):
    # Arrange
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("API error")

    base_args = {"owner": test_owner, "repo": test_repo, "token": test_token}

    # Act
    with patch("services.github.comments.get_comments.requests.get") as mock_get:
        mock_get.return_value = mock_response
        result = get_comments(123, base_args)

    # Assert
    assert result == []  # The handle_exceptions decorator should return [] on error
