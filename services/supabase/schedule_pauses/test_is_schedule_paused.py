# Standard imports
from unittest.mock import MagicMock, patch

# Third-party imports
import pytest

# Local imports
from services.supabase.schedule_pauses.is_schedule_paused import is_schedule_paused


@pytest.fixture
def mock_supabase():
    with patch("services.supabase.schedule_pauses.is_schedule_paused.supabase") as mock:
        yield mock


class TestIsSchedulePaused:
    def test_returns_true_when_pause_exists(self, mock_supabase: MagicMock):
        mock_execute = MagicMock()
        mock_execute.data = [{"id": "uuid-1"}]
        (
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.lte.return_value.gte.return_value.limit.return_value.execute
        ).return_value = mock_execute

        result = is_schedule_paused(owner_id=123, repo_id=456)

        assert result is True
        mock_supabase.table.assert_called_with("schedule_pauses")

    def test_returns_false_when_no_pause(self, mock_supabase: MagicMock):
        mock_execute = MagicMock()
        mock_execute.data = []
        (
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.lte.return_value.gte.return_value.limit.return_value.execute
        ).return_value = mock_execute

        result = is_schedule_paused(owner_id=123, repo_id=456)

        assert result is False

    def test_returns_false_when_data_is_none(self, mock_supabase: MagicMock):
        mock_execute = MagicMock()
        mock_execute.data = None
        (
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.lte.return_value.gte.return_value.limit.return_value.execute
        ).return_value = mock_execute

        result = is_schedule_paused(owner_id=123, repo_id=456)

        assert result is False

    def test_queries_with_utc_timestamp(self, mock_supabase: MagicMock):
        mock_execute = MagicMock()
        mock_execute.data = []
        mock_limit = MagicMock()
        mock_limit.execute.return_value = mock_execute
        mock_gte = MagicMock()
        mock_gte.limit.return_value = mock_limit
        mock_lte = MagicMock()
        mock_lte.gte.return_value = mock_gte
        mock_eq2 = MagicMock()
        mock_eq2.lte.return_value = mock_lte
        mock_eq1 = MagicMock()
        mock_eq1.eq.return_value = mock_eq2
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq1
        mock_supabase.table.return_value.select.return_value = mock_select

        is_schedule_paused(owner_id=123, repo_id=456)

        mock_select.eq.assert_called_with("owner_id", 123)
        mock_eq1.eq.assert_called_with("repo_id", 456)
        # Verify lte/gte are called with a full ISO timestamp (not just a date)
        lte_arg = mock_eq2.lte.call_args[0][1]
        gte_arg = mock_lte.gte.call_args[0][1]
        assert "T" in lte_arg, f"Expected ISO timestamp with 'T', got: {lte_arg}"
        assert "T" in gte_arg, f"Expected ISO timestamp with 'T', got: {gte_arg}"

    def test_returns_false_on_exception(self, mock_supabase: MagicMock):
        mock_supabase.table.side_effect = Exception("DB connection failed")

        result = is_schedule_paused(owner_id=123, repo_id=456)

        assert result is False


class TestIsSchedulePausedIntegration:
    """Integration tests against the dev Supabase database."""

    def test_returns_true_for_active_pause(self):
        """owner_id=159883862, repo_id=764482881 has an active pause ending 2026-02-27."""
        result = is_schedule_paused(owner_id=159883862, repo_id=764482881)
        assert result is True

    def test_returns_false_for_nonexistent_owner(self):
        result = is_schedule_paused(owner_id=999999999, repo_id=999999999)
        assert result is False

    def test_returns_false_for_unpaused_repo(self):
        result = is_schedule_paused(owner_id=159883862, repo_id=999999999)
        assert result is False
