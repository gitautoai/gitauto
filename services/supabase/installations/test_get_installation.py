from unittest.mock import patch, MagicMock
import inspect
import datetime

import pytest

from config import TEST_OWNER_ID
from services.supabase.installations.get_installation import get_installation


@pytest.fixture
def mock_supabase_query():
    """Fixture to provide a mocked Supabase query chain."""
    with patch("services.supabase.installations.get_installation.supabase") as mock:
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_is = MagicMock()

        mock.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.is_.return_value = mock_is

        yield mock_is


@pytest.fixture
def sample_installation_data():
    """Fixture to provide sample installation data."""
    return {
        "installation_id": 12345678,
        "created_at": datetime.datetime(2023, 1, 1, 12, 0, 0),
        "created_by": "test_user",
        "owner_id": TEST_OWNER_ID,
        "owner_name": "test_owner",
        "owner_type": "Organization",
        "uninstalled_at": None,
        "uninstalled_by": None,
    }


@pytest.fixture
def sample_user_installation_data():
    """Fixture to provide sample user installation data."""
    return {
        "installation_id": 87654321,
        "created_at": datetime.datetime(2023, 2, 1, 10, 30, 0),
        "created_by": "user_creator",
        "owner_id": 999888777,
        "owner_name": "individual_user",
        "owner_type": "User",
        "uninstalled_at": None,
        "uninstalled_by": None,
    }


