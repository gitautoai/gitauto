import pytest
import boto3
from unittest.mock import patch
from mypy_boto3_scheduler import EventBridgeSchedulerClient


class TestAwsClient:
    """Test cases for AWS client module."""

    def test_aws_region_constant(self, mock_boto3_client):
        """Test that AWS_REGION is set to the expected value."""
        from services.aws.client import AWS_REGION
        assert AWS_REGION == "us-west-1"

    @patch('boto3.client')
    def test_scheduler_client_is_eventbridge_scheduler_client(self, mock_client, mock_boto3_client):
        """Test that scheduler_client is an EventBridge Scheduler client instance."""
        # Import after patching to ensure the mock is used
        from services.aws.client import scheduler_client
        # Since we're mocking, we can't use isinstance directly
        # Instead, verify the mock was called with the correct parameters
        mock_client.assert_called_once_with("scheduler", region_name="us-west-1")

    def test_scheduler_client_uses_correct_region(self, mock_boto3_client):
        """Test that scheduler_client is configured with the correct region."""
        from services.aws.client import scheduler_client, AWS_REGION
        assert scheduler_client.meta.region_name == AWS_REGION

    def test_scheduler_client_service_name(self, mock_boto3_client):
        """Test that scheduler_client uses the correct service name."""
        from services.aws.client import scheduler_client
        assert scheduler_client.meta.service_model.service_name == "scheduler"

    def test_module_imports_successfully(self, mock_boto3_client):
        """Test that the module can be imported without errors."""
        import services.aws.client
        
        assert hasattr(services.aws.client, 'AWS_REGION')
        assert hasattr(services.aws.client, 'scheduler_client')