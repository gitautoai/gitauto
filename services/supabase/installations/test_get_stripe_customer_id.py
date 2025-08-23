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


@pytest.fixture
def sample_installation_with_stripe_data():
    """Fixture to provide sample installation data with stripe customer ID."""
    return {
        "owner_id": 123456789,
        "owners": {
            "stripe_customer_id": "cus_test123456789"
        }
    }


@pytest.fixture
def sample_installation_without_stripe_data():
    """Fixture to provide sample installation data without stripe customer ID."""
    return {
        "owner_id": 123456789,
        "owners": {
            "stripe_customer_id": None
        }
    }


@pytest.fixture
def sample_installation_with_empty_owners():
    """Fixture to provide sample installation data with empty owners."""
    return {
        "owner_id": 123456789,
        "owners": {}
    }


class TestGetStripeCustomerId:
    """Test cases for get_stripe_customer_id function."""

    def test_get_stripe_customer_id_returns_customer_id_when_found(
        self, mock_supabase_query, sample_installation_with_stripe_data
    ):
        """Test that get_stripe_customer_id returns the stripe customer ID when found."""
        # Arrange
        mock_supabase_query.execute.return_value = (
            (None, [sample_installation_with_stripe_data]),
            None,
        )

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result == "cus_test123456789"

    def test_get_stripe_customer_id_returns_none_when_no_data_found(
        self, mock_supabase_query
    ):
        """Test that get_stripe_customer_id returns None when no data is found."""
        # Arrange
        mock_supabase_query.execute.return_value = ((None, []), None)

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result is None

    def test_get_stripe_customer_id_returns_none_when_data_is_none(
        self, mock_supabase_query
    ):
        """Test that get_stripe_customer_id returns None when data[1] is None."""
        # Arrange
        mock_supabase_query.execute.return_value = ((None, None), None)

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result is None

    def test_get_stripe_customer_id_returns_none_when_data_is_empty_list(
        self, mock_supabase_query
    ):
        """Test that get_stripe_customer_id returns None when data[1] is empty list."""
        # Arrange
        mock_supabase_query.execute.return_value = ((None, []), None)

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result is None

    def test_get_stripe_customer_id_returns_none_when_owners_is_none(
        self, mock_supabase_query
    ):
        """Test that get_stripe_customer_id returns None when owners is None."""
        # Arrange
        installation_data = {
            "owner_id": 123456789,
            "owners": None
        }
        mock_supabase_query.execute.return_value = (
            (None, [installation_data]),
            None,
        )

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result is None

    def test_get_stripe_customer_id_returns_none_when_owners_is_empty_dict(
        self, mock_supabase_query, sample_installation_with_empty_owners
    ):
        """Test that get_stripe_customer_id returns None when owners is empty dict."""
        # Arrange
        mock_supabase_query.execute.return_value = (
            (None, [sample_installation_with_empty_owners]),
            None,
        )

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result is None

    def test_get_stripe_customer_id_returns_none_when_owners_key_missing(
        self, mock_supabase_query
    ):
        """Test that get_stripe_customer_id returns None when owners key is missing entirely."""
        # Arrange
        installation_data = {"owner_id": 123456789}
        mock_supabase_query.execute.return_value = (
            (None, [installation_data]),
            None,
        )

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result is None

    def test_get_stripe_customer_id_returns_none_when_stripe_customer_id_is_none(
        self, mock_supabase_query, sample_installation_without_stripe_data
    ):
        """Test that get_stripe_customer_id returns None when stripe_customer_id is None."""
        # Arrange
        mock_supabase_query.execute.return_value = (
            (None, [sample_installation_without_stripe_data]),
            None,
        )

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result is None

    def test_get_stripe_customer_id_returns_none_when_stripe_customer_id_is_not_string(
        self, mock_supabase_query
    ):
        """Test that get_stripe_customer_id returns None when stripe_customer_id is not a string."""
        # Arrange
        installation_data = {
            "owner_id": 123456789,
            "owners": {
                "stripe_customer_id": 123456  # Not a string
            }
        }
        mock_supabase_query.execute.return_value = (
            (None, [installation_data]),
            None,
        )

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result is None

    def test_get_stripe_customer_id_returns_none_when_stripe_customer_id_is_empty_string(
        self, mock_supabase_query
    ):
        """Test that get_stripe_customer_id returns None when stripe_customer_id is empty string."""
        # Arrange
        installation_data = {
            "owner_id": 123456789,
            "owners": {
                "stripe_customer_id": ""  # Empty string
            }
        }
        mock_supabase_query.execute.return_value = (
            (None, [installation_data]),
            None,
        )

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result is None

    def test_get_stripe_customer_id_returns_none_when_exception_occurs(
        self, mock_supabase_query
    ):
        """Test that get_stripe_customer_id returns None when an exception occurs."""
        # Arrange
        mock_supabase_query.execute.side_effect = Exception("Database error")

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result is None

    def test_get_stripe_customer_id_returns_none_when_type_error_occurs(
        self, mock_supabase_query
    ):
        """Test that get_stripe_customer_id returns None when TypeError occurs accessing data[1][0]."""
        # Arrange - simulate data[1] being a non-indexable object
        mock_supabase_query.execute.return_value = (
            (
                None,
                123,  # data[1][0] tries to access index 0 of int, which raises TypeError
            ),
            None,
        )

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result is None

    def test_get_stripe_customer_id_returns_none_when_index_error_occurs_on_data_access(
        self, mock_supabase_query
    ):
        """Test that get_stripe_customer_id returns None when IndexError occurs accessing data[1]."""
        # Arrange - simulate malformed response structure that causes IndexError
        mock_supabase_query.execute.return_value = (
            ("invalid",),  # This will cause IndexError when accessing data[1]
            None,
        )

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result is None

    def test_get_stripe_customer_id_calls_correct_supabase_methods(
        self, mock_supabase_query
    ):
        """Test that get_stripe_customer_id calls the correct Supabase methods with correct parameters."""
        # Arrange
        mock_supabase_query.execute.return_value = ((None, []), None)

        with patch(
            "services.supabase.installations.get_stripe_customer_id.supabase"
        ) as mock_supabase:
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()

            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = ((None, []), None)

            # Act
            get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

            # Assert
            mock_supabase.table.assert_called_once_with(table_name="installations")
            mock_table.select.assert_called_once_with(
                "owner_id, owners(stripe_customer_id)"
            )
            mock_select.eq.assert_called_once_with(
                column="installation_id", value=TEST_INSTALLATION_ID
            )
            mock_eq.execute.assert_called_once()

    @pytest.mark.parametrize(
        "installation_id,expected_customer_id",
        [
            (12345678, "cus_test12345678"),
            (87654321, "cus_test87654321"),
            (999999999, "cus_test999999999"),
            (1, "cus_test1"),
        ],
    )
    def test_get_stripe_customer_id_with_various_installation_ids_parametrized(
        self, mock_supabase_query, installation_id, expected_customer_id
    ):
        """Test get_stripe_customer_id with various installation IDs using parametrize."""
        # Arrange
        installation_data = {
            "owner_id": 123456789,
            "owners": {
                "stripe_customer_id": expected_customer_id
            }
        }
        mock_supabase_query.execute.return_value = (
            (None, [installation_data]),
            None,
        )

        # Act
        result = get_stripe_customer_id(installation_id=installation_id)

        # Assert
        assert result == expected_customer_id

    def test_get_stripe_customer_id_with_multiple_installations_returns_first(
        self, mock_supabase_query
    ):
        """Test that get_stripe_customer_id returns the first installation's stripe customer ID when multiple are found."""
        # Arrange
        first_installation = {
            "owner_id": 123456789,
            "owners": {
                "stripe_customer_id": "cus_first123"
            }
        }
        second_installation = {
            "owner_id": 987654321,
            "owners": {
                "stripe_customer_id": "cus_second456"
            }
        }
        mock_supabase_query.execute.return_value = (
            (None, [first_installation, second_installation]),
            None,
        )

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result == "cus_first123"


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

    # Assert return type annotation
    assert sig.return_annotation == "str | None"


