# Standard imports
from unittest.mock import patch, MagicMock

# Third party imports
import pytest
from botocore.exceptions import ClientError, BotoCoreError

# Local imports
from services.aws.create_log_group import create_log_group


@pytest.fixture
def mock_logs_client():
    """Fixture to mock the logs_client."""
    with patch("services.aws.create_log_group.logs_client") as mock:
        yield mock


def test_create_log_group_success(mock_logs_client):
    """Test successful log group creation."""
    # Setup
    owner_name = "testowner"
    repo_name = "testrepo"
    expected_log_group_name = "/aws/lambda/gitauto/testowner/testrepo"
    mock_logs_client.create_log_group.return_value = None

    # Execute
    result = create_log_group(owner_name, repo_name)

    # Assert
    assert result is None
    mock_logs_client.create_log_group.assert_called_once_with(
        logGroupName=expected_log_group_name
    )


def test_create_log_group_already_exists(mock_logs_client):
    """Test log group creation when log group already exists."""
    # Setup
    owner_name = "testowner"
    repo_name = "testrepo"
    expected_log_group_name = "/aws/lambda/gitauto/testowner/testrepo"
    
    # Mock ResourceAlreadyExistsException
    mock_exception = MagicMock()
    mock_logs_client.exceptions.ResourceAlreadyExistsException = mock_exception
    mock_logs_client.create_log_group.side_effect = mock_exception

    # Execute
    result = create_log_group(owner_name, repo_name)

    # Assert
    assert result is None
    mock_logs_client.create_log_group.assert_called_once_with(
        logGroupName=expected_log_group_name
    )


def test_create_log_group_with_special_characters(mock_logs_client):
    """Test log group creation with special characters in names."""
    # Setup
    owner_name = "test-owner_123"
    repo_name = "test.repo-name"
    expected_log_group_name = "/aws/lambda/gitauto/test-owner_123/test.repo-name"
    mock_logs_client.create_log_group.return_value = None

    # Execute
    result = create_log_group(owner_name, repo_name)

    # Assert
    assert result is None
    mock_logs_client.create_log_group.assert_called_once_with(
        logGroupName=expected_log_group_name
    )


def test_create_log_group_client_error(mock_logs_client):
    """Test log group creation when ClientError occurs."""
    # Setup
    owner_name = "testowner"
    repo_name = "testrepo"
    error_response = {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}
    mock_logs_client.create_log_group.side_effect = ClientError(
        error_response, "CreateLogGroup"
    )

    # Execute
    result = create_log_group(owner_name, repo_name)

    # Assert - should return None due to handle_exceptions decorator
    assert result is None
    mock_logs_client.create_log_group.assert_called_once()


def test_create_log_group_botocore_error(mock_logs_client):
    """Test log group creation when BotoCoreError occurs."""
    # Setup
    owner_name = "testowner"
    repo_name = "testrepo"
    mock_logs_client.create_log_group.side_effect = BotoCoreError()

    # Execute
    result = create_log_group(owner_name, repo_name)

    # Assert - should return None due to handle_exceptions decorator
    assert result is None
    mock_logs_client.create_log_group.assert_called_once()


def test_create_log_group_generic_exception(mock_logs_client):
    """Test log group creation when generic exception occurs."""
    # Setup
    owner_name = "testowner"
    repo_name = "testrepo"
    mock_logs_client.create_log_group.side_effect = Exception("Unexpected error")

    # Execute
    result = create_log_group(owner_name, repo_name)

    # Assert - should return None due to handle_exceptions decorator
    assert result is None
    mock_logs_client.create_log_group.assert_called_once()


@pytest.mark.parametrize(
    "owner_name,repo_name,expected_log_group",
    [
        ("owner1", "repo1", "/aws/lambda/gitauto/owner1/repo1"),
        ("my-org", "my-repo", "/aws/lambda/gitauto/my-org/my-repo"),
        ("test_owner", "test.repo", "/aws/lambda/gitauto/test_owner/test.repo"),
        ("123", "456", "/aws/lambda/gitauto/123/456"),
    ],
)
def test_create_log_group_various_names(mock_logs_client, owner_name, repo_name, expected_log_group):
    """Test log group creation with various owner and repo name combinations."""
    # Setup
    mock_logs_client.create_log_group.return_value = None

    # Execute
    result = create_log_group(owner_name, repo_name)

    # Assert
    assert result is None
    mock_logs_client.create_log_group.assert_called_once_with(
        logGroupName=expected_log_group
    )