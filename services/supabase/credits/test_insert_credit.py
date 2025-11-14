# pylint: disable=unused-argument

from unittest.mock import patch, MagicMock
import pytest
from services.supabase.credits.insert_credit import insert_credit


@pytest.fixture
def mock_supabase():
    """Fixture to provide a mocked supabase client."""
    with patch("services.supabase.credits.insert_credit.supabase") as mock:
        yield mock


@pytest.fixture
def mock_credit_amounts():
    """Fixture to provide mocked credit amounts configuration."""
    return {
        "usage": -4,
        "grant": 12,
        "bonus": 5,
        "refund": 4,
    }


@pytest.fixture
def mock_query_chain(mock_supabase):
    """Fixture to provide a complete mocked query chain."""
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()

    mock_supabase.table.return_value = mock_table
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_execute

    return {
        "table": mock_table,
        "insert": mock_insert,
        "execute": mock_execute,
    }


def test_insert_credit_success_without_usage_id(mock_supabase, mock_query_chain):
    """Test successful credit insertion without usage_id."""
    # Arrange
    owner_id = 123456
    transaction_type = "grant"

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD", {"grant": 12}
    ):
        # Act
        result = insert_credit(owner_id=owner_id, transaction_type=transaction_type)

        # Assert
        assert result is None  # Function returns None on success
        mock_supabase.table.assert_called_once_with("credits")
        mock_query_chain["table"].insert.assert_called_once_with(
            {
                "owner_id": owner_id,
                "amount_usd": 12,
                "transaction_type": transaction_type,
            }
        )
        mock_query_chain["insert"].execute.assert_called_once()


def test_insert_credit_success_with_usage_id(mock_supabase, mock_query_chain):
    """Test successful credit insertion with usage_id."""
    # Arrange
    owner_id = 789012
    transaction_type = "usage"
    usage_id = 456

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD", {"usage": -4}
    ):
        # Act
        result = insert_credit(
            owner_id=owner_id, transaction_type=transaction_type, usage_id=usage_id
        )

        # Assert
        assert result is None  # Function returns None on success
        mock_supabase.table.assert_called_once_with("credits")
        mock_query_chain["table"].insert.assert_called_once_with(
            {
                "owner_id": owner_id,
                "amount_usd": -4,
                "transaction_type": transaction_type,
                "usage_id": usage_id,
            }
        )
        mock_query_chain["insert"].execute.assert_called_once()


def test_insert_credit_with_none_usage_id(mock_supabase, mock_query_chain):
    """Test credit insertion with explicitly None usage_id."""
    # Arrange
    owner_id = 345678
    transaction_type = "bonus"
    usage_id = None

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD", {"bonus": 5}
    ):
        # Act
        result = insert_credit(
            owner_id=owner_id, transaction_type=transaction_type, usage_id=usage_id
        )

        # Assert
        assert result is None
        mock_query_chain["table"].insert.assert_called_once_with(
            {
                "owner_id": owner_id,
                "amount_usd": 5,
                "transaction_type": transaction_type,
            }
        )


def test_insert_credit_handles_database_exception(mock_supabase):
    """Test that insert_credit handles database exceptions gracefully."""
    # Arrange
    owner_id = 999999
    transaction_type = "grant"
    mock_supabase.table.side_effect = Exception("Database connection error")

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD", {"grant": 12}
    ):
        # Act
        result = insert_credit(owner_id=owner_id, transaction_type=transaction_type)

        # Assert
        assert (
            result is None
        )  # Should return default_return_value due to @handle_exceptions
        mock_supabase.table.assert_called_once_with("credits")


def test_insert_credit_handles_insert_exception(mock_supabase, mock_query_chain):
    """Test that insert_credit handles exceptions during insert operation."""
    # Arrange
    owner_id = 555555
    transaction_type = "usage"
    mock_query_chain["table"].insert.side_effect = Exception("Insert error")

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD", {"usage": -4}
    ):
        # Act
        result = insert_credit(owner_id=owner_id, transaction_type=transaction_type)

        # Assert
        assert (
            result is None
        )  # Should return default_return_value due to @handle_exceptions
        mock_query_chain["table"].insert.assert_called_once()


