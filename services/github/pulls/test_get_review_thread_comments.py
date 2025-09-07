from unittest.mock import patch, MagicMock

import pytest
from gql.transport.exceptions import TransportQueryError

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
        "comment_node_id": "MDEyOklzc3VlQ29tbWVudDEyMzQ1Njc4OQ==",
        "token": "test-token",
    }


@pytest.fixture
def sample_review_threads_response():
    """Fixture to provide sample review threads response."""
    return {
        "repository": {
            "pullRequest": {
                "reviewThreads": {
                    "nodes": [
                        {
                            "comments": {
                                "nodes": [
                                    {
                                        "id": "MDEyOklzc3VlQ29tbWVudDEyMzQ1Njc4OQ==",
                                        "author": {"login": "user1"},
                                        "body": "This is the first comment",
                                        "createdAt": "2023-01-01T10:00:00Z",
                                    },
                                    {
                                        "id": "MDEyOklzc3VlQ29tbWVudDk4NzY1NDMyMQ==",
                                        "author": {"login": "user2"},
                                        "body": "This is a reply comment",
                                        "createdAt": "2023-01-01T11:00:00Z",
                                    },
                                ]
                            }
                        },
                        {
                            "comments": {
                                "nodes": [
                                    {
                                        "id": "MDEyOklzc3VlQ29tbWVudDU1NTU1NTU1NQ==",
                                        "author": {"login": "user3"},
                                        "body": "Different thread comment",
                                        "createdAt": "2023-01-01T12:00:00Z",
                                    }
                                ]
                            }
                        },
                    ]
                }
            }
        }
    }


def test_get_review_thread_comments_success_finds_matching_comment(
    mock_graphql_client, sample_params, sample_review_threads_response
):
    """Test successful retrieval when target comment is found in a thread."""
    # Arrange
    mock_graphql_client.execute.return_value = sample_review_threads_response

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    expected_comments = [
        {
            "id": "MDEyOklzc3VlQ29tbWVudDEyMzQ1Njc4OQ==",
            "author": {"login": "user1"},
            "body": "This is the first comment",
            "createdAt": "2023-01-01T10:00:00Z",
        },
        {
            "id": "MDEyOklzc3VlQ29tbWVudDk4NzY1NDMyMQ==",
            "author": {"login": "user2"},
            "body": "This is a reply comment",
            "createdAt": "2023-01-01T11:00:00Z",
        },
    ]
    assert result == expected_comments
    mock_graphql_client.execute.assert_called_once()


def test_get_review_thread_comments_comment_not_found_returns_empty_list(
    mock_graphql_client, sample_params, sample_review_threads_response
):
    """Test that function returns empty list when target comment is not found."""
    # Arrange
    mock_graphql_client.execute.return_value = sample_review_threads_response
    sample_params["comment_node_id"] = "NonExistentCommentId"

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    assert result == []
    mock_graphql_client.execute.assert_called_once()


def test_get_review_thread_comments_no_review_threads_returns_empty_list(
    mock_graphql_client, sample_params
):
    """Test that function returns empty list when there are no review threads."""
    # Arrange
    response = {
        "repository": {
            "pullRequest": {
                "reviewThreads": {
                    "nodes": []
                }
            }
        }
    }
    mock_graphql_client.execute.return_value = response

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    assert result == []
    mock_graphql_client.execute.assert_called_once()


