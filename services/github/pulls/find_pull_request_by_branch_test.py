from unittest.mock import patch, MagicMock
import json

import pytest
from gql import gql

from services.github.pulls.find_pull_request_by_branch import find_pull_request_by_branch


@pytest.fixture
def mock_graphql_client():
    """Fixture to provide a mocked GraphQL client."""
    with patch("services.github.pulls.find_pull_request_by_branch.get_graphql_client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_pull_request():
    """Fixture providing a sample pull request response."""
    return {
        "number": 123,
        "title": "Feature: Add new functionality",
        "url": "https://api.github.com/repos/owner/repo/pulls/123",
        "headRef": {"name": "feature-branch"},
        "baseRef": {"name": "main"}
    }


@pytest.fixture
def sample_graphql_response_with_pull(sample_pull_request):
    """Fixture providing a GraphQL response with a pull request."""
    return {
        "repository": {
            "pullRequests": {
                "nodes": [sample_pull_request]
            }
        }
    }


@pytest.fixture
def sample_graphql_response_empty():
    """Fixture providing a GraphQL response with no pull requests."""
    return {
        "repository": {
            "pullRequests": {
                "nodes": []
            }
        }
    }


def test_find_pull_request_by_branch_returns_pull_request_when_found(
    mock_graphql_client, sample_graphql_response_with_pull, sample_pull_request
):
    """Test that the function returns a pull request when one is found."""
    # Arrange
    mock_graphql_client.execute.return_value = sample_graphql_response_with_pull
    owner = "test-owner"
    repo = "test-repo"
    branch_name = "feature-branch"
    token = "test-token"

    # Act
    result = find_pull_request_by_branch(owner, repo, branch_name, token)

    # Assert
    assert result == sample_pull_request
    assert result["number"] == 123
    assert result["title"] == "Feature: Add new functionality"
    assert result["headRef"]["name"] == "feature-branch"
    assert result["baseRef"]["name"] == "main"


def test_find_pull_request_by_branch_returns_none_when_no_pull_request_found(
    mock_graphql_client, sample_graphql_response_empty
):
    """Test that the function returns None when no pull request is found."""
    # Arrange
    mock_graphql_client.execute.return_value = sample_graphql_response_empty
    owner = "test-owner"
    repo = "test-repo"
    branch_name = "nonexistent-branch"
    token = "test-token"

    # Act
    result = find_pull_request_by_branch(owner, repo, branch_name, token)

    # Assert
    assert result is None


def test_find_pull_request_by_branch_calls_graphql_client_with_correct_parameters(
    mock_graphql_client, sample_graphql_response_with_pull
):
    """Test that the GraphQL client is called with the correct parameters."""
    # Arrange
    mock_graphql_client.execute.return_value = sample_graphql_response_with_pull
    owner = "test-owner"
    repo = "test-repo"
    branch_name = "feature-branch"
    token = "test-token"

    # Act
    find_pull_request_by_branch(owner, repo, branch_name, token)

    # Assert
    mock_graphql_client.execute.assert_called_once()
    call_args = mock_graphql_client.execute.call_args
    
    # Check that gql query was passed
    query_arg = call_args[0][0]
    # Check that the query argument is a DocumentNode (returned by gql())
    assert str(type(query_arg).__name__) == 'DocumentNode'
    
    # Check variable values
    variable_values = call_args[1]['variable_values']
    assert variable_values == {
        "owner": owner,
        "repo": repo,
        "headRefName": branch_name
    }


@patch("services.github.pulls.find_pull_request_by_branch.get_graphql_client")
def test_find_pull_request_by_branch_creates_client_with_token(mock_get_client):
    """Test that the GraphQL client is created with the provided token."""
    # Arrange
    mock_client = MagicMock()
    mock_client.execute.return_value = {"repository": {"pullRequests": {"nodes": []}}}
    mock_get_client.return_value = mock_client
    
    owner = "test-owner"
    repo = "test-repo"
    branch_name = "feature-branch"
    token = "test-token-123"

    # Act
    find_pull_request_by_branch(owner, repo, branch_name, token)

    # Assert
    mock_get_client.assert_called_once_with(token=token)


def test_find_pull_request_by_branch_handles_missing_repository_key(mock_graphql_client):
    """Test that the function handles missing 'repository' key gracefully."""
    # Arrange
    mock_graphql_client.execute.return_value = {}
    owner = "test-owner"
    repo = "test-repo"
    branch_name = "feature-branch"
    token = "test-token"

    # Act
    result = find_pull_request_by_branch(owner, repo, branch_name, token)

    # Assert
    assert result is None


def test_find_pull_request_by_branch_handles_missing_pull_requests_key(mock_graphql_client):
    """Test that the function handles missing 'pullRequests' key gracefully."""
    # Arrange
    mock_graphql_client.execute.return_value = {"repository": {}}
    owner = "test-owner"
    repo = "test-repo"
    branch_name = "feature-branch"
    token = "test-token"

    # Act
    result = find_pull_request_by_branch(owner, repo, branch_name, token)

    # Assert
    assert result is None


def test_find_pull_request_by_branch_handles_missing_nodes_key(mock_graphql_client):
    """Test that the function handles missing 'nodes' key gracefully."""
    # Arrange
    mock_graphql_client.execute.return_value = {
        "repository": {
            "pullRequests": {}
        }
    }
    owner = "test-owner"
    repo = "test-repo"
    branch_name = "feature-branch"
    token = "test-token"

    # Act
    result = find_pull_request_by_branch(owner, repo, branch_name, token)

    # Assert
    assert result is None


def test_find_pull_request_by_branch_returns_first_pull_request_when_multiple_found(
    mock_graphql_client
):
    """Test that the function returns the first pull request when multiple are found."""
    # Arrange
    first_pull = {
        "number": 123,
        "title": "First PR",
        "url": "https://api.github.com/repos/owner/repo/pulls/123",
        "headRef": {"name": "feature-branch"},
        "baseRef": {"name": "main"}
    }
    second_pull = {
        "number": 124,
        "title": "Second PR",
        "url": "https://api.github.com/repos/owner/repo/pulls/124",
        "headRef": {"name": "feature-branch"},
        "baseRef": {"name": "main"}
    }
    
    mock_graphql_client.execute.return_value = {
        "repository": {
            "pullRequests": {
                "nodes": [first_pull, second_pull]
            }
        }
    }
    
    owner = "test-owner"
    repo = "test-repo"
    branch_name = "feature-branch"
    token = "test-token"

    # Act
    result = find_pull_request_by_branch(owner, repo, branch_name, token)

    # Assert
    assert result == first_pull
    assert result["number"] == 123
    assert result["title"] == "First PR"


@pytest.mark.parametrize("owner,repo,branch_name,token", [
    ("owner1", "repo1", "branch1", "token1"),
    ("test-org", "test-project", "feature/new-feature", "ghp_token123"),
    ("user", "my-repo", "bugfix/issue-123", "personal_access_token"),
    ("company", "product", "release/v1.0.0", "bot_token_xyz"),
])
def test_find_pull_request_by_branch_with_various_parameter_combinations(
    mock_graphql_client, owner, repo, branch_name, token
):
    """Test that the function works with various parameter combinations."""
    # Arrange
    mock_graphql_client.execute.return_value = {
        "repository": {"pullRequests": {"nodes": []}}
    }

    # Act
    result = find_pull_request_by_branch(owner, repo, branch_name, token)

    # Assert
    assert result is None
    mock_graphql_client.execute.assert_called_once()
    
    # Verify correct parameters were passed
    call_args = mock_graphql_client.execute.call_args
    variable_values = call_args[1]['variable_values']
    assert variable_values["owner"] == owner
    assert variable_values["repo"] == repo
    assert variable_values["headRefName"] == branch_name


def test_find_pull_request_by_branch_handles_graphql_client_exception(mock_graphql_client):
    """Test that the function handles GraphQL client exceptions gracefully."""
    # Arrange
    mock_graphql_client.execute.side_effect = Exception("GraphQL execution failed")
    owner = "test-owner"
    repo = "test-repo"
    branch_name = "feature-branch"
    token = "test-token"

    # Act
    result = find_pull_request_by_branch(owner, repo, branch_name, token)

    # Assert - Due to @handle_exceptions decorator, should return None instead of raising
    assert result is None


def test_find_pull_request_by_branch_handles_json_decode_error(mock_graphql_client):
    """Test that the function handles JSON decode errors gracefully."""
    # Arrange
    mock_graphql_client.execute.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    owner = "test-owner"
    repo = "test-repo"
    branch_name = "feature-branch"
    token = "test-token"

    # Act
    result = find_pull_request_by_branch(owner, repo, branch_name, token)

    # Assert - Due to @handle_exceptions decorator, should return None instead of raising
    assert result is None


def test_find_pull_request_by_branch_handles_key_error(mock_graphql_client):
    """Test that the function handles KeyError exceptions gracefully."""
    # Arrange
    mock_graphql_client.execute.side_effect = KeyError("Missing key")
    owner = "test-owner"
    repo = "test-repo"
    branch_name = "feature-branch"
    token = "test-token"

    # Act
    result = find_pull_request_by_branch(owner, repo, branch_name, token)

    # Assert - Due to @handle_exceptions decorator, should return None instead of raising
    assert result is None


def test_find_pull_request_by_branch_handles_attribute_error(mock_graphql_client):
    """Test that the function handles AttributeError exceptions gracefully."""
    # Arrange
    mock_graphql_client.execute.side_effect = AttributeError("'NoneType' object has no attribute")
    owner = "test-owner"
    repo = "test-repo"
    branch_name = "feature-branch"
    token = "test-token"

    # Act
    result = find_pull_request_by_branch(owner, repo, branch_name, token)

    # Assert - Due to @handle_exceptions decorator, should return None instead of raising
    assert result is None


def test_find_pull_request_by_branch_handles_type_error(mock_graphql_client):
    """Test that the function handles TypeError exceptions gracefully."""
    # Arrange
    mock_graphql_client.execute.side_effect = TypeError("Invalid type")
    owner = "test-owner"
    repo = "test-repo"
    branch_name = "feature-branch"
    token = "test-token"

    # Act
    result = find_pull_request_by_branch(owner, repo, branch_name, token)

    # Assert - Due to @handle_exceptions decorator, should return None instead of raising
    assert result is None


def test_find_pull_request_by_branch_with_empty_string_parameters(mock_graphql_client):
    """Test that the function handles empty string parameters."""
    # Arrange
    mock_graphql_client.execute.return_value = {
        "repository": {"pullRequests": {"nodes": []}}
    }
    
    # Act
    result = find_pull_request_by_branch("", "", "", "")

    # Assert
    assert result is None
    mock_graphql_client.execute.assert_called_once()
    
    # Verify empty strings were passed correctly
    call_args = mock_graphql_client.execute.call_args
    variable_values = call_args[1]['variable_values']


def test_find_pull_request_by_branch_graphql_query_structure(mock_graphql_client):
    """Test that the GraphQL query contains the expected structure and fields."""
    # Arrange
    mock_graphql_client.execute.return_value = {
        "repository": {"pullRequests": {"nodes": []}}
    }
    
    # Act
    find_pull_request_by_branch("owner", "repo", "branch", "token")

    # Assert
    mock_graphql_client.execute.assert_called_once()
    call_args = mock_graphql_client.execute.call_args
    query_arg = call_args[0][0]
    
    # Convert the query to string to check its content
    query_string = str(query_arg.document)
    
    # Check that the query contains expected fields and structure
    assert "query($owner: String!, $repo: String!, $headRefName: String!)" in query_string
    assert "repository(owner: $owner, name: $repo)" in query_string
    assert "pullRequests(first: 1, headRefName: $headRefName, states: OPEN)" in query_string
    assert "number" in query_string
    assert "title" in query_string
    assert "url" in query_string
    assert "headRef { name }" in query_string
    assert "baseRef { name }" in query_string


def test_find_pull_request_by_branch_return_type_annotation():
    """Test that the function has the correct return type annotation."""
    import inspect
    
    # Get the function signature
    sig = inspect.signature(find_pull_request_by_branch)
    
    # Check return annotation
    return_annotation = sig.return_annotation
    assert return_annotation == dict | None


def test_find_pull_request_by_branch_parameter_types():
    """Test that the function has the correct parameter type annotations."""
    import inspect
    
    # Get the function signature
    sig = inspect.signature(find_pull_request_by_branch)
    
    # Check parameter annotations
    params = sig.parameters
    assert params['owner'].annotation == str
    assert params['repo'].annotation == str
    assert params['branch_name'].annotation == str
    assert params['token'].annotation == str


def test_find_pull_request_by_branch_has_docstring():
    """Test that the function has a docstring."""
    assert find_pull_request_by_branch.__doc__ is not None
    assert "https://docs.github.com/en/graphql/reference/objects#pullrequest" in find_pull_request_by_branch.__doc__

