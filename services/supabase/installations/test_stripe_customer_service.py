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


def test_get_stripe_customer_id_returns_none_when_exception_occurs(mock_supabase_query):
    """Test that get_stripe_customer_id returns None when an exception occurs."""
    # Arrange
    mock_supabase_query.execute.side_effect = Exception("Database error")

    # Act
    result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

    # Assert
    assert result is None