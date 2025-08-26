# pylint: disable=redefined-outer-name

# Standard imports
from unittest.mock import patch

# Third party imports
import pytest

# Local imports
from services.supabase.repositories.upsert_repository import upsert_repository


@pytest.fixture
def mocks():
    with patch(
        "services.supabase.repositories.upsert_repository.get_owner"
    ) as mock_get_owner, patch(
        "services.supabase.repositories.upsert_repository.create_owner"
    ) as mock_create_owner, patch(
        "services.supabase.repositories.upsert_repository.get_repository"
    ) as mock_get_repository, patch(
        "services.supabase.repositories.upsert_repository.update_repository"
    ) as mock_update_repository, patch(
        "services.supabase.repositories.upsert_repository.insert_repository"
    ) as mock_insert_repository:

        yield {
            "get_owner": mock_get_owner,
            "create_owner": mock_create_owner,
            "get_repository": mock_get_repository,
            "update_repository": mock_update_repository,
            "insert_repository": mock_insert_repository,
        }


def test_upsert_repository_owner_exists_repo_exists(mocks):
    mock_owner = {"owner_id": 123, "owner_name": "test_owner"}
    mock_repository = {"repo_id": 456, "repo_name": "test_repo"}
    mock_update_result = {"repo_id": 456, "updated": True}

    mocks["get_owner"].return_value = mock_owner
    mocks["get_repository"].return_value = mock_repository
    mocks["update_repository"].return_value = mock_update_result

    result = upsert_repository(
        owner_id=123,
        owner_name="test_owner",
        repo_id=456,
        repo_name="test_repo",
        user_id=789,
        user_name="test_user",
        file_count=10,
        blank_lines=5,
        comment_lines=3,
        code_lines=20,
    )

    assert result == mock_update_result
    mocks["get_owner"].assert_called_once_with(123)
    mocks["get_repository"].assert_called_once_with(456)
    mocks["update_repository"].assert_called_once_with(
        repo_id=456,
        updated_by="789:test_user",
        file_count=10,
        blank_lines=5,
        comment_lines=3,
        code_lines=20,
    )


def test_upsert_repository_owner_not_exists_repo_not_exists(mocks):
    mocks["get_owner"].return_value = None
    mocks["get_repository"].return_value = None
    mocks["insert_repository"].return_value = {"repo_id": 456, "created": True}

    result = upsert_repository(
        owner_id=123,
        owner_name="test_owner",
        repo_id=456,
        repo_name="test_repo",
        user_id=789,
        user_name="test_user",
    )

    assert result == {"repo_id": 456, "created": True}
    mocks["get_owner"].assert_called_once_with(123)
    mocks["create_owner"].assert_called_once_with(
        owner_id=123, owner_name="test_owner", user_id=789, user_name="test_user"
    )
    mocks["get_repository"].assert_called_once_with(456)
    mocks["insert_repository"].assert_called_once_with(
        owner_id=123,
        repo_id=456,
        repo_name="test_repo",
        user_id=789,
        user_name="test_user",
        file_count=0,
        blank_lines=0,
        comment_lines=0,
        code_lines=0,
    )


def test_upsert_repository_owner_exists_repo_not_exists(mocks):
    mock_owner = {"owner_id": 123, "owner_name": "test_owner"}
    mocks["get_owner"].return_value = mock_owner
    mocks["get_repository"].return_value = None
    mocks["insert_repository"].return_value = {"repo_id": 456, "created": True}

    result = upsert_repository(
        owner_id=123,
        owner_name="test_owner",
        repo_id=456,
        repo_name="test_repo",
        user_id=789,
        user_name="test_user",
        file_count=15,
        blank_lines=8,
        comment_lines=4,
        code_lines=25,
    )

    assert result == {"repo_id": 456, "created": True}
    mocks["get_owner"].assert_called_once_with(123)
    mocks["get_repository"].assert_called_once_with(456)
    mocks["insert_repository"].assert_called_once_with(
        owner_id=123,
        repo_id=456,
        repo_name="test_repo",
        user_id=789,
        user_name="test_user",
        file_count=15,
        blank_lines=8,
        comment_lines=4,
        code_lines=25,
    )