def test_insert_credit_handles_execute_exception(mock_supabase, mock_query_chain):
    """Test that insert_credit handles exceptions during execute operation."""
    # Arrange
    owner_id = 777777
    transaction_type = "refund"
    mock_query_chain["insert"].execute.side_effect = Exception("Execute error")

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD", {"refund": 4}
    ):
        # Act
        result = insert_credit(owner_id=owner_id, transaction_type=transaction_type)

        # Assert
        assert (
            result is None
        )  # Should return default_return_value due to @handle_exceptions
        mock_query_chain["insert"].execute.assert_called_once()


def test_insert_credit_handles_missing_transaction_type(mock_supabase):
    """Test that insert_credit handles missing transaction type in CREDIT_AMOUNTS_USD."""
    # Arrange
    owner_id = 888888
    transaction_type = "unknown_type"

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD", {"grant": 12}
    ):
        # Act
        result = insert_credit(owner_id=owner_id, transaction_type=transaction_type)

        # Assert
        assert (
            result is None
        )  # Should return default_return_value due to @handle_exceptions


@pytest.mark.parametrize("owner_id", [0, 1, 999999999, -1])
def test_insert_credit_with_various_owner_ids(
    mock_supabase, mock_query_chain, owner_id
):
    """Test that insert_credit works with various owner ID values."""
    # Arrange
    transaction_type = "grant"

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD", {"grant": 12}
    ):
        # Act
        result = insert_credit(owner_id=owner_id, transaction_type=transaction_type)

        # Assert
        assert result is None
        mock_query_chain["table"].insert.assert_called_once_with(
            {
                "owner_id": owner_id,
                "amount_usd": 12,
                "transaction_type": transaction_type,
            }
        )


@pytest.mark.parametrize("usage_id", [0, 1, 999999, -1])
def test_insert_credit_with_various_usage_ids(
    mock_supabase, mock_query_chain, usage_id
):
    """Test that insert_credit works with various usage ID values."""
    # Arrange
    owner_id = 123456
    transaction_type = "usage"

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD", {"usage": -4}
    ):
        # Act
        result = insert_credit(
            owner_id=owner_id, transaction_type=transaction_type, usage_id=usage_id
        )

        # Assert
        assert result is None
        mock_query_chain["table"].insert.assert_called_once_with(
            {
                "owner_id": owner_id,
                "amount_usd": -4,
                "transaction_type": transaction_type,
                "usage_id": usage_id,
            }
        )


@pytest.mark.parametrize(
    "transaction_type,expected_amount",
    [
        ("usage", -4),
        ("grant", 12),
        ("bonus", 5),
        ("refund", 4),
    ],
)
def test_insert_credit_with_different_transaction_types(
    mock_supabase, mock_query_chain, transaction_type, expected_amount
):
    """Test that insert_credit correctly uses amounts for different transaction types."""
    # Arrange
    owner_id = 123456
    credit_amounts = {
        "usage": -4,
        "grant": 12,
        "bonus": 5,
        "refund": 4,
    }

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD", credit_amounts
    ):
        # Act
        result = insert_credit(owner_id=owner_id, transaction_type=transaction_type)

        # Assert
        assert result is None
        mock_query_chain["table"].insert.assert_called_once_with(
            {
                "owner_id": owner_id,
                "amount_usd": expected_amount,
                "transaction_type": transaction_type,
            }
        )


def test_insert_credit_verifies_correct_table_name(mock_supabase, mock_query_chain):
    """Test that insert_credit uses the correct table name."""
    # Arrange
    owner_id = 444444
    transaction_type = "grant"

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD", {"grant": 12}
    ):
        # Act
        insert_credit(owner_id=owner_id, transaction_type=transaction_type)

        # Assert
        mock_supabase.table.assert_called_once_with("credits")


