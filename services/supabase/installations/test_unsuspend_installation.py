from unittest.mock import patch, MagicMock

import pytest

from services.supabase.installations.unsuspend_installation import (
    unsuspend_installation,
)


@pytest.fixture
def mock_supabase():
    """Fixture to provide a mocked supabase client."""
    with patch(
        "services.supabase.installations.unsuspend_installation.supabase"
    ) as mock:
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


def test_unsuspend_installation_successful_execution(mock_supabase):
    """Test that unsuspend_installation executes successfully with valid installation_id."""
    installation_id = 12345

    result = unsuspend_installation(installation_id)

    # Verify the function returns None (as expected from the decorator)
    assert result is None

    # Verify supabase operations were called correctly
    mock_supabase.table.assert_called_once_with(table_name="installations")
    mock_supabase.table.return_value.update.assert_called_once_with(
        json={"uninstalled_at": None, "uninstalled_by": None}
    )
    mock_supabase.table.return_value.update.return_value.eq.assert_called_once_with(
        column="installation_id", value=installation_id
    )
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.assert_called_once()


def test_unsuspend_installation_with_zero_installation_id(mock_supabase):
    """Test that unsuspend_installation handles zero installation_id."""
    installation_id = 0

    result = unsuspend_installation(installation_id)

    assert result is None
    mock_supabase.table.assert_called_once_with(table_name="installations")
    mock_supabase.table.return_value.update.return_value.eq.assert_called_once_with(
        column="installation_id", value=0
    )


def test_unsuspend_installation_with_negative_installation_id(mock_supabase):
    """Test that unsuspend_installation handles negative installation_id."""
    installation_id = -1

    result = unsuspend_installation(installation_id)

    assert result is None
    mock_supabase.table.assert_called_once_with(table_name="installations")
    mock_supabase.table.return_value.update.return_value.eq.assert_called_once_with(
        column="installation_id", value=-1
    )


def test_unsuspend_installation_with_large_installation_id(mock_supabase):
    """Test that unsuspend_installation handles large installation_id."""
    installation_id = 999999999

    result = unsuspend_installation(installation_id)

    assert result is None
    mock_supabase.table.assert_called_once_with(table_name="installations")
    mock_supabase.table.return_value.update.return_value.eq.assert_called_once_with(
        column="installation_id", value=999999999
    )


def test_unsuspend_installation_supabase_exception_handling(mock_supabase):
    """Test that unsuspend_installation handles supabase exceptions gracefully."""
    installation_id = 12345

    # Make the execute method raise an exception
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception(
        "Database error"
    )

    # The function should return None due to handle_exceptions decorator
    result = unsuspend_installation(installation_id)

    assert result is None
    mock_supabase.table.assert_called_once_with(table_name="installations")


def test_unsuspend_installation_data_structure():
    """Test that the correct data structure is passed to supabase update."""
    installation_id = 12345
    expected_data = {
        "uninstalled_at": None,
        "uninstalled_by": None,
    }

    with patch(
        "services.supabase.installations.unsuspend_installation.supabase"
    ) as mock_supabase:
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.return_value = None

        unsuspend_installation(installation_id)

        # Verify the exact data structure passed to update
        mock_table.update.assert_called_once_with(json=expected_data)


@pytest.mark.parametrize(
    "installation_id",
    [
        1,
        100,
        12345,
        999999,
        2147483647,  # Max 32-bit integer
    ],
)
def test_unsuspend_installation_with_various_installation_ids(
    mock_supabase, installation_id
):
    """Test that unsuspend_installation works with various installation_id values."""
    result = unsuspend_installation(installation_id)

    assert result is None
    mock_supabase.table.assert_called_once_with(table_name="installations")
    mock_supabase.table.return_value.update.return_value.eq.assert_called_once_with(
        column="installation_id", value=installation_id
    )


def test_unsuspend_installation_method_chaining(mock_supabase):
    """Test that the supabase method chaining is executed in the correct order."""
    installation_id = 12345

    unsuspend_installation(installation_id)

    # Verify the method chain is called in the correct order
    mock_supabase.table.assert_called_once_with(table_name="installations")

    # Get the mock objects from the chain
    table_mock = mock_supabase.table.return_value
    update_mock = table_mock.update.return_value
    eq_mock = update_mock.eq.return_value

    table_mock.update.assert_called_once()
    update_mock.eq.assert_called_once()
    eq_mock.execute.assert_called_once()


def test_unsuspend_installation_decorator_behavior():
    """Test that the handle_exceptions decorator is properly applied."""
    # Verify the function has the decorator applied by checking its attributes
    assert hasattr(unsuspend_installation, "__wrapped__")

    # Test that the function returns None by default (from decorator)
    with patch(
        "services.supabase.installations.unsuspend_installation.supabase"
    ) as mock_supabase:
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            "some_value"
        )

        result = unsuspend_installation(12345)
        assert (
            result is None
        )  # Should return None due to decorator default_return_value
