from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

import pytest

from services.supabase.installations.delete_installation import delete_installation


@pytest.fixture
def mock_supabase():
    """Fixture to provide a mocked supabase client."""
    with patch("services.supabase.installations.delete_installation.supabase") as mock:
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()
        MagicMock()

        # Chain the method calls
        mock.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.return_value = None

        yield mock


@pytest.fixture
def mock_datetime_now():
    """Fixture to provide a mocked datetime.now."""
    with patch(
        "services.supabase.installations.delete_installation.datetime"
    ) as mock_dt:
        # Create a fixed datetime for consistent testing
        fixed_datetime = datetime(2023, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        mock_dt.now.return_value = fixed_datetime
        mock_dt.timezone = timezone  # Keep the timezone reference
        yield mock_dt


def test_delete_installation_successful_execution(mock_supabase, mock_datetime_now):
    """Test that delete_installation executes successfully with valid parameters."""
    installation_id = 12345
    user_id = 67890
    user_name = "test-user"

    result = delete_installation(installation_id, user_id, user_name)

    # Verify the function returns None (as expected from the decorator)
    assert result is None

    # Verify supabase operations were called correctly
    mock_supabase.table.assert_called_once_with(table_name="installations")

    # Verify the update data structure
    expected_data = {
        "uninstalled_at": "2023-01-15T10:30:45+00:00",
        "uninstalled_by": "67890:test-user",
    }
    mock_supabase.table.return_value.update.assert_called_once_with(json=expected_data)
    mock_supabase.table.return_value.update.return_value.eq.assert_called_once_with(
        column="installation_id", value=installation_id
    )
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.assert_called_once()


def test_delete_installation_with_zero_installation_id(
    mock_supabase, mock_datetime_now
):
    """Test that delete_installation handles zero installation_id."""
    installation_id = 0
    user_id = 123
    user_name = "zero-test"

    result = delete_installation(installation_id, user_id, user_name)

    assert result is None
    mock_supabase.table.assert_called_once_with(table_name="installations")
    mock_supabase.table.return_value.update.return_value.eq.assert_called_once_with(
        column="installation_id", value=0
    )


def test_delete_installation_with_negative_installation_id(
    mock_supabase, mock_datetime_now
):
    """Test that delete_installation handles negative installation_id."""
    installation_id = -1
    user_id = 456
    user_name = "negative-test"

    result = delete_installation(installation_id, user_id, user_name)

    assert result is None
    mock_supabase.table.assert_called_once_with(table_name="installations")
    mock_supabase.table.return_value.update.return_value.eq.assert_called_once_with(
        column="installation_id", value=-1
    )


def test_delete_installation_with_large_installation_id(
    mock_supabase, mock_datetime_now
):
    """Test that delete_installation handles large installation_id."""
    installation_id = 999999999
    user_id = 888888888
    user_name = "large-test"

    result = delete_installation(installation_id, user_id, user_name)

    assert result is None
    mock_supabase.table.assert_called_once_with(table_name="installations")
    mock_supabase.table.return_value.update.return_value.eq.assert_called_once_with(
        column="installation_id", value=999999999
    )


def test_delete_installation_with_zero_user_id(mock_supabase, mock_datetime_now):
    """Test that delete_installation handles zero user_id."""
    installation_id = 12345
    user_id = 0
    user_name = "zero-user"

    result = delete_installation(installation_id, user_id, user_name)

    assert result is None

    # Verify the uninstalled_by field contains the zero user_id
    expected_data = {
        "uninstalled_at": "2023-01-15T10:30:45+00:00",
        "uninstalled_by": "0:zero-user",
    }
    mock_supabase.table.return_value.update.assert_called_once_with(json=expected_data)


def test_delete_installation_with_empty_user_name(mock_supabase, mock_datetime_now):
    """Test that delete_installation handles empty user_name."""
    installation_id = 12345
    user_id = 67890
    user_name = ""

    result = delete_installation(installation_id, user_id, user_name)

    assert result is None

    # Verify the uninstalled_by field contains the empty user_name
    expected_data = {
        "uninstalled_at": "2023-01-15T10:30:45+00:00",
        "uninstalled_by": "67890:",
    }
    mock_supabase.table.return_value.update.assert_called_once_with(json=expected_data)


def test_delete_installation_with_special_characters_in_user_name(
    mock_supabase, mock_datetime_now
):
    """Test that delete_installation handles special characters in user_name."""
    special_names = [
        "user-with-dashes",
        "user_with_underscores",
        "user.with.dots",
        "user@domain.com",
        "user-with-unicode-ñ",
        "user:with:colons",
    ]

    installation_id = 12345
    user_id = 67890

    for user_name in special_names:
        result = delete_installation(installation_id, user_id, user_name)

        assert result is None

        # Verify the special characters are preserved in uninstalled_by
        expected_data = {
            "uninstalled_at": "2023-01-15T10:30:45+00:00",
            "uninstalled_by": f"{user_id}:{user_name}",
        }
        mock_supabase.table.return_value.update.assert_called_with(json=expected_data)

        # Reset mock for next iteration
        mock_supabase.reset_mock()


def test_delete_installation_supabase_exception_handling(
    mock_supabase, mock_datetime_now
):
    """Test that delete_installation handles supabase exceptions gracefully."""
    installation_id = 12345
    user_id = 67890
    user_name = "test-user"

    # Make the execute method raise an exception
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception(
        "Database error"
    )

    # The function should return None due to handle_exceptions decorator
    result = delete_installation(installation_id, user_id, user_name)

    assert result is None
    mock_supabase.table.assert_called_once_with(table_name="installations")


def test_delete_installation_data_structure_format(mock_supabase, mock_datetime_now):
    """Test that the correct data structure is passed to supabase update."""
    installation_id = 12345
    user_id = 67890
    user_name = "test-user"

    delete_installation(installation_id, user_id, user_name)

    # Verify the exact data structure passed to update
    call_args = mock_supabase.table.return_value.update.call_args
    update_data = call_args[1]["json"]

    # Verify the structure and format
    assert "uninstalled_at" in update_data
    assert "uninstalled_by" in update_data
    assert update_data["uninstalled_at"] == "2023-01-15T10:30:45+00:00"
    assert update_data["uninstalled_by"] == "67890:test-user"
    assert len(update_data) == 2  # Only these two fields should be present


@pytest.mark.parametrize(
    "installation_id,user_id,user_name",
    [
        (1, 100, "user1"),
        (999999, 888888, "big-user"),
        (42, 24, "special-user"),
        (123456789, 987654321, "enterprise-user"),
        (2147483647, 2147483647, "max-int-user"),  # Max 32-bit integer
    ],
)
def test_delete_installation_with_various_parameter_combinations(
    mock_supabase, mock_datetime_now, installation_id, user_id, user_name
):
    """Test that delete_installation works with various parameter combinations."""
    result = delete_installation(installation_id, user_id, user_name)

    assert result is None
    mock_supabase.table.assert_called_once_with(table_name="installations")
    mock_supabase.table.return_value.update.return_value.eq.assert_called_once_with(
        column="installation_id", value=installation_id
    )

    # Verify the uninstalled_by format
    call_args = mock_supabase.table.return_value.update.call_args
    update_data = call_args[1]["json"]
    assert update_data["uninstalled_by"] == f"{user_id}:{user_name}"


def test_delete_installation_method_chaining(mock_supabase, mock_datetime_now):
    """Test that the supabase method chaining is executed in the correct order."""
    installation_id = 12345
    user_id = 67890
    user_name = "test-user"

    delete_installation(installation_id, user_id, user_name)

    # Verify the method chain is called in the correct order
    mock_supabase.table.assert_called_once_with(table_name="installations")

    # Get the mock objects from the chain
    table_mock = mock_supabase.table.return_value
    update_mock = table_mock.update.return_value
    eq_mock = update_mock.eq.return_value

    table_mock.update.assert_called_once()
    update_mock.eq.assert_called_once()
    eq_mock.execute.assert_called_once()


def test_delete_installation_decorator_behavior():
    """Test that the handle_exceptions decorator is properly applied."""
    # Verify the function has the decorator applied by checking its attributes
    assert hasattr(delete_installation, "__wrapped__")

    # Test that the function returns None by default (from decorator)
    with patch(
        "services.supabase.installations.delete_installation.supabase"
    ) as mock_supabase:
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            "some_value"
        )

        result = delete_installation(12345, 67890, "test-user")
        assert (
            result is None
        )  # Should return None due to decorator default_return_value


def test_delete_installation_datetime_iso_format():
    """Test that the datetime is properly formatted as ISO string."""
    with patch(
        "services.supabase.installations.delete_installation.supabase"
    ) as mock_supabase:
        # Use real datetime to test the actual ISO format
        result = delete_installation(12345, 67890, "test-user")

        assert result is None

        # Get the actual datetime string that was passed
        call_args = mock_supabase.table.return_value.update.call_args
        update_data = call_args[1]["json"]
        uninstalled_at = update_data["uninstalled_at"]

        # Verify it's a valid ISO format string with timezone
        assert isinstance(uninstalled_at, str)
        assert uninstalled_at.endswith("+00:00")  # UTC timezone

        # Verify it can be parsed back to datetime
        parsed_datetime = datetime.fromisoformat(uninstalled_at)
        assert parsed_datetime.tzinfo == timezone.utc
