from unittest.mock import patch, MagicMock
import inspect

import pytest

from config import TEST_INSTALLATION_ID
from services.supabase.installations.get_stripe_customer_id import get_stripe_customer_id


@pytest.fixture
def mock_supabase_query():
    """Fixture to provide a mocked Supabase query chain."""
    with patch("services.supabase.installations.get_stripe_customer_id.supabase") as mock:
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()

        mock.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq

        yield mock_eq


def test_get_stripe_customer_id_returns_customer_id_when_found(mock_supabase_query):
    """Test that get_stripe_customer_id returns the customer ID when found."""
    # Arrange
    expected_customer_id = "cus_test123456"
    mock_supabase_query.execute.return_value = (
        None, [{"owners": {"stripe_customer_id": expected_customer_id}}]
    )

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result == expected_customer_id


def test_get_stripe_customer_id_returns_none_when_no_data_found(mock_supabase_query):
    """Test that get_stripe_customer_id returns None when no data is found."""
    # Arrange
    mock_supabase_query.execute.return_value = (None, [])

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result is None


def test_get_stripe_customer_id_returns_none_when_data_is_none(mock_supabase_query):
    """Test that get_stripe_customer_id returns None when data[1] is None."""
    # Arrange
    mock_supabase_query.execute.return_value = (None, None)

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result is None


def test_get_stripe_customer_id_returns_none_when_data_is_empty(mock_supabase_query):
    """Test that get_stripe_customer_id returns None when data is empty."""
    # Arrange
    mock_supabase_query.execute.return_value = None

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result is None


def test_get_stripe_customer_id_returns_none_when_owners_key_missing(mock_supabase_query):
    """Test that get_stripe_customer_id returns None when owners key is missing."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        None, [{"other_field": "value"}]
    )

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result is None


def test_get_stripe_customer_id_returns_none_when_owners_is_none(mock_supabase_query):
    """Test that get_stripe_customer_id returns None when owners is None."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        None, [{"owners": None}]
    )

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result is None


def test_get_stripe_customer_id_returns_none_when_stripe_customer_id_missing(mock_supabase_query):
    """Test that get_stripe_customer_id returns None when stripe_customer_id key is missing."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        None, [{"owners": {"other_field": "value"}}]
    )

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result is None


def test_get_stripe_customer_id_returns_none_when_stripe_customer_id_is_none(mock_supabase_query):
    """Test that get_stripe_customer_id returns None when stripe_customer_id is None."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        None, [{"owners": {"stripe_customer_id": None}}]
    )

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result is None


def test_get_stripe_customer_id_returns_none_when_stripe_customer_id_is_empty_string(mock_supabase_query):
    """Test that get_stripe_customer_id returns None when stripe_customer_id is empty string."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        None, [{"owners": {"stripe_customer_id": ""}}]
    )

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result is None


def test_get_stripe_customer_id_returns_none_when_stripe_customer_id_is_not_string(mock_supabase_query):
    """Test that get_stripe_customer_id returns None when stripe_customer_id is not a string."""
    # Arrange - test with various non-string types
    non_string_values = [123, True, [], {}, 45.67]
    
    for non_string_value in non_string_values:
        mock_supabase_query.execute.return_value = (
            None, [{"owners": {"stripe_customer_id": non_string_value}}]
        )

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result is None


def test_get_stripe_customer_id_returns_first_result_when_multiple_found(mock_supabase_query):
    """Test that get_stripe_customer_id returns the first result when multiple are found."""
    # Arrange
    first_customer_id = "cus_first123"
    second_customer_id = "cus_second456"
    mock_supabase_query.execute.return_value = (
        None, [
            {"owners": {"stripe_customer_id": first_customer_id}},
            {"owners": {"stripe_customer_id": second_customer_id}},
        ]
    )

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result == first_customer_id


def test_get_stripe_customer_id_returns_none_when_exception_occurs(mock_supabase_query):
    """Test that get_stripe_customer_id returns None when an exception occurs."""
    # Arrange
    mock_supabase_query.execute.side_effect = Exception("Database error")

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result is None


def test_get_stripe_customer_id_calls_correct_supabase_methods(mock_supabase_query):
    """Test that get_stripe_customer_id calls the correct Supabase methods with correct parameters."""
    # Arrange
    mock_supabase_query.execute.return_value = (None, [])

    with patch("services.supabase.installations.get_stripe_customer_id.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = (None, [])

        # Act
        get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        mock_supabase.table.assert_called_once_with(table_name="installations")
        mock_table.select.assert_called_once_with("owner_id, owners(stripe_customer_id)")
        mock_select.eq.assert_called_once_with(column="installation_id", value=TEST_INSTALLATION_ID)
        mock_eq.execute.assert_called_once()


@pytest.mark.parametrize(
    "installation_id,expected_customer_id",
    [
        (12345, "cus_test12345"),
        (67890, "cus_test67890"),
        (999999999, "cus_test999999999"),
        (1, "cus_test1"),
    ],
)
def test_get_stripe_customer_id_with_various_installation_ids(
    mock_supabase_query, installation_id, expected_customer_id
):
    """Test get_stripe_customer_id with various installation IDs using parametrize."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        None, [{"owners": {"stripe_customer_id": expected_customer_id}}]
    )

    # Act
    result = get_stripe_customer_id(installation_id=installation_id)

    # Assert
    assert result == expected_customer_id


def test_get_stripe_customer_id_with_valid_stripe_customer_ids(mock_supabase_query):
    """Test get_stripe_customer_id with various valid Stripe customer ID formats."""
    valid_customer_ids = [
        "cus_1234567890",
        "cus_abcdefghij",
        "cus_MixedCase123",
        "cus_with_underscores_123",
        "cus_" + "a" * 50,  # Long customer ID
    ]

    for customer_id in valid_customer_ids:
        # Arrange
        mock_supabase_query.execute.return_value = (
            None, [{"owners": {"stripe_customer_id": customer_id}}]
        )

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result == customer_id


def test_get_stripe_customer_id_function_signature():
    """Test that get_stripe_customer_id has the correct function signature."""
    # Get function signature
    sig = inspect.signature(get_stripe_customer_id)

    # Assert parameter count and names
    assert len(sig.parameters) == 1
    assert "installation_id" in sig.parameters

    # Assert parameter type annotation
    installation_id_param = sig.parameters["installation_id"]
    assert installation_id_param.annotation is int


def test_get_stripe_customer_id_has_handle_exceptions_decorator():
    """Test that get_stripe_customer_id is decorated with handle_exceptions."""
    # Check if the function has the expected wrapper attributes from handle_exceptions
    assert hasattr(get_stripe_customer_id, "__wrapped__")

    # Verify the function name is preserved by the decorator
    assert get_stripe_customer_id.__name__ == "get_stripe_customer_id"


def test_get_stripe_customer_id_decorator_behavior():
    """Test that the handle_exceptions decorator is properly applied."""
    # Test that the function has the decorator applied by checking it returns None on exception
    with patch("services.supabase.installations.get_stripe_customer_id.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Unexpected error")

        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)
        assert result is None


def test_get_stripe_customer_id_with_malformed_data_structure(mock_supabase_query):
    """Test that get_stripe_customer_id handles malformed data gracefully."""
    # Arrange - simulate various malformed data structures
    malformed_cases = [
        (None, {}),  # dict instead of list
        ("wrong_structure", None),  # wrong tuple structure
        (None, [{}]),  # empty dict in list
        (None, [{"owners": {}}]),  # empty owners dict
    ]

    for malformed_data in malformed_cases:
        mock_supabase_query.execute.return_value = malformed_data

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result is None