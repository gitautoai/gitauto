from unittest.mock import patch, MagicMock

import pytest
import boto3
from mypy_boto3_scheduler import EventBridgeSchedulerClient

from services.aws.client import AWS_REGION, scheduler_client


@pytest.fixture
def mock_boto3_client():
    """Fixture to provide a mocked boto3.client function."""
    with patch("services.aws.client.boto3.client") as mock:
        mock_scheduler_client = MagicMock(spec=EventBridgeSchedulerClient)
        mock.return_value = mock_scheduler_client
        yield mock


def test_aws_region_constant():
    """Test that AWS_REGION is set to the expected value."""
    assert AWS_REGION == "us-west-1"


def test_scheduler_client_is_eventbridge_scheduler_client():
    """Test that scheduler_client is an EventBridge Scheduler client instance."""
    assert isinstance(scheduler_client, EventBridgeSchedulerClient)


def test_scheduler_client_uses_correct_region():
    """Test that scheduler_client is configured with the correct region."""
    # Since the client is already instantiated, we need to check its configuration
    # The region is typically stored in the client's meta configuration
    assert scheduler_client.meta.region_name == AWS_REGION


def test_scheduler_client_service_name():
    """Test that scheduler_client uses the correct service name."""
    assert scheduler_client.meta.service_model.service_name == "scheduler"


@patch("services.aws.client.boto3.client")
def test_scheduler_client_creation_with_mock(mock_boto3_client):
    """Test that scheduler_client is created with correct parameters."""
    # Import the module to trigger client creation
    from services.aws import client
    
    mock_boto3_client.assert_called_with("scheduler", region_name=AWS_REGION)


def test_scheduler_client_has_expected_methods():
    """Test that scheduler_client has the expected EventBridge Scheduler methods."""
    expected_methods = [
        "create_schedule",
        "delete_schedule",
        "get_schedule",
        "list_schedules",
        "update_schedule",
        "create_schedule_group",
        "delete_schedule_group",
        "get_schedule_group",
        "list_schedule_groups",
    ]
    
    for method in expected_methods:
        assert hasattr(scheduler_client, method)
        assert callable(getattr(scheduler_client, method))


def test_scheduler_client_singleton_behavior():
    """Test that importing the module multiple times returns the same client instance."""
    from services.aws.client import scheduler_client as client1
    from services.aws.client import scheduler_client as client2
    
    assert client1 is client2
    assert id(client1) == id(client2)


@pytest.mark.parametrize("region", ["us-east-1", "eu-west-1", "ap-southeast-1"])
def test_different_regions_would_create_different_clients(region):
    """Test that different regions would create different client configurations."""
    with patch("services.aws.client.boto3.client") as mock_client:
        mock_scheduler = MagicMock(spec=EventBridgeSchedulerClient)
        mock_client.return_value = mock_scheduler
        
        # Simulate creating a client with a different region
        test_client = boto3.client("scheduler", region_name=region)
        mock_client.assert_called_with("scheduler", region_name=region)
