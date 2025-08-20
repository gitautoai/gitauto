# Standard imports
from unittest.mock import patch, MagicMock

# Third party imports
import pytest


@pytest.fixture
def mock_boto3_client():
    """Fixture to mock boto3.client."""
    with patch("services.aws.clients.boto3.client") as mock:
        yield mock


def test_aws_region_constant():
    """Test that AWS_REGION is set to the correct value."""
    from services.aws.clients import AWS_REGION
    
    assert AWS_REGION == "us-west-1"


def test_lambda_client_initialization(mock_boto3_client):
    """Test that lambda_client is initialized with correct parameters."""
    # Import after mocking to ensure the mock is applied
    import importlib
    import services.aws.clients
    importlib.reload(services.aws.clients)
    
    # Verify boto3.client was called with correct parameters for lambda
    mock_boto3_client.assert_any_call("lambda", region_name="us-west-1")


def test_logs_client_initialization(mock_boto3_client):
    """Test that logs_client is initialized with correct parameters."""
    # Import after mocking to ensure the mock is applied
    import importlib
    import services.aws.clients
    importlib.reload(services.aws.clients)
    
    # Verify boto3.client was called with correct parameters for logs
    mock_boto3_client.assert_any_call("logs", region_name="us-west-1")


def test_scheduler_client_initialization(mock_boto3_client):
    """Test that scheduler_client is initialized with correct parameters."""
    # Import after mocking to ensure the mock is applied
    import importlib
    import services.aws.clients
    importlib.reload(services.aws.clients)
    
    # Verify boto3.client was called with correct parameters for scheduler
    mock_boto3_client.assert_any_call("scheduler", region_name="us-west-1")


def test_all_clients_initialization(mock_boto3_client):
    """Test that all three clients are initialized when module is imported."""
    # Import after mocking to ensure the mock is applied
    import importlib
    import services.aws.clients
    importlib.reload(services.aws.clients)
    
    # Verify boto3.client was called exactly 3 times
    assert mock_boto3_client.call_count == 3
    
    # Verify all expected calls were made
    expected_calls = [
        ("lambda", "us-west-1"),
        ("logs", "us-west-1"),
        ("scheduler", "us-west-1")
    ]
    
    actual_calls = [(call[0][0], call[1]["region_name"]) for call in mock_boto3_client.call_args_list]
    
    for expected_call in expected_calls:
        assert expected_call in actual_calls


def test_client_types():
    """Test that clients have the expected types when imported."""
    from services.aws.clients import lambda_client, logs_client, scheduler_client
    
    # These should be boto3 client objects (we can't test exact type due to mocking)
    assert lambda_client is not None
    assert logs_client is not None
    assert scheduler_client is not None
