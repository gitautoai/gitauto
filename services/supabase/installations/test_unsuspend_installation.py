from unittest.mock import patch, MagicMock
import pytest
from requests.exceptions import HTTPError, JSONDecodeError, Timeout
from services.supabase.installations.unsuspend_installation import unsuspend_installation
from tests.constants import INSTALLATION_ID


def test_unsuspend_installation_success():
    """Test successful installation unsuspension."""
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
    """Test installation unsuspension with a different installation ID."""
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
    """Test error handling when an HTTPError occurs."""
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
    """Test error handling when a JSONDecodeError occurs."""
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
    """Test error handling when a generic exception occurs."""
    with patch("services.supabase.installations.unsuspend_installation.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Unexpected error")
        
        result = unsuspend_installation(INSTALLATION_ID)
        
        assert result is None


def test_unsuspend_installation_zero_installation_id():
    """Test installation unsuspension with installation_id = 0."""
    with patch("services.supabase.installations.unsuspend_installation.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()
        mock_execute = MagicMock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_execute
        
        result = unsuspend_installation(0)
        
        mock_update.eq.assert_called_once_with(column="installation_id", value=0)
        assert result is None


def test_unsuspend_installation_negative_installation_id():
    """Test installation unsuspension with a negative installation_id."""
    with patch("services.supabase.installations.unsuspend_installation.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()
        mock_execute = MagicMock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_execute
        
        result = unsuspend_installation(-1)
        
        mock_update.eq.assert_called_once_with(column="installation_id", value=-1)
        assert result is None


def test_unsuspend_installation_attribute_error():
    """Test error handling when an AttributeError occurs."""
    with patch("services.supabase.installations.unsuspend_installation.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.side_effect = AttributeError("'NoneType' object has no attribute 'execute'")
        
        result = unsuspend_installation(INSTALLATION_ID)
        
        assert result is None


def test_unsuspend_installation_key_error():
    """Test error handling when a KeyError occurs."""
    with patch("services.supabase.installations.unsuspend_installation.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.side_effect = KeyError("installation_id")
        
        result = unsuspend_installation(INSTALLATION_ID)
        
        assert result is None


def test_unsuspend_installation_type_error():
    """Test error handling when a TypeError occurs."""
    with patch("services.supabase.installations.unsuspend_installation.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.side_effect = TypeError("unsupported operand type(s)")
        
        result = unsuspend_installation(INSTALLATION_ID)
        
        assert result is None


def test_unsuspend_installation_data_structure():
    """Test the exact data structure passed to the update method."""
    with patch("services.supabase.installations.unsuspend_installation.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        
        unsuspend_installation(INSTALLATION_ID)
        
        expected_data = {"uninstalled_at": None, "uninstalled_by": None}
        mock_table.update.assert_called_once_with(json=expected_data)