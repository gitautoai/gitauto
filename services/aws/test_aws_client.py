import pytest
import boto3
from mypy_boto3_scheduler import EventBridgeSchedulerClient


class TestAwsClient:
    """Test cases for AWS client module."""

    def test_aws_region_constant(self):
        """Test that AWS_REGION is set to the expected value."""
        from services.aws.client import AWS_REGION
        assert AWS_REGION == "us-west-1"

    def test_scheduler_client_is_eventbridge_scheduler_client(self):
        """Test that scheduler_client is an EventBridge Scheduler client instance."""
        from services.aws.client import scheduler_client
        assert isinstance(scheduler_client, EventBridgeSchedulerClient)

    def test_scheduler_client_uses_correct_region(self):
        """Test that scheduler_client is configured with the correct region."""
        from services.aws.client import scheduler_client, AWS_REGION
        assert scheduler_client.meta.region_name == AWS_REGION

    def test_scheduler_client_service_name(self):
        """Test that scheduler_client uses the correct service name."""
        from services.aws.client import scheduler_client
        assert scheduler_client.meta.service_model.service_name == "scheduler"

    def test_module_imports_successfully(self):
        """Test that the module can be imported without errors."""
        import services.aws.client
        
        assert hasattr(services.aws.client, 'AWS_REGION')
        assert hasattr(services.aws.client, 'scheduler_client')