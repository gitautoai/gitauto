import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_boto3_client():
    """Mock boto3.client to avoid making actual AWS API calls during tests."""
    with patch('boto3.client') as mock_client:
        # Create a mock EventBridgeSchedulerClient
        mock_scheduler = MagicMock()
        mock_scheduler.meta.region_name = "us-west-1"
        mock_scheduler.meta.service_model.service_name = "scheduler"
        
        # Configure the mock to return our mock scheduler
        mock_client.return_value = mock_scheduler
        
        yield mock_client