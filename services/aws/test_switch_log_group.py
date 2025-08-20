# Standard imports
import os
from unittest.mock import patch, MagicMock

# Third party imports
import pytest
from botocore.exceptions import ClientError, BotoCoreError

# Local imports
from services.aws.switch_log_group import switch_lambda_log_group


@pytest.fixture
def mock_lambda_client():
    """Fixture to mock the lambda_client."""
    with patch("services.aws.switch_log_group.lambda_client") as mock:
        yield mock


@pytest.fixture
def mock_os_environ():
    """Fixture to mock os.environ."""
    with patch.dict(os.environ, {}, clear=True) as mock:
        yield mock


def test_switch_lambda_log_group_success_with_env_var(mock_lambda_client, mock_os_environ):
    """Test successful lambda log group switch with environment variable set."""
    # Setup
    owner_name = "testowner"
    repo_name = "testrepo"
    function_name = "custom-function-name"
    expected_log_group = "/aws/lambda/gitauto/testowner/testrepo"
    
    mock_os_environ["AWS_LAMBDA_FUNCTION_NAME"] = function_name
    mock_lambda_client.update_function_configuration.return_value = None

    # Execute
    result = switch_lambda_log_group(owner_name, repo_name)

    # Assert
    assert result is None
    mock_lambda_client.update_function_configuration.assert_called_once_with(
        FunctionName=function_name,
        LoggingConfig={"LogGroup": expected_log_group}
    )


def test_switch_lambda_log_group_success_with_default_function_name(mock_lambda_client, mock_os_environ):
    """Test successful lambda log group switch with default function name."""
    # Setup
    owner_name = "testowner"
    repo_name = "testrepo"
    expected_log_group = "/aws/lambda/gitauto/testowner/testrepo"
    
    # Don't set AWS_LAMBDA_FUNCTION_NAME environment variable
    mock_lambda_client.update_function_configuration.return_value = None

    # Execute
    result = switch_lambda_log_group(owner_name, repo_name)

    # Assert
    assert result is None
    mock_lambda_client.update_function_configuration.assert_called_once_with(
        FunctionName="pr-agent-prod",  # Default value
        LoggingConfig={"LogGroup": expected_log_group}
    )


def test_switch_lambda_log_group_with_special_characters(mock_lambda_client, mock_os_environ):
    """Test lambda log group switch with special characters in names."""
    # Setup
    owner_name = "test-owner_123"
    repo_name = "test.repo-name"
    expected_log_group = "/aws/lambda/gitauto/test-owner_123/test.repo-name"
    
    mock_lambda_client.update_function_configuration.return_value = None

    # Execute
    result = switch_lambda_log_group(owner_name, repo_name)

    # Assert
    assert result is None
    mock_lambda_client.update_function_configuration.assert_called_once_with(
        FunctionName="pr-agent-prod",
        LoggingConfig={"LogGroup": expected_log_group}
    )


def test_switch_lambda_log_group_client_error(mock_lambda_client, mock_os_environ):
    """Test lambda log group switch when ClientError occurs."""
    # Setup
    owner_name = "testowner"
    repo_name = "testrepo"
    error_response = {"Error": {"Code": "ResourceNotFoundException", "Message": "Function not found"}}
    mock_lambda_client.update_function_configuration.side_effect = ClientError(
        error_response, "UpdateFunctionConfiguration"
    )

    # Execute
    result = switch_lambda_log_group(owner_name, repo_name)

    # Assert - should return None due to handle_exceptions decorator
    assert result is None
    mock_lambda_client.update_function_configuration.assert_called_once()


def test_switch_lambda_log_group_botocore_error(mock_lambda_client, mock_os_environ):
    """Test lambda log group switch when BotoCoreError occurs."""
    # Setup
    owner_name = "testowner"
    repo_name = "testrepo"
    mock_lambda_client.update_function_configuration.side_effect = BotoCoreError()

    # Execute
    result = switch_lambda_log_group(owner_name, repo_name)

    # Assert - should return None due to handle_exceptions decorator
    assert result is None
    mock_lambda_client.update_function_configuration.assert_called_once()


def test_switch_lambda_log_group_generic_exception(mock_lambda_client, mock_os_environ):
    """Test lambda log group switch when generic exception occurs."""
    # Setup
    owner_name = "testowner"
    repo_name = "testrepo"
    mock_lambda_client.update_function_configuration.side_effect = Exception("Unexpected error")

    # Execute
    result = switch_lambda_log_group(owner_name, repo_name)

    # Assert - should return None due to handle_exceptions decorator
    assert result is None
    mock_lambda_client.update_function_configuration.assert_called_once()


@pytest.mark.parametrize(
    "owner_name,repo_name,function_name,expected_log_group",
    [
        ("owner1", "repo1", "func1", "/aws/lambda/gitauto/owner1/repo1"),
        ("my-org", "my-repo", "my-function", "/aws/lambda/gitauto/my-org/my-repo"),
        ("test_owner", "test.repo", "test-func", "/aws/lambda/gitauto/test_owner/test.repo"),
        ("123", "456", "func-789", "/aws/lambda/gitauto/123/456"),
    ],
)
def test_switch_lambda_log_group_various_names(mock_lambda_client, mock_os_environ, owner_name, repo_name, function_name, expected_log_group):
    """Test lambda log group switch with various name combinations."""
    # Setup
    mock_os_environ["AWS_LAMBDA_FUNCTION_NAME"] = function_name
    mock_lambda_client.update_function_configuration.return_value = None

    # Execute
    result = switch_lambda_log_group(owner_name, repo_name)

    # Assert
    assert result is None
    mock_lambda_client.update_function_configuration.assert_called_once_with(
        FunctionName=function_name,
        LoggingConfig={"LogGroup": expected_log_group}
    )