# pylint: disable=unused-argument

from unittest.mock import patch, MagicMock, PropertyMock
import pytest
from services.supabase.credits.check_grant_exists import check_grant_exists


@pytest.fixture
def mock_supabase():
    """Fixture to provide a mocked supabase client."""
    with patch("services.supabase.credits.check_grant_exists.supabase") as mock:
        yield mock


@pytest.fixture
def mock_query_chain(mock_supabase):
    """Fixture to provide a complete mocked query chain."""
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()

    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2

    return {
        "table": mock_table,
        "select": mock_select,
        "eq1": mock_eq1,
        "eq2": mock_eq2,
    }


@pytest.fixture
def mock_query_result():
    """Fixture to provide a mocked query result."""
    mock_result = MagicMock()
    mock_result.data = []
    return mock_result


def test_check_grant_exists_returns_true_when_grants_exist(
    mock_supabase, mock_query_chain, mock_query_result
):
    """Test that check_grant_exists returns True when grants exist for the owner."""
    # Arrange
    owner_id = 123456
    mock_query_result.data = [{"id": 1}, {"id": 2}]  # Multiple grants
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert result is True
    mock_supabase.table.assert_called_once_with("credits")
    mock_query_chain["table"].select.assert_called_once_with("id")
    mock_query_chain["select"].eq.assert_called_once_with("owner_id", owner_id)
    mock_query_chain["eq1"].eq.assert_called_once_with("transaction_type", "grant")
    mock_query_chain["eq2"].execute.assert_called_once()


def test_check_grant_exists_returns_true_when_single_grant_exists(
    mock_supabase, mock_query_chain, mock_query_result
):
    """Test that check_grant_exists returns True when a single grant exists."""
    # Arrange
    owner_id = 789012
    mock_query_result.data = [{"id": 42}]  # Single grant
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert result is True


def test_check_grant_exists_returns_false_when_no_grants_exist(
    mock_supabase, mock_query_chain, mock_query_result
):
    """Test that check_grant_exists returns False when no grants exist for the owner."""
    # Arrange
    owner_id = 345678
    mock_query_result.data = []  # No grants
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert result is False
    mock_supabase.table.assert_called_once_with("credits")
    mock_query_chain["table"].select.assert_called_once_with("id")
    mock_query_chain["select"].eq.assert_called_once_with("owner_id", owner_id)
    mock_query_chain["eq1"].eq.assert_called_once_with("transaction_type", "grant")
    mock_query_chain["eq2"].execute.assert_called_once()


def test_check_grant_exists_handles_database_exception(mock_supabase):
    """Test that check_grant_exists handles database exceptions gracefully."""
    # Arrange
    owner_id = 999999
    mock_supabase.table.side_effect = Exception("Database connection error")

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert (
        result is False
    )  # Should return default_return_value due to @handle_exceptions
    mock_supabase.table.assert_called_once_with("credits")


@pytest.mark.parametrize("owner_id", [0, -1, 999999999, 1])
def test_check_grant_exists_with_various_owner_ids(
    mock_supabase, mock_query_chain, mock_query_result, owner_id
):
    """Test that check_grant_exists works with various owner ID values."""
    # Arrange
    mock_query_result.data = []
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert result is False


def test_check_grant_exists_handles_query_chain_exception(mock_supabase):
    """Test that check_grant_exists handles exceptions in the query chain."""
    # Arrange
    owner_id = 555555
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    mock_table.select.side_effect = Exception("Query error")

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert (
        result is False
    )  # Should return default_return_value due to @handle_exceptions
    mock_supabase.table.assert_called_once_with("credits")
    mock_table.select.assert_called_once_with("id")


def test_check_grant_exists_handles_execute_exception(mock_supabase, mock_query_chain):
    """Test that check_grant_exists handles exceptions during execute."""
    # Arrange
    owner_id = 777777
    mock_query_chain["eq2"].execute.side_effect = Exception("Execute error")

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert (
        result is False
    )  # Should return default_return_value due to @handle_exceptions
    mock_query_chain["eq2"].execute.assert_called_once()


def test_check_grant_exists_handles_result_data_access_exception(
    mock_supabase, mock_query_chain
):
    """Test that check_grant_exists handles exceptions when accessing result.data."""
    # Arrange
    owner_id = 888888
    mock_query_result = MagicMock()
    # Make accessing .data raise an exception
    type(mock_query_result).data = PropertyMock(
        side_effect=AttributeError("No data attribute")
    )
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert (
        result is False
    )  # Should return default_return_value due to @handle_exceptions


def test_check_grant_exists_with_none_data(mock_supabase, mock_query_chain):
    """Test that check_grant_exists handles None data gracefully."""
    # Arrange
    owner_id = 111111
    mock_query_result = MagicMock()
    mock_query_result.data = None
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert (
        result is False
    )  # len(None) should raise TypeError, handled by @handle_exceptions


def test_check_grant_exists_with_empty_list_data(mock_supabase, mock_query_chain):
    """Test that check_grant_exists correctly handles empty list data."""
    # Arrange
    owner_id = 222222
    mock_query_result = MagicMock()
    mock_query_result.data = []
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert result is False
    assert len(mock_query_result.data) == 0


