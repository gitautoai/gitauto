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
        None,
    )

    # Act
    result = get_installation_id(owner_id=TEST_OWNER_ID)

    # Assert
    assert result == expected_installation_id


def test_get_installation_id_returns_first_installation_when_multiple_found(
    mock_supabase_query,
):
    """Test that get_installation_id returns the first installation when multiple are found."""
    # Arrange
    first_installation_id = 12345
    second_installation_id = 67890
    mock_supabase_query.execute.return_value = (
        (
            None,
            [
                {"installation_id": first_installation_id},
                {"installation_id": second_installation_id},
            ],
        ),
        None,
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
    mock_supabase_query.execute.return_value = ((None, []), None)

    # Act
    result = get_installation_id(owner_id=TEST_OWNER_ID)

    # Assert
    assert result is None


def test_get_installation_id_returns_none_when_index_error_occurs(mock_supabase_query):
    """Test that get_installation_id returns None when IndexError occurs accessing data."""
    # Arrange - simulate empty result that would cause IndexError
    mock_supabase_query.execute.return_value = ((None, None), None)

    # Act
    result = get_installation_id(owner_id=TEST_OWNER_ID)

    # Assert
    assert result is None


def test_get_installation_id_returns_none_when_key_error_occurs(mock_supabase_query):
    """Test that get_installation_id returns None when KeyError occurs accessing installation_id."""
    # Arrange - simulate result without installation_id key
    mock_supabase_query.execute.return_value = (
        (None, [{"other_field": "value"}]),
        None,
    )

    # Act
    result = get_installation_id(owner_id=TEST_OWNER_ID)

    # Assert
    assert result is None


def test_get_installation_id_function_signature():
    """Test that get_installation_id has the correct function signature."""
    # Get function signature
    sig = inspect.signature(get_installation_id)

    # Assert parameter count and names
    assert len(sig.parameters) == 1
    assert "owner_id" in sig.parameters

    # Assert parameter type annotation
    owner_id_param = sig.parameters["owner_id"]
    assert owner_id_param.annotation is int
    assert sig.return_annotation is int


def test_get_installation_id_has_handle_exceptions_decorator():
    """Test that get_installation_id is decorated with handle_exceptions."""
    # Check if the function has the expected wrapper attributes from handle_exceptions
    assert hasattr(get_installation_id, "__wrapped__")

    # Verify the function name is preserved by the decorator
    assert get_installation_id.__name__ == "get_installation_id"

    # Verify the docstring is preserved
    assert (
        get_installation_id.__doc__ == "https://supabase.com/docs/reference/python/is"
    )
