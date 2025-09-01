# Standard imports
from unittest.mock import MagicMock, patch

# Third party imports
import pytest
from gql.transport.exceptions import TransportError

# Local imports
from services.github.pulls.get_review_thread_comments import get_review_thread_comments


@pytest.fixture
def mock_graphql_client():
    """Fixture to provide a mocked GraphQL client."""
    with patch("services.github.pulls.get_review_thread_comments.get_graphql_client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_params():
    """Fixture to provide sample parameters for testing."""
    return {
        "owner": "test-owner",
        "repo": "test-repo",
        "pull_number": 123,
        "comment_node_id": "target_comment_456",
        "token": "test-token",
    }


@pytest.fixture
def mock_response_with_target_comment():
    """Fixture providing a mock response where target comment is found."""
    return {
        "repository": {
            "pullRequest": {
                "reviewThreads": {
                    "nodes": [
                        {
                            "comments": {
                                "nodes": [
                                    {
                                        "id": "comment_123",
                                        "author": {"login": "user1"},
                                        "body": "First comment",
                                        "createdAt": "2023-01-01T00:00:00Z"
                                    },
                                    {
                                        "id": "target_comment_456",
                                        "author": {"login": "user2"},
                                        "body": "Target comment",
                                        "createdAt": "2023-01-02T00:00:00Z"
                                    }
                                ]
                            }
                        },
                        {
                            "comments": {
                                "nodes": [
                                    {
                                        "id": "comment_789",
                                        "author": {"login": "user3"},
                                        "body": "Other thread comment",
                                        "createdAt": "2023-01-03T00:00:00Z"
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }
    }


def test_get_review_thread_comments_success_comment_found(
    mock_graphql_client, sample_params, mock_response_with_target_comment
):
    """Test successful retrieval when comment is found in a thread."""
    # Arrange
    mock_graphql_client.execute.return_value = mock_response_with_target_comment

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    mock_graphql_client.execute.assert_called_once()
    
    # Verify result - should return the comments from the thread containing target comment
    expected_comments = [
        {
            "id": "comment_123",
            "author": {"login": "user1"},
            "body": "First comment",
            "createdAt": "2023-01-01T00:00:00Z"
        },
        {
            "id": "target_comment_456",
            "author": {"login": "user2"},
            "body": "Target comment",
            "createdAt": "2023-01-02T00:00:00Z"
        }
    ]
    assert result == expected_comments


def test_get_review_thread_comments_comment_not_found(mock_graphql_client, sample_params):
    """Test when the target comment is not found in any thread."""
    # Arrange
    mock_response = {
        "repository": {
            "pullRequest": {
                "reviewThreads": {
                    "nodes": [
                        {
                            "comments": {
                                "nodes": [
                                    {
                                        "id": "comment_123",
                                        "author": {"login": "user1"},
                                        "body": "Some comment",
                                        "createdAt": "2023-01-01T00:00:00Z"
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }
    }
    mock_graphql_client.execute.return_value = mock_response

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    assert result == []


def test_get_review_thread_comments_empty_threads(mock_graphql_client, sample_params):
    """Test when there are no review threads."""
    # Arrange
    mock_response = {
        "repository": {
            "pullRequest": {
                "reviewThreads": {
                    "nodes": []
                }
            }
        }
    }
    mock_graphql_client.execute.return_value = mock_response

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    assert result == []


def test_get_review_thread_comments_empty_comments_in_thread(mock_graphql_client, sample_params):
    """Test when threads exist but have no comments."""
    # Arrange
    mock_response = {
        "repository": {
            "pullRequest": {
                "reviewThreads": {
                    "nodes": [
                        {
                            "comments": {
                                "nodes": []
                            }
                        }
                    ]
                }
            }
        }
    }
    mock_graphql_client.execute.return_value = mock_response

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    assert result == []


def test_get_review_thread_comments_missing_repository(mock_graphql_client, sample_params):
    """Test when repository is not found in response."""
    # Arrange
    mock_response = {}
    mock_graphql_client.execute.return_value = mock_response

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    assert result == []


def test_get_review_thread_comments_missing_pull_request(mock_graphql_client, sample_params):
    """Test when pull request is not found in response."""
    # Arrange
    mock_response = {
        "repository": {}
    }
    mock_graphql_client.execute.return_value = mock_response

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    assert result == []


def test_get_review_thread_comments_transport_error(sample_params):
    """Test handling of GraphQL transport error."""
    # Arrange
    with patch("services.github.pulls.get_review_thread_comments.get_graphql_client") as mock_client_func:
        mock_client = MagicMock()
        mock_client.execute.side_effect = TransportError("Network error")
        mock_client_func.return_value = mock_client

        # Act
        result = get_review_thread_comments(**sample_params)

        # Assert - should return None due to handle_exceptions decorator
        assert result is None


def test_get_review_thread_comments_generic_exception(sample_params):
    """Test handling of generic exception."""
    # Arrange
    with patch("services.github.pulls.get_review_thread_comments.get_graphql_client") as mock_client_func:
        mock_client = MagicMock()
        mock_client.execute.side_effect = Exception("Unexpected error")
        mock_client_func.return_value = mock_client

        # Act
        result = get_review_thread_comments(**sample_params)

        # Assert - should return None due to handle_exceptions decorator
        assert result is None


def test_get_review_thread_comments_malformed_response(sample_params):
    """Test handling of malformed GraphQL response."""
    # Arrange
    mock_response = {
        "repository": {
            "pullRequest": {
                "reviewThreads": {
                    "nodes": [
                        {
                            "comments": {
                                "nodes": [
                                    {
                                        # Missing required 'id' field
                                        "author": {"login": "user1"},
                                        "body": "Comment without ID"
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }
    }
    
    with patch("services.github.pulls.get_review_thread_comments.get_graphql_client") as mock_client_func:
        mock_client = MagicMock()
        mock_client.execute.return_value = mock_response
        mock_client_func.return_value = mock_client

        # Act
        result = get_review_thread_comments(**sample_params)

        # Assert - should return None due to handle_exceptions decorator catching KeyError
        assert result is None


def test_get_review_thread_comments_multiple_threads_with_target(mock_graphql_client, sample_params):
    """Test when target comment is in the second thread."""
    # Arrange
    mock_response = {
        "repository": {
            "pullRequest": {
                "reviewThreads": {
                    "nodes": [
                        {
                            "comments": {
                                "nodes": [
                                    {
                                        "id": "comment_111",
                                        "author": {"login": "user1"},
                                        "body": "First thread comment",
                                        "createdAt": "2023-01-01T00:00:00Z"
                                    }
                                ]
                            }
                        },
                        {
                            "comments": {
                                "nodes": [
                                    {
                                        "id": "target_comment_456",
                                        "author": {"login": "user2"},
                                        "body": "Target comment in second thread",
                                        "createdAt": "2023-01-02T00:00:00Z"
                                    },
                                    {
                                        "id": "comment_333",
                                        "author": {"login": "user3"},
                                        "body": "Another comment in same thread",
                                        "createdAt": "2023-01-03T00:00:00Z"
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }
    }
    mock_graphql_client.execute.return_value = mock_response

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert - should return comments from the second thread
    expected_comments = [
        {
            "id": "target_comment_456",
            "author": {"login": "user2"},
            "body": "Target comment in second thread",
            "createdAt": "2023-01-02T00:00:00Z"
        },
        {
            "id": "comment_333",
            "author": {"login": "user3"},
            "body": "Another comment in same thread",
            "createdAt": "2023-01-03T00:00:00Z"
        }
    ]
    assert result == expected_comments


def test_get_review_thread_comments_calls_graphql_with_correct_parameters(
    mock_graphql_client, sample_params
):
    """Test that function calls GraphQL client with correct query and variables."""
    # Arrange
    mock_graphql_client.execute.return_value = {
        "repository": {
            "pullRequest": {
                "reviewThreads": {"nodes": []}
            }
        }
    }

    # Act
    get_review_thread_comments(**sample_params)

    # Assert
    call_args = mock_graphql_client.execute.call_args
    query_arg = call_args[1]["document"]
    variables_arg = call_args[1]["variable_values"]

    # Verify the query structure (checking if it's a gql DocumentNode)
    assert str(type(query_arg).__name__) == "DocumentNode"
    
    # Check that the query contains expected fields
    query_str = str(query_arg)
    assert "GetReviewThreadComments" in query_str
    assert "reviewThreads" in query_str
    assert "comments" in query_str

    # Verify the variables
    expected_variables = {
        "owner": "test-owner",
        "repo": "test-repo", 
        "pull_number": 123
    }
    assert variables_arg == expected_variables


def test_get_review_thread_comments_creates_graphql_client_with_token(sample_params):
    """Test that function creates GraphQL client with the provided token."""
    # Arrange
    with patch("services.github.pulls.get_review_thread_comments.get_graphql_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.execute.return_value = {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {"nodes": []}
                }
            }
        }

        # Act
        get_review_thread_comments(**sample_params)

        # Assert
        mock_get_client.assert_called_once_with(token="test-token")


def test_get_review_thread_comments_with_null_repository(mock_graphql_client, sample_params):
    """Test when repository is null in response."""
    # Arrange
    mock_response = {"repository": None}
    mock_graphql_client.execute.return_value = mock_response

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    assert result == []


def test_get_review_thread_comments_with_null_pull_request(mock_graphql_client, sample_params):
    """Test when pull request is null in response."""
    # Arrange
    mock_response = {
        "repository": {
            "pullRequest": None
        }
    }
    mock_graphql_client.execute.return_value = mock_response

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    assert result == []


def test_get_review_thread_comments_with_null_review_threads(mock_graphql_client, sample_params):
    """Test when reviewThreads is null in response."""
    # Arrange
    mock_response = {
        "repository": {
            "pullRequest": {
                "reviewThreads": None
            }
        }
    }
    mock_graphql_client.execute.return_value = mock_response

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    assert result == []


def test_get_review_thread_comments_with_null_comments(mock_graphql_client, sample_params):
    """Test when comments is null in a thread."""
    # Arrange
    mock_response = {
        "repository": {
            "pullRequest": {
                "reviewThreads": {
                    "nodes": [
                        {
                            "comments": None
                        }
                    ]
                }
            }
        }
    }
    mock_graphql_client.execute.return_value = mock_response

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    assert result == []


def test_get_review_thread_comments_single_comment_thread(mock_graphql_client, sample_params):
    """Test when target comment is the only comment in its thread."""
    # Arrange
    mock_response = {
        "repository": {
            "pullRequest": {
                "reviewThreads": {
                    "nodes": [
                        {
                            "comments": {
                                "nodes": [
                                    {
                                        "id": "target_comment_456",
                                        "author": {"login": "user1"},
                                        "body": "Single comment in thread",
                                        "createdAt": "2023-01-01T00:00:00Z"
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }
    }
    mock_graphql_client.execute.return_value = mock_response

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    expected_comments = [
        {
            "id": "target_comment_456",
            "author": {"login": "user1"},
            "body": "Single comment in thread",
            "createdAt": "2023-01-01T00:00:00Z"
        }
    ]
    assert result == expected_comments