class TestGetInstallation:
    """Test cases for get_installation function."""

    def test_get_installation_returns_installation_when_found(
        self, mock_supabase_query, sample_installation_data
    ):
        """Test that get_installation returns the installation when found."""
        # Arrange
        mock_supabase_query.execute.return_value = (
            (None, [sample_installation_data]),
            None,
        )

        # Act
        result = get_installation(owner_id=TEST_OWNER_ID)

        # Assert
        assert result is not None
        assert isinstance(result, dict)
        assert result["installation_id"] == sample_installation_data["installation_id"]
        assert result["owner_id"] == sample_installation_data["owner_id"]
        assert result["owner_name"] == sample_installation_data["owner_name"]
        assert result["owner_type"] == sample_installation_data["owner_type"]
        assert result["uninstalled_at"] is None

    def test_get_installation_returns_first_installation_when_multiple_found(
        self, mock_supabase_query
    ):
        """Test that get_installation returns the first installation when multiple are found."""
        # Arrange
        first_installation = {
            "installation_id": 11111,
            "owner_id": TEST_OWNER_ID,
            "owner_name": "first_owner",
            "owner_type": "Organization",
            "created_at": datetime.datetime(2023, 1, 1, 12, 0, 0),
            "created_by": "test_user",
            "uninstalled_at": None,
            "uninstalled_by": None,
        }
        second_installation = {
            "installation_id": 22222,
            "owner_id": TEST_OWNER_ID,
            "owner_name": "second_owner",
            "owner_type": "User",
            "created_at": datetime.datetime(2023, 2, 1, 12, 0, 0),
            "created_by": "test_user",
            "uninstalled_at": None,
            "uninstalled_by": None,
        }
        mock_supabase_query.execute.return_value = (
            (None, [first_installation, second_installation]),
            None,
        )

        # Act
        result = get_installation(owner_id=TEST_OWNER_ID)

        # Assert
        assert result is not None
        assert result["installation_id"] == first_installation["installation_id"]
        assert result["owner_name"] == first_installation["owner_name"]

    def test_get_installation_returns_none_when_no_data_found(
        self, mock_supabase_query
    ):
        """Test that get_installation returns None when no data is found."""
        # Arrange
        mock_supabase_query.execute.return_value = ((None, []), None)

        # Act
        result = get_installation(owner_id=TEST_OWNER_ID)

        # Assert
        assert result is None

    def test_get_installation_returns_none_when_data_is_none(self, mock_supabase_query):
        """Test that get_installation returns None when data[1] is None."""
        # Arrange
        mock_supabase_query.execute.return_value = ((None, None), None)

        # Act
        result = get_installation(owner_id=TEST_OWNER_ID)

        # Assert
        assert result is None

    def test_get_installation_returns_none_when_exception_occurs(
        self, mock_supabase_query
    ):
        """Test that get_installation returns None when an exception occurs."""
        # Arrange
        mock_supabase_query.execute.side_effect = Exception("Database error")

        # Act
        result = get_installation(owner_id=TEST_OWNER_ID)

        # Assert
        assert result is None

    def test_get_installation_returns_none_when_type_error_occurs(
        self, mock_supabase_query
    ):
        """Test that get_installation returns None when TypeError occurs accessing data[1][0]."""
        # Arrange - simulate data[1] being a non-indexable object
        mock_supabase_query.execute.return_value = (
            (
                None,
                123,
            ),  # data[1][0] tries to access index 0 of int, which raises TypeError
            None,
        )

        # Act
        result = get_installation(owner_id=TEST_OWNER_ID)

        # Assert
        assert result is None

    def test_get_installation_returns_none_when_index_error_occurs_on_data_access(
        self, mock_supabase_query
    ):
        """Test that get_installation returns None when IndexError occurs accessing data[1]."""
        # Arrange - simulate malformed response structure that causes IndexError
        mock_supabase_query.execute.return_value = (
            ("invalid",),  # This will cause IndexError when accessing data[1]
            None,
        )

        # Act
        result = get_installation(owner_id=TEST_OWNER_ID)

        # Assert
        assert result is None

    def test_get_installation_with_user_type_installation(
        self, mock_supabase_query, sample_user_installation_data
    ):
        """Test that get_installation works correctly with User type installations."""
        # Arrange
        mock_supabase_query.execute.return_value = (
            (None, [sample_user_installation_data]),
            None,
        )

        # Act
        result = get_installation(owner_id=999888777)

        # Assert
        assert result is not None
        assert result["owner_type"] == "User"
        assert result["owner_name"] == "individual_user"
        assert result["installation_id"] == 87654321

    def test_get_installation_with_different_owner_ids(self, mock_supabase_query):
        """Test get_installation with various owner ID values."""
        test_cases = [
            (1, 11111),
            (999999999, 22222),
            (123456789, 33333),
        ]

        for owner_id, installation_id in test_cases:
            # Arrange
            installation_data = {
                "installation_id": installation_id,
                "owner_id": owner_id,
                "owner_name": f"owner_{owner_id}",
                "owner_type": "Organization",
                "created_at": datetime.datetime.now(),
                "created_by": "test_user",
                "uninstalled_at": None,
                "uninstalled_by": None,
            }
            mock_supabase_query.execute.return_value = (
                (None, [installation_data]),
                None,
            )

            # Act
            result = get_installation(owner_id=owner_id)

            # Assert
            assert result is not None
            assert result["owner_id"] == owner_id
            assert result["installation_id"] == installation_id

    def test_get_installation_calls_correct_supabase_methods(self, mock_supabase_query):
        """Test that get_installation calls the correct Supabase methods with correct parameters."""
        # Arrange
        mock_supabase_query.execute.return_value = ((None, []), None)

        with patch(
            "services.supabase.installations.get_installation.supabase"
        ) as mock_supabase:
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            mock_is = MagicMock()

            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.is_.return_value = mock_is
            mock_is.execute.return_value = ((None, []), None)

            # Act
            get_installation(owner_id=TEST_OWNER_ID)

            # Assert
            mock_supabase.table.assert_called_once_with(table_name="installations")
            mock_table.select.assert_called_once_with("*")
            mock_select.eq.assert_called_once_with(
                column="owner_id", value=TEST_OWNER_ID
            )
            mock_eq.is_.assert_called_once_with(column="uninstalled_at", value="null")
            mock_is.execute.assert_called_once()

    def test_get_installation_with_complete_installation_data(
        self, mock_supabase_query
    ):
        """Test with a complete installation data structure."""
        complete_installation = {
            "installation_id": 12345678,
            "created_at": datetime.datetime(2023, 1, 1, 12, 0, 0),
            "created_by": "github_user",
            "owner_id": TEST_OWNER_ID,
            "owner_name": "test_organization",
            "owner_type": "Organization",
            "uninstalled_at": None,
            "uninstalled_by": None,
        }

        # Arrange
        mock_supabase_query.execute.return_value = (
            (None, [complete_installation]),
            None,
        )

        # Act
        result = get_installation(owner_id=TEST_OWNER_ID)

        # Assert
        assert result is not None
        assert result == complete_installation
        assert all(key in result for key in complete_installation.keys())

    @pytest.mark.parametrize(
        "owner_id,expected_installation_id",
        [
            (1, 11111),
            (999999999, 22222),
            (123456789, 33333),
            (0, 44444),  # Edge case: zero owner_id
        ],
    )
    def test_get_installation_with_various_owner_ids_parametrized(
        self, mock_supabase_query, owner_id, expected_installation_id
    ):
        """Test get_installation with various owner IDs using parametrize."""
        # Arrange
        installation_data = {
            "installation_id": expected_installation_id,
            "owner_id": owner_id,
            "owner_name": f"owner_{owner_id}",
            "owner_type": "Organization",
            "created_at": datetime.datetime.now(),
            "created_by": "test_user",
            "uninstalled_at": None,
            "uninstalled_by": None,
        }
        mock_supabase_query.execute.return_value = ((None, [installation_data]), None)

        # Act
        result = get_installation(owner_id=owner_id)

        # Assert
        assert result is not None
        assert result["owner_id"] == owner_id
        assert result["installation_id"] == expected_installation_id


