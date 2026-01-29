from unittest.mock import Mock, patch

from services.supabase.installations.get_installation_by_owner import (
    get_installation_by_owner,
)


def test_get_installation_by_owner_success():
    mock_result = Mock()
    mock_result.data = {
        "installation_id": 12345,
        "owner_id": 789,
        "owner_name": "test-owner",
        "owner_type": "Organization",
        "uninstalled_at": None,
    }

    with patch(
        "services.supabase.installations.get_installation_by_owner.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_is = Mock()
        mock_maybe_single = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.is_.return_value = mock_is
        mock_is.maybe_single.return_value = mock_maybe_single
        mock_maybe_single.execute.return_value = mock_result

        result = get_installation_by_owner("test-owner")

        assert result is not None
        assert isinstance(result, dict)
        assert result["installation_id"] == 12345
        assert result["owner_id"] == 789
        assert result["owner_name"] == "test-owner"

        mock_supabase.table.assert_called_once_with("installations")
        mock_table.select.assert_called_once_with("*")
        mock_select.eq.assert_called_once_with("owner_name", "test-owner")
        mock_eq.is_.assert_called_once_with("uninstalled_at", "null")
        mock_is.maybe_single.assert_called_once()
        mock_maybe_single.execute.assert_called_once()


def test_get_installation_by_owner_not_found():
    mock_result = Mock()
    mock_result.data = None

    with patch(
        "services.supabase.installations.get_installation_by_owner.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_is = Mock()
        mock_maybe_single = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.is_.return_value = mock_is
        mock_is.maybe_single.return_value = mock_maybe_single
        mock_maybe_single.execute.return_value = mock_result

        result = get_installation_by_owner("nonexistent-owner")

        assert result is None


def test_get_installation_by_owner_exception_handling():
    with patch(
        "services.supabase.installations.get_installation_by_owner.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database connection error")

        result = get_installation_by_owner("test-owner")

        assert result is None


def test_get_installation_by_owner_filters_uninstalled():
    mock_result = Mock()
    mock_result.data = {
        "installation_id": 12345,
        "owner_name": "test-owner",
        "uninstalled_at": None,
    }

    with patch(
        "services.supabase.installations.get_installation_by_owner.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_is = Mock()
        mock_maybe_single = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.is_.return_value = mock_is
        mock_is.maybe_single.return_value = mock_maybe_single
        mock_maybe_single.execute.return_value = mock_result

        get_installation_by_owner("test-owner")

        mock_eq.is_.assert_called_once_with("uninstalled_at", "null")
