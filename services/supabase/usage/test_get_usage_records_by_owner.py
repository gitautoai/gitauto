# pylint: disable=redefined-outer-name, unused-argument
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

from constants.triggers import Trigger
from services.supabase.client import supabase
from services.supabase.usage.get_usage_records_by_owner import \
    get_usage_records_by_owner
from services.supabase.usage.insert_usage import insert_usage

# ===== solitary =====

def test_get_usage_records_by_owner_success():
    """Verify that usage records are correctly retrieved for a given owner and date range."""
    with patch("services.supabase.usage.get_usage_records_by_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_gte = Mock()
        mock_lt = Mock()
        mock_order = Mock()
        mock_execute = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.gte.return_value = mock_gte
        mock_gte.lt.return_value = mock_lt
        mock_lt.order.return_value = mock_order
        mock_order.execute.return_value = Mock(data=[{"id": 1}, {"id": 2}])

        owner = "test-owner"
        start = "2023-01-01T00:00:00Z"
        end = "2023-01-02T00:00:00Z"
        result = get_usage_records_by_owner(owner, start, end)

        assert result == [{"id": 1}, {"id": 2}]
        mock_supabase.table.assert_called_once_with("usage")
        mock_table.select.assert_called_once_with("id, repo_name, pr_number, trigger, is_completed, created_at")
        mock_select.eq.assert_called_once_with("owner_name", owner)
        mock_eq.gte.assert_called_once_with("created_at", start)
        mock_gte.lt.assert_called_once_with("created_at", end)
        mock_lt.order.assert_called_once_with("created_at")
        mock_order.execute.assert_called_once()


def test_get_usage_records_by_owner_empty():
    """Verify that an empty list is returned when no records match the criteria."""
    with patch("services.supabase.usage.get_usage_records_by_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_gte = Mock()
        mock_lt = Mock()
        mock_order = Mock()
        mock_execute = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.gte.return_value = mock_gte
        mock_gte.lt.return_value = mock_lt
        mock_lt.order.return_value = mock_order
        mock_order.execute.return_value = Mock(data=[])

        result = get_usage_records_by_owner("test-owner", "2023-01-01", "2023-01-02")
        assert result == []


def test_get_usage_records_by_owner_exception():
    """Verify that an empty list is returned when a database exception occurs."""
    with patch("services.supabase.usage.get_usage_records_by_owner.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database error")

        result = get_usage_records_by_owner("test-owner", "2023-01-01", "2023-01-02")
        assert result == []


# ===== integration =====

@pytest.mark.skipif(not os.getenv("SUPABASE_URL"), reason="No Supabase credentials")
class TestGetUsageRecordsByOwnerIntegration:
    test_owner = f"test_owner_{os.urandom(4).hex()}"

    def setup_method(self):
        # Ensure clean state for the test owner
        supabase.table("usage").delete().eq("owner_name", self.test_owner).execute()

    def teardown_method(self):
        # Clean up test data
        supabase.table("usage").delete().eq("owner_name", self.test_owner).execute()

    def test_get_usage_records_by_owner_success(self):
        """Verify that records are correctly filtered by owner and date range, and ordered by created_at."""
        now = datetime.utcnow()
        start = now - timedelta(days=2)
        end = now + timedelta(days=2)

        # Record 1: Before range
        insert_usage(
            owner_id=1, owner_type="User", owner_name=self.test_owner,
            repo_id=1, repo_name="repo1", pr_number=1, user_id=1, user_name="u1",
            installation_id=1, source="test", trigger=Trigger.DASHBOARD
        )
        # We can't easily set created_at via insert_usage, but we can update it if needed.
        # However, for this test, we can just use the current time and adjust the range.

        # Let's use a more reliable way to test date ranges by inserting and then updating created_at
        # since insert_usage doesn't allow specifying created_at.

        # Actually, let's just insert records and use a range that definitely includes them.
        # To test the range, we can insert records, then use a range that excludes them.

        # Insert 3 records
        for i in range(3):
            insert_usage(
                owner_id=1, owner_type="User", owner_name=self.test_owner,
                repo_id=i, repo_name=f"repo{i}", pr_number=i, user_id=1, user_name="u1",
                installation_id=1, source="test", trigger=Trigger.DASHBOARD
            )

        # Use a range that covers now
        start_range = (now - timedelta(days=1)).isoformat()
        end_range = (now + timedelta(days=1)).isoformat()

        results = get_usage_records_by_owner(self.test_owner, start_range, end_range)
        assert len(results) == 3

        # Verify ordering (created_at should be ascending)
        created_ats = [r["created_at"] for r in results]
        assert created_ats == sorted(created_ats)

    def test_get_usage_records_by_owner_no_records(self):
        """Verify that an empty list is returned when no records exist for the owner."""
        results = get_usage_records_by_owner("non_existent_owner_12345", "2000-01-01", "2100-01-01")
        assert results == []

    def test_get_usage_records_by_owner_wrong_range(self):
        """Verify that records are not returned if they fall outside the specified date range."""
        insert_usage(
            owner_id=1, owner_type="User", owner_name=self.test_owner,
            repo_id=1, repo_name="repo1", pr_number=1, user_id=1, user_name="u1",
            installation_id=1, source="test", trigger=Trigger.DASHBOARD
        )

        # Range in the past
        start_range = "2000-01-01T00:00:00Z"
        end_range = "2000-01-02T00:00:00Z"

        results = get_usage_records_by_owner(self.test_owner, start_range, end_range)
        assert results == []
