from unittest.mock import patch, MagicMock
import pytest
from requests.exceptions import HTTPError, JSONDecodeError, Timeout
from services.supabase.installations.unsuspend_installation import unsuspend_installation
from tests.constants import INSTALLATION_ID


def test_unsuspend_installation_success():
    with patch("services.supabase.installations.unsuspend_installation.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()
        mock_execute = MagicMock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_execute
        
        result = unsuspend_installation(INSTALLATION_ID)
        
        mock_supabase.table.assert_called_once_with(table_name="installations")
        mock_table.update.assert_called_once_with(json={
            "uninstalled_at": None,
            "uninstalled_by": None,
        })
        mock_update.eq.assert_called_once_with(column="installation_id", value=INSTALLATION_ID)
        mock_eq.execute.assert_called_once()
        assert result is None


def test_unsuspend_installation_with_different_installation_id():
    test_installation_id = 12345
    with patch("services.supabase.installations.unsuspend_installation.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()
        mock_execute = MagicMock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_execute
        
        result = unsuspend_installation(test_installation_id)
        
        mock_update.eq.assert_called_once_with(column="installation_id", value=test_installation_id)
        assert result is None


def test_unsuspend_installation_http_error():
    with patch("services.supabase.installations.unsuspend_installation.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.side_effect = HTTPError("Database error")
        
        result = unsuspend_installation(INSTALLATION_ID)
        
        assert result is None


def test_unsuspend_installation_json_decode_error():
    with patch("services.supabase.installations.unsuspend_installation.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.side_effect = JSONDecodeError("Invalid JSON", "{", 0)
        
        result = unsuspend_installation(INSTALLATION_ID)
        
        assert result is None


def test_unsuspend_installation_generic_exception():
    with patch("services.supabase.installations.unsuspend_installation.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Unexpected error")
        
        result = unsuspend_installation(INSTALLATION_ID)
        
        assert result is None
