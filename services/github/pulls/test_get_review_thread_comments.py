# Standard imports
from unittest.mock import MagicMock, patch

# Third party imports
import pytest
from gql.transport.exceptions import TransportError

# Local imports
from services.github.pulls.get_review_thread_comments import get_review_thread_comments


def test_get_review_thread_comments_success_comment_found():
    """Test successful retrieval when comment is found in a thread."""
    # Mock GraphQL response data
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

    with patch("services.github.pulls.get_review_thread_comments.get_graphql_client") as mock_client_func:
        # Setup mock client
        mock_client = MagicMock()
        mock_client.execute.return_value = mock_response
        mock_client_func.return_value = mock_client

        # Call function
        result = get_review_thread_comments(
            owner="test-owner",
            repo="test-repo", 
            pull_number=123,
            comment_node_id="target_comment_456",
            token="test_token"
        )

        # Verify GraphQL client was created with correct token
        mock_client_func.assert_called_once_with("test_token")
        
        # Verify GraphQL query was executed
        mock_client.execute.assert_called_once()
        call_args = mock_client.execute.call_args
        
        # Check that the query contains expected fields
        query_str = str(call_args[1]["document"])
        assert "GetReviewThreadComments" in query_str
        assert "reviewThreads" in query_str
        assert "comments" in query_str
        
        # Check variables
        variables = call_args[1]["variable_values"]
        assert variables["owner"] == "test-owner"
        assert variables["repo"] == "test-repo"
        assert variables["pull_number"] == 123

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


def test_get_review_thread_comments_comment_not_found():
    """Test when the target comment is not found in any thread."""
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

    with patch("services.github.pulls.get_review_thread_comments.get_graphql_client") as mock_client_func:
        mock_client = MagicMock()
        mock_client.execute.return_value = mock_response
        mock_client_func.return_value = mock_client

        # Call function with non-existent comment ID
        result = get_review_thread_comments(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            comment_node_id="non_existent_comment",
            token="test_token"
        )

        # Should return empty list when comment not found
        assert result == []


def test_get_review_thread_comments_empty_threads():
    """Test when there are no review threads."""
    mock_response = {
        "repository": {
            "pullRequest": {
                "reviewThreads": {
                    "nodes": []
                }
            }
        }
    }

    with patch("services.github.pulls.get_review_thread_comments.get_graphql_client") as mock_client_func:
        mock_client = MagicMock()
        mock_client.execute.return_value = mock_response
        mock_client_func.return_value = mock_client

        result = get_review_thread_comments(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            comment_node_id="any_comment",
            token="test_token"
        )

        assert result == []


def test_get_review_thread_comments_empty_comments_in_thread():
    """Test when threads exist but have no comments."""
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

    with patch("services.github.pulls.get_review_thread_comments.get_graphql_client") as mock_client_func:
        mock_client = MagicMock()
        mock_client.execute.return_value = mock_response
        mock_client_func.return_value = mock_client

        result = get_review_thread_comments(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            comment_node_id="any_comment",
            token="test_token"
        )

        assert result == []


def test_get_review_thread_comments_missing_repository():
    """Test when repository is not found in response."""
    mock_response = {}

    with patch("services.github.pulls.get_review_thread_comments.get_graphql_client") as mock_client_func:
        mock_client = MagicMock()
        mock_client.execute.return_value = mock_response
        mock_client_func.return_value = mock_client

        result = get_review_thread_comments(
            owner="non-existent-owner",
            repo="non-existent-repo",
            pull_number=123,
            comment_node_id="any_comment",
            token="test_token"
        )

        assert result == []


def test_get_review_thread_comments_missing_pull_request():
    """Test when pull request is not found in response."""
    mock_response = {
        "repository": {}
    }

    with patch("services.github.pulls.get_review_thread_comments.get_graphql_client") as mock_client_func:
        mock_client = MagicMock()
        mock_client.execute.return_value = mock_response
        mock_client_func.return_value = mock_client

        result = get_review_thread_comments(
            owner="test-owner",
            repo="test-repo",
            pull_number=999,
            comment_node_id="any_comment",
            token="test_token"
        )

        assert result == []


def test_get_review_thread_comments_transport_error():
    """Test handling of GraphQL transport error."""
    with patch("services.github.pulls.get_review_thread_comments.get_graphql_client") as mock_client_func:
        mock_client = MagicMock()
        mock_client.execute.side_effect = TransportError("Network error")
        mock_client_func.return_value = mock_client

        # Should return None due to handle_exceptions decorator
        result = get_review_thread_comments(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            comment_node_id="any_comment",
            token="test_token"
        )

        assert result is None


def test_get_review_thread_comments_generic_exception():
    """Test handling of generic exception."""
    with patch("services.github.pulls.get_review_thread_comments.get_graphql_client") as mock_client_func:
        mock_client = MagicMock()
        mock_client.execute.side_effect = Exception("Unexpected error")
        mock_client_func.return_value = mock_client

        # Should return None due to handle_exceptions decorator
        result = get_review_thread_comments(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            comment_node_id="any_comment",
            token="test_token"
        )

        assert result is None


def test_get_review_thread_comments_malformed_response():
    """Test handling of malformed GraphQL response."""
    mock_response = {
        "repository": {
            "pullRequest": {
                "reviewThreads": {
                    "nodes": [
                        {
                            "comments": {
                                "nodes": [
                                    {
                                        # Missing required fields
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

        # Should return None due to handle_exceptions decorator catching KeyError
        result = get_review_thread_comments(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            comment_node_id="any_comment",
            token="test_token"
        )

        assert result is None


def test_get_review_thread_comments_multiple_threads_with_target():
    """Test when target comment is in the second thread."""
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
                                        "id": "target_comment_222",
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

    with patch("services.github.pulls.get_review_thread_comments.get_graphql_client") as mock_client_func:
        mock_client = MagicMock()
        mock_client.execute.return_value = mock_response
        mock_client_func.return_value = mock_client

        result = get_review_thread_comments(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            comment_node_id="target_comment_222",
            token="test_token"
        )

        # Should return comments from the second thread
        expected_comments = [
            {
                "id": "target_comment_222",
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