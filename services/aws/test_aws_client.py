# Standard imports
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest


class TestAWSClient:
    @patch("services.aws.client.boto3")
    def test_scheduler_client_initialization(self, mock_boto3):
        """Test that scheduler client is properly initialized."""
        # Setup
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Import the module to trigger initialization
        import services.aws.client
        
        # Verify
        mock_boto3.client.assert_called_once_with("scheduler")
        assert scheduler_client == mock_client

    def test_scheduler_client_type(self):
        """Test that scheduler_client has the expected type annotation."""
        from services.aws.client import scheduler_client
        assert scheduler_client is not None
