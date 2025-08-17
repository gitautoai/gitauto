from unittest.mock import patch, MagicMock
import pytest
from mypy_boto3_scheduler import EventBridgeSchedulerClient

from services.aws.client import scheduler_client, AWS_REGION


@pytest.fixture
def mock_boto3_client():
    """Mock boto3.client for testing."""
    with patch("services.aws.client.boto3.client") as mock:
        mock_scheduler = MagicMock(spec=EventBridgeSchedulerClient)
        mock.return_value = mock_scheduler
        yield mock


def test_aws_region_constant():
    """Test that AWS_REGION is set to the correct value."""
    assert AWS_REGION == "us-west-1"


def test_scheduler_client_is_eventbridge_scheduler_client():
    """Test that scheduler_client is an EventBridgeSchedulerClient instance."""
    assert isinstance(scheduler_client, EventBridgeSchedulerClient)


def test_scheduler_client_created_with_correct_parameters(mock_boto3_client):
    """Test that scheduler_client is created with correct parameters."""
    # Re-import to trigger the client creation with mocked boto3
    from importlib import reload
    import services.aws.client
    reload(services.aws.client)
    
    mock_boto3_client.assert_called_once_with("scheduler", region_name="us-west-1")


def test_scheduler_client_service_name(mock_boto3_client):
    """Test that the correct AWS service name is used."""
    from importlib import reload
    import services.aws.client
    reload(services.aws.client)
    
    # Verify boto3.client was called with "scheduler" service
    args, kwargs = mock_boto3_client.call_args
    assert args[0] == "scheduler"


def test_scheduler_client_region_configuration(mock_boto3_client):
    """Test that the correct region is configured."""
    from importlib import reload
    import services.aws.client
    reload(services.aws.client)
    
    # Verify boto3.client was called with correct region
    args, kwargs = mock_boto3_client.call_args
    assert kwargs["region_name"] == AWS_REGION


def test_scheduler_client_singleton_behavior():
    """Test that scheduler_client maintains singleton-like behavior."""
    from services.aws.client import scheduler_client as client1
    from services.aws.client import scheduler_client as client2
    
    # Both imports should reference the same client instance
    assert client1 is client2


@patch("services.aws.client.boto3.client")
def test_scheduler_client_initialization_called_once(mock_boto3_client):
    """Test that boto3.client is called only once during module import."""
    mock_scheduler = MagicMock(spec=EventBridgeSchedulerClient)
    mock_boto3_client.return_value = mock_scheduler
    
    # Re-import the module multiple times
    from importlib import reload
    import services.aws.client
    reload(services.aws.client)
    reload(services.aws.client)
    reload(services.aws.client)
    
    # boto3.client should be called once per reload (3 times total)
    assert mock_boto3_client.call_count == 3


def test_scheduler_client_has_expected_methods():
    """Test that scheduler_client has expected EventBridge Scheduler methods."""
    # These are common methods available on EventBridge Scheduler client
    expected_methods = [
        'create_schedule',
        'delete_schedule',
        'get_schedule',
        'list_schedules',
        'update_schedule'
    ]
    
    for method in expected_methods:
        assert hasattr(scheduler_client, method), f"scheduler_client missing method: {method}"


def test_aws_region_is_string():
    """Test that AWS_REGION is a string."""
    assert isinstance(AWS_REGION, str)
    assert len(AWS_REGION) > 0


def test_aws_region_format():
    """Test that AWS_REGION follows AWS region naming convention."""
    # AWS regions typically follow pattern: us-west-1, eu-central-1, etc.
    import re
    region_pattern = r'^[a-z]{2}-[a-z]+-\d+$'
    assert re.match(region_pattern, AWS_REGION), f"AWS_REGION '{AWS_REGION}' doesn't match expected pattern"


@patch("services.aws.client.boto3")
def test_boto3_import_success(mock_boto3):
    """Test that boto3 is imported successfully."""
    mock_client = MagicMock(spec=EventBridgeSchedulerClient)
    mock_boto3.client.return_value = mock_client
    
    from importlib import reload
    import services.aws.client
    reload(services.aws.client)
    
    mock_boto3.client.assert_called_once()


def test_module_level_constants():
    """Test that all expected module-level constants are defined."""
    import services.aws.client as aws_client_module
    
    # Check that required constants exist
    assert hasattr(aws_client_module, 'AWS_REGION')
    assert hasattr(aws_client_module, 'scheduler_client')
    
    # Check their types
    assert isinstance(aws_client_module.AWS_REGION, str)
    assert isinstance(aws_client_module.scheduler_client, EventBridgeSchedulerClient)


@pytest.mark.parametrize("region", [
    "us-west-1",
    "us-east-1", 
    "eu-central-1",
    "ap-southeast-1"
])
def test_aws_region_variations(region):
    """Test that different AWS regions would work with the client setup."""
    with patch("services.aws.client.AWS_REGION", region):
        with patch("services.aws.client.boto3.client") as mock_client:
            mock_scheduler = MagicMock(spec=EventBridgeSchedulerClient)
            mock_client.return_value = mock_scheduler
            
            from importlib import reload
            import services.aws.client
            reload(services.aws.client)
            
            mock_client.assert_called_with("scheduler", region_name=region)
