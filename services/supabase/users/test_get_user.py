import os
from unittest.mock import patch, MagicMock

import pytest

from services.supabase.users.get_user import get_user


def _mock_response(data):
    mock = MagicMock()
    mock.data = data
    return mock


@pytest.fixture
def sample_user_data():
    return {
        "user_id": 123,
        "user_name": "test_user",
        "email": "test@example.com",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
    }


def test_get_user_returns_user_when_found(sample_user_data):
    with patch("services.supabase.users.get_user.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = _mock_response(
            [sample_user_data]
        )

        result = get_user(user_id=123)

        assert result == sample_user_data


def test_get_user_returns_none_when_not_found():
    with patch("services.supabase.users.get_user.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = _mock_response(
            []
        )

        result = get_user(user_id=999)

        assert result is None


def test_get_user_returns_first_user_when_multiple_found(sample_user_data):
    with patch("services.supabase.users.get_user.supabase") as mock_supabase:
        second_user_data = {
            "user_id": 124,
            "user_name": "second_user",
            "email": "second@example.com",
            "created_at": "2023-01-02T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z",
        }
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = _mock_response(
            [sample_user_data, second_user_data]
        )

        result = get_user(user_id=123)

        assert result is not None
        assert result == sample_user_data
        assert result["user_id"] == 123


def test_get_user_handles_supabase_exception():
    with patch("services.supabase.users.get_user.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database connection error")

        result = get_user(user_id=123)

        assert result is None


def test_get_user_handles_malformed_response():
    with patch("services.supabase.users.get_user.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = _mock_response(
            None
        )

        result = get_user(user_id=123)

        assert result is None


@pytest.mark.parametrize("user_id", [1, 999999, 0, -1])
def test_get_user_with_various_user_ids(user_id):
    with patch("services.supabase.users.get_user.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = _mock_response(
            []
        )

        result = get_user(user_id=user_id)

        assert result is None


@pytest.mark.skipif(bool(os.environ.get("CI")), reason="Integration test")
def test_get_user_integration():
    result = get_user(46782860)
    assert result is not None
    assert result["user_id"] == 46782860

    result = get_user(999999999)
    assert result is None
