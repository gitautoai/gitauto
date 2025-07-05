from unittest.mock import patch, MagicMock

import pytest

from config import TEST_OWNER_ID, TEST_INSTALLATION_ID
from services.supabase.installations.get_installation_id import get_installation_id


@pytest.fixture
def mock_supabase_query():
    """Fixture to provide a mocked Supabase query chain."""
    with patch("services.supabase.installations.get_installation_id.supabase") as mock:
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_is = MagicMock()
        
        mock.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.is_.return_value = mock_is
        
        yield mock_is


def test_get_installation_id_returns_installation_id_when_found(mock_supabase_query):
    """Test that get_installation_id returns the installation ID when found."""
    # Arrange
    expected_installation_id = TEST_INSTALLATION_ID
    mock_supabase_query.execute.return_value = (
        None,
        [{"installation_id": expected_installation_id}]
    )
    
    # Act
    result = get_installation_id(owner_id=TEST_OWNER_ID)
    
    # Assert
    assert result == expected_installation_id


def test_get_installation_id_queries_correct_table(mock_supabase_query):
    """Test that get_installation_id queries the installations table."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        None,
        [{"installation_id": TEST_INSTALLATION_ID}]
    )
    
    # Act
    get_installation_id(owner_id=TEST_OWNER_ID)
    
    # Assert
    from services.supabase.installations.get_installation_id import supabase
    supabase.table.assert_called_once_with(table_name="installations")


def test_get_installation_id_selects_installation_id_column(mock_supabase_query):
    """Test that get_installation_id selects the installation_id column."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        None,
        [{"installation_id": TEST_INSTALLATION_ID}]
    )
    
    # Act
    get_installation_id(owner_id=TEST_OWNER_ID)
    
    # Assert
    from services.supabase.installations.get_installation_id import supabase
    supabase.table.return_value.select.assert_called_once_with("installation_id")


def test_get_installation_id_filters_by_owner_id(mock_supabase_query):
    """Test that get_installation_id filters by the provided owner_id."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        None,
        [{"installation_id": TEST_INSTALLATION_ID}]
    )
    
    # Act
    get_installation_id(owner_id=TEST_OWNER_ID)
    
    # Assert
    from services.supabase.installations.get_installation_id import supabase
    supabase.table.return_value.select.return_value.eq.assert_called_once_with(
        column="owner_id", value=TEST_OWNER_ID
    )


def test_get_installation_id_filters_not_uninstalled(mock_supabase_query):
    """Test that get_installation_id filters for non-uninstalled installations."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        None,
        [{"installation_id": TEST_INSTALLATION_ID}]
    )
    
    # Act
    get_installation_id(owner_id=TEST_OWNER_ID)
    
    # Assert
    from services.supabase.installations.get_installation_id import supabase
    supabase.table.return_value.select.return_value.eq.return_value.is_.assert_called_once_with(
        column="uninstalled_at", value="null"
    )


def test_get_installation_id_returns_first_installation_when_multiple_found(mock_supabase_query):
    """Test that get_installation_id returns the first installation when multiple are found."""
    # Arrange
    first_installation_id = 12345
    second_installation_id = 67890
    mock_supabase_query.execute.return_value = (
        None,
        [
            {"installation_id": first_installation_id},
            {"installation_id": second_installation_id}
        ]
    )
    
    # Act
    result = get_installation_id(owner_id=TEST_OWNER_ID)
    
    # Assert
    assert result == first_installation_id


def test_get_installation_id_returns_none_when_exception_occurs(mock_supabase_query):
    """Test that get_installation_id returns None when an exception occurs."""
    # Arrange
    mock_supabase_query.execute.side_effect = Exception("Database error")
    
    # Act
    result = get_installation_id(owner_id=TEST_OWNER_ID)
    
    # Assert
    assert result is None


def test_get_installation_id_returns_none_when_no_data_found(mock_supabase_query):
    """Test that get_installation_id returns None when no data is found."""
    # Arrange
    mock_supabase_query.execute.return_value = (None, [])
    
    # Act
    result = get_installation_id(owner_id=TEST_OWNER_ID)
    
    # Assert
    assert result is None
