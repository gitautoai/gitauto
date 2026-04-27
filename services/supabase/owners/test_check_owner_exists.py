import os
from unittest.mock import patch, MagicMock

import pytest

from config import TEST_OWNER_ID
from services.supabase.owners.check_owner_exists import check_owner_exists


def _mock_response(data):
    mock = MagicMock()
    mock.data = data
    return mock


@pytest.fixture
def mock_supabase_client():
    with patch("services.supabase.owners.check_owner_exists.supabase") as mock:
        yield mock


def test_check_owner_exists_returns_true_when_owner_found(mock_supabase_client):
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()

    mock_supabase_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.eq.return_value = mock_eq
    mock_eq.execute.return_value = _mock_response([{"owner_id": TEST_OWNER_ID}])

    result = check_owner_exists(platform="github", owner_id=TEST_OWNER_ID)

    assert result is True
    mock_supabase_client.table.assert_called_once_with(table_name="owners")
    mock_table.select.assert_called_once_with("owner_id")
    mock_select.eq.assert_called_once_with(column="platform", value="github")
    mock_eq.eq.assert_called_once_with(column="owner_id", value=TEST_OWNER_ID)


def test_check_owner_exists_returns_false_when_owner_not_found(mock_supabase_client):
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()

    mock_supabase_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.eq.return_value = mock_eq
    mock_eq.execute.return_value = _mock_response([])

    result = check_owner_exists(platform="github", owner_id=TEST_OWNER_ID)

    assert result is False


def test_check_owner_exists_returns_false_when_data_is_none(mock_supabase_client):
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()

    mock_supabase_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.eq.return_value = mock_eq
    mock_eq.execute.return_value = _mock_response(None)

    result = check_owner_exists(platform="github", owner_id=TEST_OWNER_ID)

    assert result is False


def test_check_owner_exists_with_different_owner_ids(mock_supabase_client):
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()

    mock_supabase_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.eq.return_value = mock_eq

    test_owner_ids = [123, 456, 789, 999999]

    for owner_id in test_owner_ids:
        mock_eq.execute.return_value = _mock_response([{"owner_id": owner_id}])
        result = check_owner_exists(platform="github", owner_id=owner_id)
        assert result is True
        mock_select.eq.assert_called_with(column="platform", value="github")
        mock_eq.eq.assert_called_with(column="owner_id", value=owner_id)


@pytest.mark.parametrize(
    "owner_id,expected_data,expected_result",
    [
        (123, [{"owner_id": 123}], True),
        (456, [], False),
        (789, [{"owner_id": 789}, {"owner_id": 999}], True),
        (0, [], False),
        (-1, [], False),
        (999999, [{"owner_id": 999999}], True),
    ],
)
def test_check_owner_exists_with_various_scenarios(
    mock_supabase_client, owner_id, expected_data, expected_result
):
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()

    mock_supabase_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.eq.return_value = mock_eq
    mock_eq.execute.return_value = _mock_response(expected_data)

    result = check_owner_exists(platform="github", owner_id=owner_id)

    assert result is expected_result


def test_check_owner_exists_exception_handling_returns_default():
    with patch("services.supabase.owners.check_owner_exists.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database connection error")
        result = check_owner_exists(platform="github", owner_id=TEST_OWNER_ID)
        assert result is False


def test_check_owner_exists_boolean_conversion():
    with patch("services.supabase.owners.check_owner_exists.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.eq.return_value = mock_eq

        mock_eq.execute.return_value = _mock_response([{"owner_id": TEST_OWNER_ID}])
        result = check_owner_exists(platform="github", owner_id=TEST_OWNER_ID)
        assert result is True
        assert isinstance(result, bool)

        mock_eq.execute.return_value = _mock_response([])
        result = check_owner_exists(platform="github", owner_id=TEST_OWNER_ID)
        assert result is False
        assert isinstance(result, bool)

        mock_eq.execute.return_value = _mock_response(None)
        result = check_owner_exists(platform="github", owner_id=TEST_OWNER_ID)
        assert result is False
        assert isinstance(result, bool)


@pytest.mark.skipif(bool(os.environ.get("CI")), reason="Integration test")
def test_check_owner_exists_integration():
    result = check_owner_exists(platform="github", owner_id=159883862)
    assert result is True

    result = check_owner_exists(platform="github", owner_id=999999999)
    assert result is False