def test_get_stripe_customer_id_has_handle_exceptions_decorator():
    """Test that get_stripe_customer_id is decorated with handle_exceptions."""
    # Check if the function has the expected wrapper attributes from handle_exceptions
    assert hasattr(get_stripe_customer_id, "__wrapped__")

    # Verify the function name is preserved by the decorator
    assert get_stripe_customer_id.__name__ == "get_stripe_customer_id"


def test_get_stripe_customer_id_decorator_behavior():
    """Test that the handle_exceptions decorator is properly applied."""
    # Test that the function has the decorator applied by checking it returns None on exception
    with patch(
        "services.supabase.installations.get_stripe_customer_id.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = Exception("Unexpected error")

        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)
        assert result is None


def test_get_stripe_customer_id_with_malformed_data_structure(mock_supabase_query):
    """Test that get_stripe_customer_id handles malformed data gracefully."""
    # Arrange - simulate various malformed data structures
    malformed_cases = [
        ((None, {}), None),  # dict instead of list, data[1][0] will raise KeyError
        ((None, []), None),  # empty list
        (("wrong_structure",), None),  # wrong structure
        (None, None),  # None data
    ]

    for malformed_data in malformed_cases:
        mock_supabase_query.execute.return_value = malformed_data

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result is None


def test_get_stripe_customer_id_with_edge_case_installation_ids(mock_supabase_query):
    """Test get_stripe_customer_id with edge case installation ID values."""
    edge_cases = [
        (-1, "cus_negative"),  # Negative installation ID
        (0, "cus_zero"),  # Zero installation ID
        (2**31 - 1, "cus_max_int"),  # Large positive integer
    ]

    for installation_id, expected_customer_id in edge_cases:
        # Arrange
        installation_data = {
            "owner_id": 123456789,
            "owners": {
                "stripe_customer_id": expected_customer_id
            }
        }
        mock_supabase_query.execute.return_value = (
            (None, [installation_data]),
            None,
        )

        # Act
        result = get_stripe_customer_id(installation_id=installation_id)

        # Assert
        assert result == expected_customer_id


def test_get_stripe_customer_id_with_various_stripe_customer_id_formats(
    mock_supabase_query
):
    """Test get_stripe_customer_id with various valid stripe customer ID formats."""
    valid_customer_ids = [
        "cus_1234567890",
        "cus_abcdefghij",
        "cus_MixedCase123",
        "cus_with_underscores_123",
    ]

    for customer_id in valid_customer_ids:
        # Arrange
        installation_data = {
            "owner_id": 123456789,
            "owners": {
                "stripe_customer_id": customer_id
            }
        }
        mock_supabase_query.execute.return_value = (
            (None, [installation_data]),
            None,
        )

        # Act
        result = get_stripe_customer_id(installation_id=TEST_INSTALLATION_ID)

        # Assert
        assert result == customer_id
        assert isinstance(result, str)