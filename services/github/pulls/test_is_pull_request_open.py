from unittest.mock import patch, MagicMock

import pytest

from services.github.pulls.is_pull_request_open import is_pull_request_open


@pytest.fixture
def mock_graphql_client():
    """Fixture to provide a mocked GraphQL client."""
    with patch("services.github.pulls.is_pull_request_open.get_graphql_client") as mock:
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
        "token": "test-token",
    }


def test_is_pull_request_open_returns_true_when_pr_is_open(
    mock_graphql_client, sample_params
):
    """Test that function returns True when pull request state is OPEN."""
    # Arrange
    mock_graphql_client.execute.return_value = {
        "repository": {"pullRequest": {"state": "OPEN"}}
    }

    # Act
    result = is_pull_request_open(**sample_params)

    # Assert
    assert result is True
    mock_graphql_client.execute.assert_called_once()


def test_is_pull_request_open_returns_false_when_pr_is_closed(
    mock_graphql_client, sample_params
):
    """Test that function returns False when pull request state is CLOSED."""
    # Arrange
    mock_graphql_client.execute.return_value = {
        "repository": {"pullRequest": {"state": "CLOSED"}}
    }

    # Act
    result = is_pull_request_open(**sample_params)

    # Assert
    assert result is False
    mock_graphql_client.execute.assert_called_once()


def test_is_pull_request_open_returns_false_when_pr_is_merged(
    mock_graphql_client, sample_params
):
    """Test that function returns False when pull request state is MERGED."""
    # Arrange
    mock_graphql_client.execute.return_value = {
        "repository": {"pullRequest": {"state": "MERGED"}}
    }

    # Act
    result = is_pull_request_open(**sample_params)

    # Assert
    assert result is False
    mock_graphql_client.execute.assert_called_once()


def test_is_pull_request_open_returns_false_when_repository_not_found(
    mock_graphql_client, sample_params
):
    """Test that function returns False when repository is not found."""
    # Arrange
    mock_graphql_client.execute.return_value = {"repository": None}

    # Act
    result = is_pull_request_open(**sample_params)

    # Assert
    assert result is False  # Repository not found means PR doesn't exist
    mock_graphql_client.execute.assert_called_once()


def test_is_pull_request_open_returns_false_when_pull_request_not_found(
    mock_graphql_client, sample_params
):
    """Test that function returns False when pull request is not found."""
    # Arrange
    mock_graphql_client.execute.return_value = {"repository": {"pullRequest": None}}

    # Act
    result = is_pull_request_open(**sample_params)

    # Assert
    assert result is False  # PR not found means it doesn't exist
    mock_graphql_client.execute.assert_called_once()


def test_is_pull_request_open_returns_false_when_empty_response(
    mock_graphql_client, sample_params
):
    """Test that function returns False when response is empty."""
    # Arrange
    mock_graphql_client.execute.return_value = {}

    # Act
    result = is_pull_request_open(**sample_params)

    # Assert
    assert result is False
    mock_graphql_client.execute.assert_called_once()


def test_is_pull_request_open_calls_graphql_with_correct_parameters(
    mock_graphql_client, sample_params
):
    """Test that function calls GraphQL client with correct query and variables."""
    # Arrange
    mock_graphql_client.execute.return_value = {
        "repository": {"pullRequest": {"state": "OPEN"}}
    }

    # Act
    is_pull_request_open(**sample_params)

    # Assert
    call_args = mock_graphql_client.execute.call_args
    query_arg = call_args[0][0]
    variables_arg = call_args[1]["variable_values"]

    # Verify the query structure (checking if it's a gql object with the right content)
    assert str(type(query_arg).__name__) == "DocumentNode"

    # Verify the variables
    expected_variables = {"owner": "test-owner", "repo": "test-repo", "pullNumber": 123}
    assert variables_arg == expected_variables


def test_is_pull_request_open_creates_graphql_client_with_token(sample_params):
    """Test that function creates GraphQL client with the provided token."""
    with patch(
        "services.github.pulls.is_pull_request_open.get_graphql_client"
    ) as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.execute.return_value = {
            "repository": {"pullRequest": {"state": "OPEN"}}
        }

        # Act
        is_pull_request_open(**sample_params)

        # Assert
        mock_get_client.assert_called_once_with(token="test-token")


def test_is_pull_request_open_handles_exception_returns_true(sample_params):
    """Test that function returns True when an exception occurs (fail-open due to @handle_exceptions decorator)."""
    with patch(
        "services.github.pulls.is_pull_request_open.get_graphql_client"
    ) as mock_get_client:
        mock_get_client.side_effect = Exception("GraphQL error")

        # Act
        result = is_pull_request_open(**sample_params)

        # Assert
        assert result is True  # Network errors return True (fail-open)
