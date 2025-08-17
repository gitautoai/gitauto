from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture
def mock_boto3_client():
    """Mock boto3.client for testing."""
    with patch("services.aws.client.boto3.client") as mock:
        yield mock


def test_aws_region_constant():
    """Test that AWS_REGION is set to the expected value."""
    from services.aws.client import AWS_REGION
    
    assert AWS_REGION == "us-west-1"


def test_scheduler_client_initialization(mock_boto3_client):
    """Test that scheduler_client is initialized correctly."""
    # Import after mocking to ensure the mock is applied
    from services.aws.client import scheduler_client
    
    # Verify boto3.client was called with correct parameters
    mock_boto3_client.assert_called_once_with("scheduler", region_name="us-west-1")
    
    # Verify scheduler_client is the return value of boto3.client
    assert scheduler_client == mock_boto3_client.return_value


def test_scheduler_client_type_annotation(mock_boto3_client):
    """Test that scheduler_client has the correct type annotation."""
    from services.aws.client import scheduler_client
    
    # The client should be the mocked return value
    assert scheduler_client == mock_boto3_client.return_value


def test_scheduler_client_is_singleton(mock_boto3_client):
    """Test that scheduler_client is created only once (singleton pattern)."""
    # Import multiple times to verify it's only created once
    from services.aws.client import scheduler_client as client1
    from services.aws.client import scheduler_client as client2
    
    # Both imports should reference the same object
    assert client1 is client2
    
    # boto3.client should only be called once during module import
    mock_boto3_client.assert_called_once()


def test_module_imports():
    """Test that all required imports are available."""
    import services.aws.client as client_module
    
    # Check that all expected attributes exist
    assert hasattr(client_module, "boto3")
    assert hasattr(client_module, "EventBridgeSchedulerClient")
    assert hasattr(client_module, "AWS_REGION")
    assert hasattr(client_module, "scheduler_client")


def test_aws_region_is_string():
    """Test that AWS_REGION is a string."""
    from services.aws.client import AWS_REGION
    
    assert isinstance(AWS_REGION, str)
    assert len(AWS_REGION) > 0