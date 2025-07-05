from unittest.mock import patch, MagicMock
import inspect

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
        (None, [{"installation_id": expected_installation_id}]),
        None
    )
    
    # Act
    result = get_installation_id(owner_id=TEST_OWNER_ID)
    
    # Assert
    assert result == expected_installation_id


def test_get_installation_id_queries_correct_table(mock_supabase_query):
    """Test that get_installation_id queries the installations table."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        (None, [{"installation_id": TEST_INSTALLATION_ID}]),
        None
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
        (None, [{"installation_id": TEST_INSTALLATION_ID}]),
        None
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
        (None, [{"installation_id": TEST_INSTALLATION_ID}]),
        None
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
        (None, [{"installation_id": TEST_INSTALLATION_ID}]),
        None
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
        (None, [
            {"installation_id": first_installation_id},
            {"installation_id": second_installation_id}
        ]),
        None
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
    mock_supabase_query.execute.return_value = (
        (None, []),
        None
    )
    
    # Act
    result = get_installation_id(owner_id=TEST_OWNER_ID)
    
    # Assert
    assert result is None


def test_get_installation_id_returns_none_when_index_error_occurs(mock_supabase_query):
    """Test that get_installation_id returns None when IndexError occurs accessing data."""
    # Arrange - simulate empty result that would cause IndexError
    mock_supabase_query.execute.return_value = (
        (None, None),
        None
    )
    
    # Act
    result = get_installation_id(owner_id=TEST_OWNER_ID)
    
    # Assert
    assert result is None


def test_get_installation_id_returns_none_when_key_error_occurs(mock_supabase_query):
    """Test that get_installation_id returns None when KeyError occurs accessing installation_id."""
    # Arrange - simulate result without installation_id key
    mock_supabase_query.execute.return_value = (
        (None, [{"other_field": "value"}]),
        None
    )
    
    # Act
    result = get_installation_id(owner_id=TEST_OWNER_ID)
    
    # Assert
    assert result is None


@pytest.mark.parametrize("owner_id_value", [
    1,
    999999999,
    TEST_OWNER_ID,
    0,
    -1,
])
def test_get_installation_id_with_various_owner_ids(mock_supabase_query, owner_id_value):
    """Test that get_installation_id works with various owner ID values."""
    # Arrange
    expected_installation_id = TEST_INSTALLATION_ID
    mock_supabase_query.execute.return_value = (
        (None, [{"installation_id": expected_installation_id}]),
        None
    )
    
    # Act
    result = get_installation_id(owner_id=owner_id_value)
    
    # Assert
    assert result == expected_installation_id


def test_get_installation_id_function_signature():
    """Test that get_installation_id has the correct function signature."""
    # Get function signature
    sig = inspect.signature(get_installation_id)
    
    # Assert parameter count and names
    assert len(sig.parameters) == 1
    assert "owner_id" in sig.parameters
    
    # Assert parameter type annotation
    owner_id_param = sig.parameters["owner_id"]
    assert owner_id_param.annotation == int
    assert sig.return_annotation == int


def test_get_installation_id_has_handle_exceptions_decorator():
    """Test that get_installation_id is decorated with handle_exceptions."""
    # Check if the function has the expected wrapper attributes from handle_exceptions
    assert hasattr(get_installation_id, "__wrapped__")
    
    # Verify the function name is preserved by the decorator
    assert get_installation_id.__name__ == "get_installation_id"
    
    # Verify the docstring is preserved
    assert get_installation_id.__doc__ == "https://supabase.com/docs/reference/python/is"