def test_check_grant_exists_with_large_result_set(mock_supabase, mock_query_chain):
    """Test that check_grant_exists handles large result sets correctly."""
    # Arrange
    owner_id = 333333
    mock_query_result = MagicMock()
    # Create a large list of grant records
    mock_query_result.data = [{"id": i} for i in range(100)]
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert result is True
    assert len(mock_query_result.data) == 100


def test_check_grant_exists_verifies_correct_table_name(
    mock_supabase, mock_query_chain, mock_query_result
):
    """Test that check_grant_exists queries the correct table name."""
    # Arrange
    owner_id = 444444
    mock_query_result.data = []
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    check_grant_exists(owner_id=owner_id)

    # Assert
    mock_supabase.table.assert_called_once_with("credits")


def test_check_grant_exists_verifies_correct_select_field(
    mock_supabase, mock_query_chain, mock_query_result
):
    """Test that check_grant_exists selects the correct field."""
    # Arrange
    owner_id = 555555
    mock_query_result.data = []
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    check_grant_exists(owner_id=owner_id)

    # Assert
    mock_query_chain["table"].select.assert_called_once_with("id")


def test_check_grant_exists_verifies_correct_owner_id_filter(
    mock_supabase, mock_query_chain, mock_query_result
):
    """Test that check_grant_exists filters by the correct owner_id."""
    # Arrange
    owner_id = 666666
    mock_query_result.data = []
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    check_grant_exists(owner_id=owner_id)

    # Assert
    mock_query_chain["select"].eq.assert_called_once_with("owner_id", owner_id)


def test_check_grant_exists_verifies_correct_transaction_type_filter(
    mock_supabase, mock_query_chain, mock_query_result
):
    """Test that check_grant_exists filters by the correct transaction_type."""
    # Arrange
    owner_id = 777777
    mock_query_result.data = []
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    check_grant_exists(owner_id=owner_id)

    # Assert
    mock_query_chain["eq1"].eq.assert_called_once_with("transaction_type", "grant")


def test_check_grant_exists_handles_type_error_on_len(mock_supabase, mock_query_chain):
    """Test that check_grant_exists handles TypeError when calling len() on result.data."""
    # Arrange
    owner_id = 888888
    mock_query_result = MagicMock()
    mock_query_result.data = 42  # This will cause TypeError when len() is called
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert (
        result is False
    )  # Should return default_return_value due to @handle_exceptions


def test_check_grant_exists_handles_attribute_error_on_result(
    mock_supabase, mock_query_chain
):
    """Test that check_grant_exists handles AttributeError when result doesn't have data attribute."""
    # Arrange
    owner_id = 999999
    mock_query_result = MagicMock()
    del mock_query_result.data  # Remove the data attribute
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert (
        result is False
    )  # Should return default_return_value due to @handle_exceptions


@pytest.mark.parametrize(
    "data_content,expected_result",
    [
        ([{"id": 1}], True),
        ([{"id": 1}, {"id": 2}], True),
        ([{"id": 1}, {"id": 2}, {"id": 3}], True),
        ([], False),
    ],
)
def test_check_grant_exists_with_different_data_sizes(
    mock_supabase, mock_query_chain, data_content, expected_result
):
    """Test that check_grant_exists correctly evaluates different data sizes."""
    # Arrange
    owner_id = 123456
    mock_query_result = MagicMock()
    mock_query_result.data = data_content
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert result is expected_result


def test_check_grant_exists_handles_key_error_exception(
    mock_supabase, mock_query_chain
):
    """Test that check_grant_exists handles KeyError exceptions gracefully."""
    # Arrange
    owner_id = 101010
    mock_query_chain["select"].eq.side_effect = KeyError("Missing key")

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert (
        result is False
    )  # Should return default_return_value due to @handle_exceptions


def test_check_grant_exists_handles_value_error_exception(
    mock_supabase, mock_query_chain
):
    """Test that check_grant_exists handles ValueError exceptions gracefully."""
    # Arrange
    owner_id = 121212
    mock_query_chain["eq1"].eq.side_effect = ValueError("Invalid value")

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert (
        result is False
    )  # Should return default_return_value due to @handle_exceptions


def test_check_grant_exists_return_type_is_boolean(
    mock_supabase, mock_query_chain, mock_query_result
):
    """Test that check_grant_exists always returns a boolean value."""
    # Arrange
    owner_id = 131313
    mock_query_result.data = [{"id": 1}]
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert isinstance(result, bool)
    assert result is True


def test_check_grant_exists_return_type_is_boolean_when_false(
    mock_supabase, mock_query_chain, mock_query_result
):
    """Test that check_grant_exists returns boolean False when no grants exist."""
    # Arrange
    owner_id = 141414
    mock_query_result.data = []
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert isinstance(result, bool)
    assert result is False


def test_check_grant_exists_with_complex_data_structure(
    mock_supabase, mock_query_chain
):
    """Test that check_grant_exists works with complex data structures in result."""
    # Arrange
    owner_id = 151515
    mock_query_result = MagicMock()
    mock_query_result.data = [
        {"id": 1, "owner_id": owner_id, "transaction_type": "grant", "amount": 12},
        {"id": 2, "owner_id": owner_id, "transaction_type": "grant", "amount": 12},
    ]
    mock_query_chain["eq2"].execute.return_value = mock_query_result

    # Act
    result = check_grant_exists(owner_id=owner_id)

    # Assert
    assert result is True
