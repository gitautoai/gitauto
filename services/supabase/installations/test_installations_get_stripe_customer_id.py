from unittest.mock import patch, MagicMock

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
        [None, [{"owners": {"stripe_customer_id": expected_customer_id}}]], None
    )

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result == expected_customer_id


def test_get_stripe_customer_id_returns_none_when_no_data_found(mock_supabase_query):
    """Test that get_stripe_customer_id returns None when no data is found."""
    # Arrange
    mock_supabase_query.execute.return_value = ([None, []], None)

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result is None


def test_get_stripe_customer_id_returns_none_when_data_is_none(mock_supabase_query):
    """Test that get_stripe_customer_id returns None when data[1] is None."""
    # Arrange
    mock_supabase_query.execute.return_value = ([None, None], None)

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result is None


def test_get_stripe_customer_id_returns_none_when_owners_key_missing(mock_supabase_query):
    """Test that get_stripe_customer_id returns None when owners key is missing."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        [None, [{"other_field": "value"}]], None
    )

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result is None


def test_get_stripe_customer_id_returns_none_when_stripe_customer_id_is_none(mock_supabase_query):
    """Test that get_stripe_customer_id returns None when stripe_customer_id is None."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        [None, [{"owners": {"stripe_customer_id": None}}]], None
    )

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result is None


def test_get_stripe_customer_id_returns_none_when_stripe_customer_id_is_empty_string(mock_supabase_query):
    """Test that get_stripe_customer_id returns None when stripe_customer_id is empty string."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        [None, [{"owners": {"stripe_customer_id": ""}}]], None
    )

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result is None


def test_get_stripe_customer_id_returns_none_when_exception_occurs(mock_supabase_query):
    """Test that get_stripe_customer_id returns None when an exception occurs."""
    # Arrange
    mock_supabase_query.execute.side_effect = Exception("Database error")

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result is None


def test_get_stripe_customer_id_calls_correct_supabase_methods():
    """Test that get_stripe_customer_id calls the correct Supabase methods with correct parameters."""
    with patch("services.supabase.installations.get_stripe_customer_id.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = ([None, []], None)

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
        [None, [{"owners": {"stripe_customer_id": expected_customer_id}}]], None
    )

    # Act
    result = get_stripe_customer_id(installation_id=installation_id)

    # Assert
    assert result == expected_customer_id