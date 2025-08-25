from unittest.mock import patch, MagicMock

import pytest

from services.supabase.users.upsert_user import upsert_user


@pytest.fixture
def mock_supabase():
    """Fixture to mock the Supabase client"""
    with patch("services.supabase.users.upsert_user.supabase") as mock_supabase:
        # Create a chain of mocks to handle the method chaining
        mock_table = MagicMock()
        mock_upsert = MagicMock()
        mock_execute = MagicMock()

        # Set up the chain
        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = mock_execute

        yield mock_supabase


@pytest.fixture
def mock_check_email_is_valid():
    """Fixture to mock the email validation function"""
    with patch(
        "services.supabase.users.upsert_user.check_email_is_valid"
    ) as mock_check:
        yield mock_check


def test_upsert_user_with_valid_email(mock_supabase, mock_check_email_is_valid):
    """Test upsert_user with a valid email"""
    # Setup
    user_id = 123
    user_name = "test_user"
    email = "valid@example.com"
    mock_check_email_is_valid.return_value = True

    # Execute
    upsert_user(user_id=user_id, user_name=user_name, email=email)

    # Assert
    mock_check_email_is_valid.assert_called_once_with(email=email)
    mock_supabase.table.assert_called_once_with(table_name="users")
    mock_supabase.table.return_value.upsert.assert_called_once_with(
        json={
            "user_id": user_id,
            "user_name": user_name,
            "email": email,
            "created_by": str(user_id),
        },
        on_conflict="user_id",
    )
    mock_supabase.table.return_value.upsert.return_value.execute.assert_called_once()


def test_upsert_user_with_invalid_email(mock_supabase, mock_check_email_is_valid):
    """Test upsert_user with an invalid email"""
    # Setup
    user_id = 123
    user_name = "test_user"
    email = "invalid-email"
    mock_check_email_is_valid.return_value = False

    # Execute
    upsert_user(user_id=user_id, user_name=user_name, email=email)

    # Assert
    mock_check_email_is_valid.assert_called_once_with(email=email)
    mock_supabase.table.assert_called_once_with(table_name="users")
    mock_supabase.table.return_value.upsert.assert_called_once_with(
        json={
            "user_id": user_id,
            "user_name": user_name,
            "created_by": str(user_id),
        },
        on_conflict="user_id",
    )
    mock_supabase.table.return_value.upsert.return_value.execute.assert_called_once()


def test_upsert_user_with_none_email(mock_supabase, mock_check_email_is_valid):
    """Test upsert_user with None as email"""
    # Setup
    user_id = 123
    user_name = "test_user"
    email = None
    mock_check_email_is_valid.return_value = False

    # Execute
    upsert_user(user_id=user_id, user_name=user_name, email=email)

    # Assert
    mock_check_email_is_valid.assert_called_once_with(email=email)
    mock_supabase.table.assert_called_once_with(table_name="users")
    mock_supabase.table.return_value.upsert.assert_called_once_with(
        json={
            "user_id": user_id,
            "user_name": user_name,
            "created_by": str(user_id),
        },
        on_conflict="user_id",
    )
    mock_supabase.table.return_value.upsert.return_value.execute.assert_called_once()


def test_upsert_user_exception_handling(mock_supabase, mock_check_email_is_valid):
    """Test exception handling in upsert_user"""
    # Setup
    user_id = 123
    user_name = "test_user"
    email = "valid@example.com"
    mock_check_email_is_valid.return_value = True
    mock_supabase.table.side_effect = Exception("Database error")

    # Execute - should not raise an exception due to handle_exceptions decorator
    result = upsert_user(user_id=user_id, user_name=user_name, email=email)

    # Assert
    assert result is None  # Default return value from handle_exceptions
    mock_check_email_is_valid.assert_called_once_with(email=email)
    mock_supabase.table.assert_called_once_with(table_name="users")
