from unittest.mock import patch, MagicMock
import pytest
from services.supabase.credits.check_grant_exists import check_grant_exists


@pytest.fixture
def mock_supabase():
    """Fixture to provide a mocked supabase client."""
    with patch("services.supabase.credits.check_grant_exists.supabase") as mock:
        yield mock


@pytest.fixture
def mock_query_result():
    """Fixture to provide a mocked query result."""
    mock_result = MagicMock()
    mock_result.data = []
    return mock_result


def test_check_grant_exists_returns_true_when_grants_exist(mock_supabase, mock_query_result):
    """Test that check_grant_exists returns True when grants exist for the owner."""
    # Arrange
    owner_id = 123456
    mock_query_result.data = [{"id": 1}, {"id": 2}]  # Multiple grants
    
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    mock_eq2.execute.return_value = mock_query_result
    
    # Act
    result = check_grant_exists(owner_id=owner_id)
    
    # Assert
    assert result is True
    mock_supabase.table.assert_called_once_with("credits")
    mock_table.select.assert_called_once_with("id")
    mock_select.eq.assert_called_once_with("owner_id", owner_id)
    mock_eq1.eq.assert_called_once_with("transaction_type", "grant")
    mock_eq2.execute.assert_called_once()


def test_check_grant_exists_returns_true_when_single_grant_exists(mock_supabase, mock_query_result):
    """Test that check_grant_exists returns True when a single grant exists."""
    # Arrange
    owner_id = 789012
    mock_query_result.data = [{"id": 42}]  # Single grant
    
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    mock_eq2.execute.return_value = mock_query_result
    
    # Act
    result = check_grant_exists(owner_id=owner_id)
    
    # Assert
    assert result is True


def test_check_grant_exists_returns_false_when_no_grants_exist(mock_supabase, mock_query_result):
    """Test that check_grant_exists returns False when no grants exist for the owner."""
    # Arrange
    owner_id = 345678
    mock_query_result.data = []  # No grants
    
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    mock_eq2.execute.return_value = mock_query_result
    
    # Act
    result = check_grant_exists(owner_id=owner_id)
    
    # Assert
    assert result is False
    mock_supabase.table.assert_called_once_with("credits")
    mock_table.select.assert_called_once_with("id")
    mock_select.eq.assert_called_once_with("owner_id", owner_id)
    mock_eq1.eq.assert_called_once_with("transaction_type", "grant")
    mock_eq2.execute.assert_called_once()


def test_check_grant_exists_handles_database_exception(mock_supabase):
    """Test that check_grant_exists handles database exceptions gracefully."""
    # Arrange
    owner_id = 999999
    mock_supabase.table.side_effect = Exception("Database connection error")
    
    # Act
    result = check_grant_exists(owner_id=owner_id)
    
    # Assert
    assert result is False  # Should return default_return_value due to @handle_exceptions
    mock_supabase.table.assert_called_once_with("credits")


@pytest.mark.parametrize("owner_id", [0, -1, 999999999, 1])
def test_check_grant_exists_with_various_owner_ids(mock_supabase, mock_query_result, owner_id):
    """Test that check_grant_exists works with various owner ID values."""
    # Arrange
    mock_query_result.data = []
    
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    mock_eq2.execute.return_value = mock_query_result
    
    # Act
    result = check_grant_exists(owner_id=owner_id)
    
    # Assert
    assert result is False
    mock_select.eq.assert_called_once_with("owner_id", owner_id)