def test_insert_credit_data_structure_without_usage_id(mock_supabase, mock_query_chain):
    """Test that insert_credit creates correct data structure without usage_id."""
    # Arrange
    owner_id = 555555
    transaction_type = "grant"
    expected_data = {
        "owner_id": owner_id,
        "amount_usd": 12,
        "transaction_type": transaction_type,
    }

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD", {"grant": 12}
    ):
        # Act
        insert_credit(owner_id=owner_id, transaction_type=transaction_type)

        # Assert
        mock_query_chain["table"].insert.assert_called_once_with(expected_data)


def test_insert_credit_data_structure_with_usage_id(mock_supabase, mock_query_chain):
    """Test that insert_credit creates correct data structure with usage_id."""
    # Arrange
    owner_id = 666666
    transaction_type = "usage"
    usage_id = 789
    expected_data = {
        "owner_id": owner_id,
        "amount_usd": -4,
        "transaction_type": transaction_type,
        "usage_id": usage_id,
    }

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD", {"usage": -4}
    ):
        # Act
        insert_credit(
            owner_id=owner_id, transaction_type=transaction_type, usage_id=usage_id
        )

        # Assert
        mock_query_chain["table"].insert.assert_called_once_with(expected_data)


def test_insert_credit_handles_key_error_from_credit_amounts(mock_supabase):
    """Test that insert_credit handles KeyError when transaction_type is not in CREDIT_AMOUNTS_USD."""
    # Arrange
    owner_id = 777777
    transaction_type = "nonexistent_type"

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD", {"grant": 12}
    ):
        # Act
        result = insert_credit(owner_id=owner_id, transaction_type=transaction_type)

        # Assert
        assert (
            result is None
        )  # Should return default_return_value due to @handle_exceptions


def test_insert_credit_handles_type_error_exception(mock_supabase, mock_query_chain):
    """Test that insert_credit handles TypeError exceptions gracefully."""
    # Arrange
    owner_id = 888888
    transaction_type = "grant"
    mock_query_chain["table"].insert.side_effect = TypeError("Type error")

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD", {"grant": 12}
    ):
        # Act
        result = insert_credit(owner_id=owner_id, transaction_type=transaction_type)

        # Assert
        assert (
            result is None
        )  # Should return default_return_value due to @handle_exceptions


def test_insert_credit_handles_attribute_error_exception(mock_supabase):
    """Test that insert_credit handles AttributeError exceptions gracefully."""
    # Arrange
    owner_id = 999999
    transaction_type = "grant"
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    del mock_table.insert  # Remove the insert attribute

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD", {"grant": 12}
    ):
        # Act
        result = insert_credit(owner_id=owner_id, transaction_type=transaction_type)

        # Assert
        assert (
            result is None
        )  # Should return default_return_value due to @handle_exceptions


def test_insert_credit_with_zero_amount(mock_supabase, mock_query_chain):
    """Test that insert_credit works with zero amount."""
    # Arrange
    owner_id = 101010
    transaction_type = "zero_amount"

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD", {"zero_amount": 0}
    ):
        # Act
        result = insert_credit(owner_id=owner_id, transaction_type=transaction_type)

        # Assert
        assert result is None
        mock_query_chain["table"].insert.assert_called_once_with(
            {
                "owner_id": owner_id,
                "amount_usd": 0,
                "transaction_type": transaction_type,
            }
        )


def test_insert_credit_with_large_negative_amount(mock_supabase, mock_query_chain):
    """Test that insert_credit works with large negative amounts."""
    # Arrange
    owner_id = 121212
    transaction_type = "large_deduction"

    with patch(
        "services.supabase.credits.insert_credit.CREDIT_AMOUNTS_USD",
        {"large_deduction": -1000},
    ):
        # Act
        result = insert_credit(owner_id=owner_id, transaction_type=transaction_type)

        # Assert
        assert result is None
        mock_query_chain["table"].insert.assert_called_once_with(
            {
                "owner_id": owner_id,
                "amount_usd": -1000,
                "transaction_type": transaction_type,
            }
        )