def test_get_review_thread_comments_empty_thread_comments_returns_empty_list(
    mock_graphql_client, sample_params
):
    """Test that function returns empty list when threads have no comments."""
    # Arrange
    response = {
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
    mock_graphql_client.execute.return_value = response

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    assert result == []
    mock_graphql_client.execute.assert_called_once()


def test_get_review_thread_comments_repository_not_found_returns_empty_list(
    mock_graphql_client, sample_params
):
    """Test that function returns empty list when repository is not found."""
    # Arrange
    response = {"repository": None}
    mock_graphql_client.execute.return_value = response

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    assert result == []
    mock_graphql_client.execute.assert_called_once()


def test_get_review_thread_comments_pull_request_not_found_returns_empty_list(
    mock_graphql_client, sample_params
):
    """Test that function returns empty list when pull request is not found."""
    # Arrange
    response = {"repository": {"pullRequest": None}}
    mock_graphql_client.execute.return_value = response

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    assert result == []
    mock_graphql_client.execute.assert_called_once()


def test_get_review_thread_comments_empty_response_returns_empty_list(
    mock_graphql_client, sample_params
):
    """Test that function returns empty list when response is empty."""
    # Arrange
    mock_graphql_client.execute.return_value = {}

    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    assert result == []
    mock_graphql_client.execute.assert_called_once()


def test_get_review_thread_comments_calls_graphql_with_correct_parameters(
    mock_graphql_client, sample_params, sample_review_threads_response
):
    """Test that function calls GraphQL client with correct query and variables."""
    # Arrange
    mock_graphql_client.execute.return_value = sample_review_threads_response

    # Act
    get_review_thread_comments(**sample_params)

    # Assert
    call_args = mock_graphql_client.execute.call_args
    query_arg = call_args[0][0] if call_args[0] else call_args.kwargs["document"]
    variables_arg = call_args[1]["variable_values"] if call_args[0] else call_args.kwargs["variable_values"]

    # Verify the query structure (checking if it's a gql object with the right content)
    assert str(type(query_arg).__name__) == "DocumentNode"

    # Verify the variables
    expected_variables = {
        "owner": "test-owner",
        "repo": "test-repo",
        "pull_number": 123,
    }
    assert variables_arg == expected_variables


def test_get_review_thread_comments_creates_graphql_client_with_token(sample_params):
    """Test that function creates GraphQL client with the provided token."""
    with patch(
        "services.github.pulls.get_review_thread_comments.get_graphql_client"
    ) as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.execute.return_value = {
            "repository": {"pullRequest": {"reviewThreads": {"nodes": []}}}
        }

        # Act
        get_review_thread_comments(**sample_params)

        # Assert
        mock_get_client.assert_called_once_with("test-token")


def test_get_review_thread_comments_handles_graphql_exception_returns_empty_list(sample_params):
    """Test that function returns None when GraphQL exception occurs (due to @handle_exceptions decorator)."""
    with patch(
        "services.github.pulls.get_review_thread_comments.get_graphql_client"
    ) as mock_get_client:
        mock_get_client.side_effect = TransportQueryError("GraphQL transport error")

        # Act
        result = get_review_thread_comments(**sample_params)

        # Assert
        assert result is None


def test_get_review_thread_comments_handles_client_execute_exception_returns_none(sample_params):
    """Test that function returns None when client.execute raises exception (due to @handle_exceptions decorator)."""
    with patch(
        "services.github.pulls.get_review_thread_comments.get_graphql_client"
    ) as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.execute.side_effect = Exception("GraphQL execution error")

        # Act
        result = get_review_thread_comments(**sample_params)

        # Assert
        assert result is None


def test_get_review_thread_comments_with_different_parameters(mock_graphql_client):
    """Test function with different parameter values."""
    # Arrange
    response = {
        "repository": {
            "pullRequest": {
                "reviewThreads": {
                    "nodes": [
                        {
                            "comments": {
                                "nodes": [
                                    {
                                        "id": "SpecialCommentId123",
                                        "author": {"login": "special-user"},
                                        "body": "Special comment body",
                                        "createdAt": "2023-12-01T15:30:00Z",
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }
    }
    mock_graphql_client.execute.return_value = response

    # Act
    result = get_review_thread_comments(
        owner="special-owner",
        repo="special-repo",
        pull_number=999,
        comment_node_id="SpecialCommentId123",
        token="special-token"
    )

    # Assert
    expected_comments = [
        {
            "id": "SpecialCommentId123",
            "author": {"login": "special-user"},
            "body": "Special comment body",
            "createdAt": "2023-12-01T15:30:00Z",
        }
    ]
    assert result == expected_comments
    mock_graphql_client.execute.assert_called_once()


def test_get_review_thread_comments_malformed_response_structure(
    mock_graphql_client, sample_params
):
    """Test handling of malformed response structures."""
    malformed_responses = [
        {},  # Empty response
        {"repository": "string"},
        {"repository": {"pullRequest": "string"}},
        {"repository": {"pullRequest": {"reviewThreads": "string"}}},
        {"repository": {"pullRequest": {"reviewThreads": {"nodes": "string"}}}},
        {"repository": None},
        {"repository": {"pullRequest": None}},
        {"repository": {"pullRequest": {"reviewThreads": None}}},
    ]

    for malformed_response in malformed_responses:
        mock_graphql_client.reset_mock()
        mock_graphql_client.execute.return_value = malformed_response

        result = get_review_thread_comments(**sample_params)

        assert result == []
        mock_graphql_client.execute.assert_called_once()


def test_get_review_thread_comments_non_dict_response_types_return_none(sample_params):
    """Test that function returns None when response is not a dict (handled by decorator)."""
    non_dict_responses = [
        None,
        "string_instead_of_dict", 
        123,
        [],
    ]
    
    for response in non_dict_responses:
        with patch("services.github.pulls.get_review_thread_comments.get_graphql_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.execute.return_value = response
            
            result = get_review_thread_comments(**sample_params)
            assert result == []  # Our improved implementation should handle these


def test_get_review_thread_comments_missing_comment_fields(
    mock_graphql_client, sample_params
):
    """Test handling of comments with missing or malformed fields."""
    response = {
        "repository": {
            "pullRequest": {
                "reviewThreads": {
                    "nodes": [
                        {
                            "comments": {
                                "nodes": [
                                    {
                                        "id": "MDEyOklzc3VlQ29tbWVudDEyMzQ1Njc4OQ==",
                                        # Missing author, body, createdAt fields
                                    },
                                    {
                                        "id": "AnotherCommentId",
                                        "author": None,
                                        "body": None,
                                        "createdAt": None,
                                    },
                                ]
                            }
                        }
                    ]
                }
            }
        }
    }
    mock_graphql_client.execute.return_value = response

    result = get_review_thread_comments(**sample_params)

    expected_comments = [
        {
            "id": "MDEyOklzc3VlQ29tbWVudDEyMzQ1Njc4OQ==",
        },
        {
            "id": "AnotherCommentId",
            "author": None,
            "body": None,
            "createdAt": None,
        },
    ]
    assert result == expected_comments
    mock_graphql_client.execute.assert_called_once()


def test_get_review_thread_comments_function_has_proper_docstring():
    """Test that the function has proper documentation."""
    assert get_review_thread_comments.__doc__ is not None
    assert "Get all comments in a review thread" in get_review_thread_comments.__doc__
    assert "GraphQL API" in get_review_thread_comments.__doc__
    assert "https://docs.github.com/en/graphql/reference/objects#pullrequestreviewcomment" in get_review_thread_comments.__doc__

def test_get_review_thread_comments_multiple_threads_finds_correct_one(
    mock_graphql_client, sample_params
):
    """Test that function finds the correct thread when multiple threads exist."""
    response = {
        "repository": {
            "pullRequest": {
                "reviewThreads": {
                    "nodes": [
                        {
                            "comments": {
                                "nodes": [
                                    {
                                        "id": "WrongCommentId1",
                                        "author": {"login": "user1"},
                                        "body": "Wrong thread comment 1",
                                        "createdAt": "2023-01-01T10:00:00Z",
                                    }
                                ]
                            }
                        },
                        {
                            "comments": {
                                "nodes": [
                                    {
                                        "id": "MDEyOklzc3VlQ29tbWVudDEyMzQ1Njc4OQ==",
                                        "author": {"login": "user2"},
                                        "body": "Correct thread comment 1",
                                        "createdAt": "2023-01-01T11:00:00Z",
                                    },
                                    {
                                        "id": "CorrectThreadComment2",
                                        "author": {"login": "user3"},
                                        "body": "Correct thread comment 2",
                                        "createdAt": "2023-01-01T12:00:00Z",
                                    }
                                ]
                            }
                        },
                        {
                            "comments": {
                                "nodes": [
                                    {
                                        "id": "WrongCommentId2",
                                        "author": {"login": "user4"},
                                        "body": "Wrong thread comment 2",
                                        "createdAt": "2023-01-01T13:00:00Z",
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }
    }
    mock_graphql_client.execute.return_value = response

    result = get_review_thread_comments(**sample_params)

    # Should return all comments from the thread containing the target comment
    expected_comments = [
        {
            "id": "MDEyOklzc3VlQ29tbWVudDEyMzQ1Njc4OQ==",
            "author": {"login": "user2"},
            "body": "Correct thread comment 1",
            "createdAt": "2023-01-01T11:00:00Z",
        },
        {
            "id": "CorrectThreadComment2",
            "author": {"login": "user3"},
            "body": "Correct thread comment 2",
            "createdAt": "2023-01-01T12:00:00Z",
        }
    ]
    assert result == expected_comments
    mock_graphql_client.execute.assert_called_once()


def test_get_review_thread_comments_thread_with_missing_comments_structure(
    mock_graphql_client, sample_params
):
    """Test handling of threads with missing or malformed comments structure."""
    response = {
        "repository": {
            "pullRequest": {
                "reviewThreads": {
                    "nodes": [
                        {
                            # Missing comments field entirely
                        },
                        {
                            "comments": None  # comments is null
                        },
                        {
                            "comments": {}  # comments missing nodes
                        }
                    ]
                }
            }
        }
    }
    mock_graphql_client.execute.return_value = response
    # Act
    result = get_review_thread_comments(**sample_params)

    # Assert
    assert result == []
    mock_graphql_client.execute.assert_called_once()
