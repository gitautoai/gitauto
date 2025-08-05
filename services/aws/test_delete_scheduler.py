# Standard imports
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest

# Local imports
from services.aws.delete_scheduler import delete_scheduler


class TestDeleteScheduler:
    @patch("services.aws.delete_scheduler.scheduler_client")
    @patch("services.aws.delete_scheduler.logging")
    def test_delete_scheduler_success(self, mock_logging, mock_scheduler_client):
        """Test successful scheduler deletion."""
        # Setup
        schedule_name = "gitauto-repo-123-456"
        mock_scheduler_client.delete_schedule.return_value = None
        
        # Execute
        result = delete_scheduler(schedule_name)
        
        # Verify
        mock_scheduler_client.delete_schedule.assert_called_once_with(Name=schedule_name)
        mock_logging.info.assert_called_once_with(
            "Deleted EventBridge Scheduler: %s", schedule_name
        )
        assert result is True

    @patch("services.aws.delete_scheduler.scheduler_client")
    @patch("services.aws.delete_scheduler.logging")
    def test_delete_scheduler_with_exception(self, mock_logging, mock_scheduler_client):
        """Test scheduler deletion when AWS client raises exception."""
        # Setup
        schedule_name = "gitauto-repo-123-456"
        mock_scheduler_client.delete_schedule.side_effect = Exception("AWS Error")
        
        # Execute - should not raise exception due to handle_exceptions decorator
        result = delete_scheduler(schedule_name)
        
        # Verify
        mock_scheduler_client.delete_schedule.assert_called_once_with(Name=schedule_name)
        # Logging should not be called when exception occurs
        mock_logging.info.assert_not_called()
        # Should return default value False due to handle_exceptions decorator
        assert result is False

    @patch("services.aws.delete_scheduler.scheduler_client")
    def test_delete_scheduler_with_empty_name(self, mock_scheduler_client):
        """Test scheduler deletion with empty schedule name."""
        # Setup
        schedule_name = ""
        
        # Execute
        result = delete_scheduler(schedule_name)
        
        # Verify
        mock_scheduler_client.delete_schedule.assert_called_once_with(Name="")
        assert result is True

    @patch("services.aws.delete_scheduler.scheduler_client")
    def test_delete_scheduler_with_special_characters(self, mock_scheduler_client):
        """Test scheduler deletion with special characters in name."""
        # Setup
        schedule_name = "gitauto-repo-123-456-test_special-chars"
        
        # Execute
        result = delete_scheduler(schedule_name)
        
        # Verify
        mock_scheduler_client.delete_schedule.assert_called_once_with(Name=schedule_name)
        assert result is True