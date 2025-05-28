from unittest.mock import Mock, patch
import pytest
from tests.constants import INSTALLATION_ID
from services.supabase.installations.is_installation_valid import is_installation_valid


def test_is_installation_valid_with_valid_installation():
    mock_response = Mock()
    mock_response.data = [{"uninstalled_at": None}]
    
    with patch("services.supabase.installations.is_installation_valid.supabase") as mock_supabase:
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_response
        
        result = is_installation_valid(INSTALLATION_ID)
        
        assert result is True
        mock_supabase.table.assert_called_once_with(table_name="installations")
        mock_table.select.assert_called_once_with("uninstalled_at")
        mock_select.eq.assert_called_once_with(column="installation_id", value=INSTALLATION_ID)
        mock_eq.execute.assert_called_once()


def test_is_installation_valid_with_uninstalled_installation():
    mock_response = Mock()
    mock_response.data = [{"uninstalled_at": "2023-01-01T00:00:00Z"}]
    
    with patch("services.supabase.installations.is_installation_valid.supabase") as mock_supabase:
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_response
        
        result = is_installation_valid(INSTALLATION_ID)
        
        assert result is False
        mock_supabase.table.assert_called_once_with(table_name="installations")
        mock_table.select.assert_called_once_with("uninstalled_at")
        mock_select.eq.assert_called_once_with(column="installation_id", value=INSTALLATION_ID)
        mock_eq.execute.assert_called_once()


def test_is_installation_valid_with_no_data():
    mock_response = Mock()
    mock_response.data = []
    
    with patch("services.supabase.installations.is_installation_valid.supabase") as mock_supabase:
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_response
        
        result = is_installation_valid(INSTALLATION_ID)
        
        assert result is False
        mock_supabase.table.assert_called_once_with(table_name="installations")
        mock_table.select.assert_called_once_with("uninstalled_at")
        mock_select.eq.assert_called_once_with(column="installation_id", value=INSTALLATION_ID)
        mock_eq.execute.assert_called_once()


def test_is_installation_valid_with_none_data():
    mock_response = Mock()
    mock_response.data = None
    
    with patch("services.supabase.installations.is_installation_valid.supabase") as mock_supabase:
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_response
        
        result = is_installation_valid(INSTALLATION_ID)
        
        assert result is False
        mock_supabase.table.assert_called_once_with(table_name="installations")
        mock_table.select.assert_called_once_with("uninstalled_at")
        mock_select.eq.assert_called_once_with(column="installation_id", value=INSTALLATION_ID)
        mock_eq.execute.assert_called_once()


def test_is_installation_valid_with_exception():
    with patch("services.supabase.installations.is_installation_valid.supabase") as mock_supabase:
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.side_effect = Exception("Database error")
        
        result = is_installation_valid(INSTALLATION_ID)
        
        assert result is False
        mock_supabase.table.assert_called_once_with(table_name="installations")
        mock_table.select.assert_called_once_with("uninstalled_at")
        mock_select.eq.assert_called_once_with(column="installation_id", value=INSTALLATION_ID)
        mock_eq.execute.assert_called_once()


def test_is_installation_valid_with_zero_installation_id():
    mock_response = Mock()
    mock_response.data = [{"uninstalled_at": None}]
    
    with patch("services.supabase.installations.is_installation_valid.supabase") as mock_supabase:
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_response
        
        result = is_installation_valid(0)
        
        assert result is True
        mock_supabase.table.assert_called_once_with(table_name="installations")
        mock_table.select.assert_called_once_with("uninstalled_at")
        mock_select.eq.assert_called_once_with(column="installation_id", value=0)
        mock_eq.execute.assert_called_once()


def test_is_installation_valid_with_negative_installation_id():
    mock_response = Mock()
    mock_response.data = []
    
    with patch("services.supabase.installations.is_installation_valid.supabase") as mock_supabase:
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_response
        
        result = is_installation_valid(-1)
        
        assert result is False
        mock_supabase.table.assert_called_once_with(table_name="installations")
        mock_table.select.assert_called_once_with("uninstalled_at")
        mock_select.eq.assert_called_once_with(column="installation_id", value=-1)
        mock_eq.execute.assert_called_once()
