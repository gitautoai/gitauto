# Standard imports
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest

# Local imports
from services.aws.get_schedulers import get_schedulers_by_owner_id


class TestGetSchedulers:
    @patch("services.aws.get_schedulers.scheduler_client")
    def test_get_schedulers_by_owner_id_single_page(self, mock_scheduler_client):
        """Test getting schedulers for owner ID with single page response."""
        # Setup
        owner_id = 123
        mock_response = {
            "Schedules": [
                {"Name": "gitauto-repo-123-456"},
                {"Name": "gitauto-repo-123-789"},
                {"Name": "gitauto-repo-999-111"},  # Different owner, should be filtered out
                {"Name": "other-schedule"},  # Different pattern, should be filtered out
            ]
        }
        mock_scheduler_client.list_schedules.return_value = mock_response
        
        # Execute
        result = get_schedulers_by_owner_id(owner_id)
        
        # Verify
        mock_scheduler_client.list_schedules.assert_called_once_with()
        expected_schedules = ["gitauto-repo-123-456", "gitauto-repo-123-789"]
        assert result == expected_schedules

    @patch("services.aws.get_schedulers.scheduler_client")
    def test_get_schedulers_by_owner_id_multiple_pages(self, mock_scheduler_client):
        """Test getting schedulers with pagination."""
        # Setup
        owner_id = 123
        mock_responses = [
            {
                "Schedules": [
                    {"Name": "gitauto-repo-123-456"},
                    {"Name": "gitauto-repo-123-789"},
                ],
                "NextToken": "token123"
            },
            {
                "Schedules": [
                    {"Name": "gitauto-repo-123-101"},
                    {"Name": "gitauto-repo-999-222"},  # Different owner
                ]
            }
        ]
        mock_scheduler_client.list_schedules.side_effect = mock_responses
        
        # Execute
        result = get_schedulers_by_owner_id(owner_id)
        
        # Verify
        assert mock_scheduler_client.list_schedules.call_count == 2
        mock_scheduler_client.list_schedules.assert_any_call()
        mock_scheduler_client.list_schedules.assert_any_call(NextToken="token123")
        expected_schedules = ["gitauto-repo-123-456", "gitauto-repo-123-789", "gitauto-repo-123-101"]
        assert result == expected_schedules

    @patch("services.aws.get_schedulers.scheduler_client")
    def test_get_schedulers_by_owner_id_no_schedules(self, mock_scheduler_client):
        """Test getting schedulers when no schedules exist."""
        # Setup
        owner_id = 123
        mock_response = {"Schedules": []}
        mock_scheduler_client.list_schedules.return_value = mock_response
        
        # Execute
        result = get_schedulers_by_owner_id(owner_id)
        
        # Verify
        mock_scheduler_client.list_schedules.assert_called_once_with()
        assert result == []

    @patch("services.aws.get_schedulers.scheduler_client")
    def test_get_schedulers_by_owner_id_no_matching_schedules(self, mock_scheduler_client):
        """Test getting schedulers when no schedules match the owner ID."""
        # Setup
        owner_id = 123
        mock_response = {
            "Schedules": [
                {"Name": "gitauto-repo-999-456"},  # Different owner
                {"Name": "other-schedule"},  # Different pattern
                {"Name": "gitauto-repo-456-123"},  # Different owner
            ]
        }
        mock_scheduler_client.list_schedules.return_value = mock_response
        
        # Execute
        result = get_schedulers_by_owner_id(owner_id)
        
        # Verify
        mock_scheduler_client.list_schedules.assert_called_once_with()
        assert result == []

    @patch("services.aws.get_schedulers.scheduler_client")
    def test_get_schedulers_by_owner_id_with_index_suffix(self, mock_scheduler_client):
        """Test getting schedulers with index suffix pattern."""
        # Setup
        owner_id = 123
        mock_response = {
            "Schedules": [
                {"Name": "gitauto-repo-123-456"},
                {"Name": "gitauto-repo-123-456-1"},
                {"Name": "gitauto-repo-123-456-2"},
                {"Name": "gitauto-repo-123-789-test"},
            ]
        }
        mock_scheduler_client.list_schedules.return_value = mock_response
        
        # Execute
        result = get_schedulers_by_owner_id(owner_id)
        
        # Verify
        expected_schedules = [
            "gitauto-repo-123-456",
            "gitauto-repo-123-456-1", 
            "gitauto-repo-123-456-2",
            "gitauto-repo-123-789-test"
        ]
        assert result == expected_schedules

    @patch("services.aws.get_schedulers.scheduler_client")
    def test_get_schedulers_by_owner_id_with_exception(self, mock_scheduler_client):
        """Test getting schedulers when AWS client raises exception."""
        # Setup
        owner_id = 123
        mock_scheduler_client.list_schedules.side_effect = Exception("AWS Error")
        
        # Execute - should not raise exception due to handle_exceptions decorator
        result = get_schedulers_by_owner_id(owner_id)
        
        # Verify
        mock_scheduler_client.list_schedules.assert_called_once_with()
        # Should return default value [] due to handle_exceptions decorator
        assert result == []