def test_get_installation_function_signature():
    """Test that get_installation has the correct function signature."""
    # Get function signature
    sig = inspect.signature(get_installation)

    # Assert parameter count and names
    assert len(sig.parameters) == 1
    assert "owner_id" in sig.parameters

    # Assert parameter type annotation
    owner_id_param = sig.parameters["owner_id"]
    assert owner_id_param.annotation is int


def test_get_installation_has_handle_exceptions_decorator():
    """Test that get_installation is decorated with handle_exceptions."""
    # Check if the function has the expected wrapper attributes from handle_exceptions
    assert hasattr(get_installation, "__wrapped__")

    # Verify the function name is preserved by the decorator
    assert get_installation.__name__ == "get_installation"


def test_get_installation_decorator_behavior():
    """Test that the handle_exceptions decorator is properly applied."""
    # Test that the function has the decorator applied by checking it returns None on exception
    with patch(
        "services.supabase.installations.get_installation.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = Exception("Unexpected error")

        result = get_installation(owner_id=TEST_OWNER_ID)
        assert result is None


def test_get_installation_with_type_casting_behavior(
    mock_supabase_query, sample_installation_data
):
    """Test that get_installation properly handles the cast operation."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        (None, [sample_installation_data]),
        None,
    )

    # Act
    result = get_installation(owner_id=TEST_OWNER_ID)

    # Assert - The function should return the raw dict data after casting
    assert result is not None
    assert isinstance(result, dict)
    # Verify that all expected fields are present
    expected_fields = [
        "installation_id",
        "owner_id",
        "owner_name",
        "owner_type",
        "created_at",
        "created_by",
        "uninstalled_at",
        "uninstalled_by",
    ]
    for field in expected_fields:
        assert field in result


def test_get_installation_with_malformed_data_structure(mock_supabase_query):
    """Test that get_installation handles malformed data gracefully."""
    # Arrange - simulate various malformed data structures
    malformed_cases = [
        ((None, {}), None),  # dict instead of list, data[1][0] will raise KeyError
        ((None, []), None),
        (("wrong_structure",), None),
        (None, None),
    ]

    for malformed_data in malformed_cases:
        mock_supabase_query.execute.return_value = malformed_data

        # Act
        result = get_installation(owner_id=TEST_OWNER_ID)

        # Assert
        assert result is None


def test_get_installation_with_edge_case_owner_ids(mock_supabase_query):
    """Test get_installation with edge case owner ID values."""
    edge_cases = [
        (-1, "negative_owner"),  # Negative owner ID
        (0, "zero_owner"),  # Zero owner ID
        (2**31 - 1, "max_int_owner"),  # Large positive integer
    ]

    for owner_id, owner_name in edge_cases:
        # Arrange
        installation_data = {
            "installation_id": 99999,
            "owner_id": owner_id,
            "owner_name": owner_name,
            "owner_type": "Organization",
            "created_at": datetime.datetime.now(),
            "created_by": "test_user",
            "uninstalled_at": None,
            "uninstalled_by": None,
        }
        mock_supabase_query.execute.return_value = ((None, [installation_data]), None)

        # Act
        result = get_installation(owner_id=owner_id)

        # Assert
        assert result is not None
        assert result["owner_id"] == owner_id
        assert result["owner_name"] == owner_name
