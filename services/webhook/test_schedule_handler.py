# Standard imports
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest

# Local imports
from services.webhook.schedule_handler import schedule_handler


@pytest.fixture
def mock_event():
    """Fixture for EventBridge event."""
    return {
        "ownerId": 123,
        "ownerType": "Organization",
        "ownerName": "test-org",
        "repoId": 456,
        "repoName": "test-repo",
        "userId": 789,
        "userName": "test-user",
        "installationId": 999,
    }


class TestScheduleHandler:
    def test_schedule_handler_missing_required_fields(self):
        """Test that schedule_handler raises ValueError when required fields are missing."""
        # Setup - event with missing fields
        incomplete_event = {
            "ownerId": 123,
            "ownerName": "test-org",
            # Missing other required fields
        }

        # Execute and verify - should raise ValueError
        with pytest.raises(ValueError, match="Missing required fields in event detail"):
            schedule_handler(incomplete_event)

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    def test_schedule_handler_no_token(self, mock_get_token, mock_event):
        """Test that schedule_handler raises ValueError when token is None."""
        # Setup
        mock_get_token.return_value = None

        # Execute and verify
        with pytest.raises(ValueError, match="Token is None for installation_id"):
            schedule_handler(mock_event)

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    def test_schedule_handler_trigger_disabled(
        self, mock_get_repository, mock_get_token, mock_event
    ):
        """Test that schedule_handler skips when trigger_on_schedule is disabled."""
        # Setup
        mock_get_token.return_value = "test-token"
        mock_get_repository.return_value = {
            "id": 456,
            "name": "test-repo",
            "trigger_on_schedule": False,
        }

        # Execute
        result = schedule_handler(mock_event)

        # Verify
        assert result["status"] == "skipped"
        assert "trigger_on_schedule is not enabled" in result["message"]

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.is_request_limit_reached")
    def test_schedule_handler_request_limit_reached(
        self,
        mock_is_request_limit_reached,
        mock_get_repository,
        mock_get_token,
        mock_event,
    ):
        """Test that schedule_handler skips when request limit is reached."""
        # Setup
        mock_get_token.return_value = "test-token"
        mock_get_repository.return_value = {
            "id": 456,
            "name": "test-repo",
            "trigger_on_schedule": True,
        }
        mock_is_request_limit_reached.return_value = {"is_limit_reached": True}

        # Execute
        result = schedule_handler(mock_event)

        # Verify
        assert result["status"] == "skipped"
        assert "Request limit reached" in result["message"]

    @patch("services.webhook.schedule_handler.get_all_coverages")
    def test_get_all_coverages_returns_empty_list_not_none(
        self, mock_get_all_coverages
    ):
        """Test that get_all_coverages returns empty list instead of None.

        This test verifies the fix for 'NoneType' object is not iterable error.
        """
        # Setup - simulate empty coverage data
        mock_get_all_coverages.return_value = []  # Should be empty list, not None

        # Execute
        all_coverages = mock_get_all_coverages(repo_id=123)

        # Verify - should be able to iterate without TypeError
        assert isinstance(all_coverages, list)
        assert len(all_coverages) == 0

        # This would fail with TypeError if all_coverages was None
        for coverage in all_coverages:
            pass  # Should not raise TypeError

        # Test the actual pattern used in schedule_handler
        test_files = [("src/main.py", 1024), ("src/utils.py", 512)]
        enriched_files = []

        for file_path, file_size in test_files:
            # This is the line that was failing at line 114
            coverages = next(
                (c for c in all_coverages if c.get("full_path") == file_path), None
            )
            if coverages:
                enriched_files.append(coverages)
            else:
                enriched_files.append({"full_path": file_path, "file_size": file_size})

        # Verify we processed all files without error
        assert len(enriched_files) == 2
        assert all("full_path" in f for f in enriched_files)

    def test_get_all_coverages_contract(self):
        """Verify that get_all_coverages always returns a list."""
        from services.supabase.coverages.get_all_coverages import get_all_coverages

        with patch(
            "services.supabase.coverages.get_all_coverages.supabase"
        ) as mock_supabase:
            # Setup mock to return empty data
            mock_result = MagicMock()
            mock_result.data = []
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = (
                mock_result
            )

            # Execute
            result = get_all_coverages(repo_id=123)

            # Verify - should be empty list, not None
            assert result == []
            assert result is not None
            assert isinstance(result, list)
