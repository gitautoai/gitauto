from unittest.mock import patch

import pytest

from services.supabase.users.get_user import get_user


@pytest.fixture
def sample_user_data():
    """Fixture providing sample user data."""
    return {
        "user_id": 123,
        "user_name": "test_user",
        "email": "test@example.com",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
    }


def test_get_user_returns_user_when_found(sample_user_data):
    """Test that get_user returns user data when user is found."""
    with patch("services.supabase.users.get_user.supabase") as mock_supabase:
        # Setup mock to return user data
        mock_response = ((None, [sample_user_data]), "metadata")
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Call function
        result = get_user(user_id=123)

        # Verify result
        assert result == sample_user_data


def test_get_user_returns_none_when_not_found():
    """Test that get_user returns None when user is not found."""
    with patch("services.supabase.users.get_user.supabase") as mock_supabase:
        # Setup mock to return empty data
        mock_response = ((None, []), "metadata")
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Call function
        result = get_user(user_id=999)

        # Verify result
        assert result is None


def test_get_user_returns_first_user_when_multiple_found(sample_user_data):
    """Test that get_user returns the first user when multiple users are found."""
    with patch("services.supabase.users.get_user.supabase") as mock_supabase:
        # Create multiple user data
        second_user_data = {
            "user_id": 124,
            "user_name": "second_user",
            "email": "second@example.com",
            "created_at": "2023-01-02T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z",
        }
        mock_response = ((None, [sample_user_data, second_user_data]), "metadata")
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Call function
        result = get_user(user_id=123)

        # Verify result - should return first user
        assert result is not None
        assert result == sample_user_data
        assert result["user_id"] == 123
        assert result["user_name"] == "test_user"


def test_get_user_handles_supabase_exception():
    """Test that get_user handles exceptions gracefully and returns None."""
    with patch("services.supabase.users.get_user.supabase") as mock_supabase:
        # Setup mock to raise exception
        mock_supabase.table.side_effect = Exception("Database connection error")

        # Call function
        result = get_user(user_id=123)

        # Verify result - should return None due to exception handling
        assert result is None


def test_get_user_handles_malformed_response():
    """Test that get_user handles malformed response gracefully."""
    with patch("services.supabase.users.get_user.supabase") as mock_supabase:
        # Setup mock with malformed response
        mock_response = ((None, None), "metadata")  # Invalid response structure
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Call function
        result = get_user(user_id=123)

        # Verify result - should return None due to exception handling
        assert result is None


@pytest.mark.parametrize(
    "user_id",
    [
        1,
        999999,
        0,
        -1,
    ],
)
def test_get_user_with_various_user_ids(user_id):
    """Test that get_user handles various user ID formats correctly."""
    with patch("services.supabase.users.get_user.supabase") as mock_supabase:
        # Setup mock to return empty data
        mock_response = ((None, []), "metadata")
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Call function
        result = get_user(user_id=user_id)

        # Verify result
        assert result is None


def test_get_user_type_annotation_compliance(sample_user_data):
    """Test that get_user returns the correct type as per annotation."""
    with patch("services.supabase.users.get_user.supabase") as mock_supabase:
        mock_response = ((None, [sample_user_data]), "metadata")
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        result = get_user(user_id=123)

        # Verify type compliance
        assert isinstance(result, dict)
        assert all(isinstance(key, str) for key in result.keys())