def test_upsert_repository_update_no_data_returned(mocks):
    mock_owner = {"owner_id": 123, "owner_name": "test_owner"}
    mock_repository = {"repo_id": 456, "repo_name": "test_repo"}

    mocks["get_owner"].return_value = mock_owner
    mocks["get_repository"].return_value = mock_repository
    mocks["update_repository"].return_value = None

    result = upsert_repository(
        owner_id=123,
        owner_name="test_owner",
        repo_id=456,
        repo_name="test_repo",
        user_id=789,
        user_name="test_user",
    )

    assert result is None
    mocks["get_owner"].assert_called_once_with(123)
    mocks["get_repository"].assert_called_once_with(456)
    mocks["update_repository"].assert_called_once_with(
        repo_id=456,
        updated_by="789:test_user",
        file_count=0,
        blank_lines=0,
        comment_lines=0,
        code_lines=0,
    )


def test_upsert_repository_insert_no_data_returned(mocks):
    mock_owner = {"owner_id": 123, "owner_name": "test_owner"}

    mocks["get_owner"].return_value = mock_owner
    mocks["get_repository"].return_value = None
    mocks["insert_repository"].return_value = None

    result = upsert_repository(
        owner_id=123,
        owner_name="test_owner",
        repo_id=456,
        repo_name="test_repo",
        user_id=789,
        user_name="test_user",
    )

    assert result is None
    mocks["get_owner"].assert_called_once_with(123)
    mocks["get_repository"].assert_called_once_with(456)
    mocks["insert_repository"].assert_called_once_with(
        owner_id=123,
        repo_id=456,
        repo_name="test_repo",
        user_id=789,
        user_name="test_user",
        file_count=0,
        blank_lines=0,
        comment_lines=0,
        code_lines=0,
    )


def test_upsert_repository_with_default_parameters(mocks):
    mock_owner = {"owner_id": 123, "owner_name": "test_owner"}
    mock_insert_result = {"repo_id": 456, "created": True}

    mocks["get_owner"].return_value = mock_owner
    mocks["get_repository"].return_value = None
    mocks["insert_repository"].return_value = mock_insert_result

    result = upsert_repository(
        owner_id=123,
        owner_name="test_owner",
        repo_id=456,
        repo_name="test_repo",
        user_id=789,
        user_name="test_user",
    )

    assert result == mock_insert_result
    mocks["get_owner"].assert_called_once_with(123)
    mocks["get_repository"].assert_called_once_with(456)
    mocks["insert_repository"].assert_called_once_with(
        owner_id=123,
        repo_id=456,
        repo_name="test_repo",
        user_id=789,
        user_name="test_user",
        file_count=0,
        blank_lines=0,
        comment_lines=0,
        code_lines=0,
    )


def test_upsert_repository_owner_not_exists_create_owner_called(mocks):
    mocks["get_owner"].return_value = None
    mocks["get_repository"].return_value = None
    mocks["insert_repository"].return_value = {"repo_id": 456, "created": True}

    upsert_repository(
        owner_id=123,
        owner_name="test_owner",
        repo_id=456,
        repo_name="test_repo",
        user_id=789,
        user_name="test_user",
    )

    mocks["create_owner"].assert_called_once_with(
        owner_id=123, owner_name="test_owner", user_id=789, user_name="test_user"
    )


def test_upsert_repository_owner_exists_create_owner_not_called(mocks):
    mock_owner = {"owner_id": 123, "owner_name": "test_owner"}
    mock_repository = {"repo_id": 456, "repo_name": "test_repo"}
    mock_update_result = {"repo_id": 456, "updated": True}

    mocks["get_owner"].return_value = mock_owner
    mocks["get_repository"].return_value = mock_repository
    mocks["update_repository"].return_value = mock_update_result

    upsert_repository(
        owner_id=123,
        owner_name="test_owner",
        repo_id=456,
        repo_name="test_repo",
        user_id=789,
        user_name="test_user",
    )

    mocks["create_owner"].assert_not_called()


def test_upsert_repository_string_formatting(mocks):
    mock_owner = {"owner_id": 123, "owner_name": "test_owner"}
    mock_insert_result = {"repo_id": 456, "created": True}

    mocks["get_owner"].return_value = mock_owner
    mocks["get_repository"].return_value = None
    mocks["insert_repository"].return_value = mock_insert_result

    upsert_repository(
        owner_id=123,
        owner_name="test_owner",
        repo_id=456,
        repo_name="test_repo",
        user_id=789,
        user_name="test_user",
    )

    mocks["insert_repository"].assert_called_once_with(
        owner_id=123,
        repo_id=456,
        repo_name="test_repo",
        user_id=789,
        user_name="test_user",
        file_count=0,
        blank_lines=0,
        comment_lines=0,
        code_lines=0,
    )
