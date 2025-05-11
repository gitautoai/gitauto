from unittest import mock
import pytest

from config import TEST_OWNER_ID
from services.supabase.owners.get_owner import get_owner


def test_get_owner_success():
    # Arrange
    mock_owner_data = {
        "created_at": "2024-08-13 07:22:26.940858+00",
        "owner_id": TEST_OWNER_ID,
        "stripe_customer_id": "cus_QeYAAwQEjB9DJp",
        "created_by": None,
        "owner_name": "gitautoai",
        "org_rules": "",
        "owner_type": "Organization",
        "updated_by": "",
        "updated_at": "2025-03-03 04:12:21.668749+00"
    }
    
    mock_result = mock.MagicMock()
    mock_result.data = [mock_owner_data]
    
    mock_table = mock.MagicMock()
    mock_table.select.return_value.eq.return_value.execute.return_value = mock_result
    
    # Act
    with mock.patch("services.supabase.owners.get_owner.supabase") as mock_supabase:
        mock_supabase.table.return_value = mock_table
        result = get_owner(owner_id=TEST_OWNER_ID)
    
    # Assert
    mock_supabase.table.assert_called_once_with("owners")
    mock_table.select.assert_called_once_with("*")
    mock_table.select.return_value.eq.assert_called_once_with("owner_id", TEST_OWNER_ID)
    mock_table.select.return_value.eq.return_value.execute.assert_called_once()
    assert result == mock_owner_data


def test_get_owner_not_found():
    # Arrange
    mock_result = mock.MagicMock()
    mock_result.data = []
    
    mock_table = mock.MagicMock()
    mock_table.select.return_value.eq.return_value.execute.return_value = mock_result
    
    # Act
    with mock.patch("services.supabase.owners.get_owner.supabase") as mock_supabase:
        mock_supabase.table.return_value = mock_table
        result = get_owner(owner_id=TEST_OWNER_ID)
    
    # Assert
    mock_supabase.table.assert_called_once_with("owners")
    mock_table.select.assert_called_once_with("*")
    mock_table.select.return_value.eq.assert_called_once_with("owner_id", TEST_OWNER_ID)
    mock_table.select.return_value.eq.return_value.execute.assert_called_once()
    assert result is None


def test_get_owner_exception():
    # Arrange
    mock_table = mock.MagicMock()
    mock_table.select.return_value.eq.return_value.execute.side_effect = Exception("Database error")
    
    # Act
    with mock.patch("services.supabase.owners.get_owner.supabase") as mock_supabase:
        mock_supabase.table.return_value = mock_table
        result = get_owner(owner_id=TEST_OWNER_ID)
    
    # Assert
    mock_supabase.table.assert_called_once_with("owners")
    mock_table.select.assert_called_once_with("*")
    mock_table.select.return_value.eq.assert_called_once_with("owner_id", TEST_OWNER_ID)
    mock_table.select.return_value.eq.return_value.execute.assert_called_once()
    assert result is None