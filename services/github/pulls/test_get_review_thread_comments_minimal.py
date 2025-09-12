from unittest.mock import patch, MagicMock
import pytest
from services.github.pulls.get_review_thread_comments import get_review_thread_comments


@pytest.fixture
def mock_graphql_client():
    """Fixture to provide a mocked GraphQL client."""
    with patch(
        "services.github.pulls.get_review_thread_comments.get_graphql_client"
    ) as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


def test_get_review_thread_comments_basic(mock_graphql_client):
    """Basic test to verify the function works."""
    # Arrange
    mock_graphql_client.execute.return_value = {
        "repository": {"pullRequest": {"reviewThreads": {"nodes": []}}}
    }

    # Act
    result = get_review_thread_comments("owner", "repo", 123, "comment_id", "token")

    # Assert
    assert result == []
    mock_graphql_client.execute.assert_called_once()
