from unittest.mock import Mock, patch

from services.supabase.repositories.upsert_repository import upsert_repository


def test_upsert_repository_owner_exists_repo_exists():
    mock_owner = {"owner_id": 123, "owner_name": "test_owner"}
    mock_repo_data = [{"repo_id": 456, "repo_name": "test_repo"}]
    mock_update_data = [{"repo_id": 456, "updated": True}]

    with patch(
        "services.supabase.repositories.upsert_repository.get_owner"
    ) as mock_get_owner, patch(
        "services.supabase.repositories.upsert_repository.supabase"
    ) as mock_supabase:

        mock_get_owner.return_value = mock_owner

        mock_select_result = Mock()
        mock_select_result.data = mock_repo_data

        mock_update_result = Mock()
        mock_update_result.data = mock_update_data

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = (
            mock_select_result
        )
        mock_table.update.return_value.eq.return_value.execute.return_value = (
            mock_update_result
        )

        mock_supabase.table.return_value = mock_table

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

        assert result == mock_update_data[0]
        mock_get_owner.assert_called_once_with(123)
        mock_supabase.table.assert_called_with("repositories")


def test_upsert_repository_owner_not_exists_repo_not_exists():
    mock_insert_data = [{"repo_id": 456, "created": True}]

    with patch(
        "services.supabase.repositories.upsert_repository.get_owner"
    ) as mock_get_owner, patch(
        "services.supabase.repositories.upsert_repository.create_owner"
    ) as mock_create_owner, patch(
        "services.supabase.repositories.upsert_repository.supabase"
    ) as mock_supabase:

        mock_get_owner.return_value = None

        mock_select_result = Mock()
        mock_select_result.data = []

        mock_insert_result = Mock()
        mock_insert_result.data = mock_insert_data

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = (
            mock_select_result
        )
        mock_table.insert.return_value.execute.return_value = mock_insert_result

        mock_supabase.table.return_value = mock_table

        result = upsert_repository(
            owner_id=123,
            owner_name="test_owner",
            repo_id=456,
            repo_name="test_repo",
            user_id=789,
            user_name="test_user",
        )

        assert result == mock_insert_data[0]
        mock_get_owner.assert_called_once_with(123)
        mock_create_owner.assert_called_once_with(
            owner_id=123, owner_name="test_owner", user_id=789, user_name="test_user"
        )


def test_upsert_repository_owner_exists_repo_not_exists():
    mock_owner = {"owner_id": 123, "owner_name": "test_owner"}
    mock_insert_data = [{"repo_id": 456, "created": True}]

    with patch(
        "services.supabase.repositories.upsert_repository.get_owner"
    ) as mock_get_owner, patch(
        "services.supabase.repositories.upsert_repository.supabase"
    ) as mock_supabase:

        mock_get_owner.return_value = mock_owner

        mock_select_result = Mock()
        mock_select_result.data = []

        mock_insert_result = Mock()
        mock_insert_result.data = mock_insert_data

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = (
            mock_select_result
        )
        mock_table.insert.return_value.execute.return_value = mock_insert_result

        mock_supabase.table.return_value = mock_table

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

        assert result == mock_insert_data[0]
        mock_get_owner.assert_called_once_with(123)


def test_upsert_repository_update_no_data_returned():
    mock_owner = {"owner_id": 123, "owner_name": "test_owner"}
    mock_repo_data = [{"repo_id": 456, "repo_name": "test_repo"}]

    with patch(
        "services.supabase.repositories.upsert_repository.get_owner"
    ) as mock_get_owner, patch(
        "services.supabase.repositories.upsert_repository.supabase"
    ) as mock_supabase:

        mock_get_owner.return_value = mock_owner

        mock_select_result = Mock()
        mock_select_result.data = mock_repo_data

        mock_update_result = Mock()
        mock_update_result.data = []

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = (
            mock_select_result
        )
        mock_table.update.return_value.eq.return_value.execute.return_value = (
            mock_update_result
        )

        mock_supabase.table.return_value = mock_table

        result = upsert_repository(
            owner_id=123,
            owner_name="test_owner",
            repo_id=456,
            repo_name="test_repo",
            user_id=789,
            user_name="test_user",
        )

        assert result is None


def test_upsert_repository_insert_no_data_returned():
    mock_owner = {"owner_id": 123, "owner_name": "test_owner"}

    with patch(
        "services.supabase.repositories.upsert_repository.get_owner"
    ) as mock_get_owner, patch(
        "services.supabase.repositories.upsert_repository.supabase"
    ) as mock_supabase:

        mock_get_owner.return_value = mock_owner

        mock_select_result = Mock()
        mock_select_result.data = []

        mock_insert_result = Mock()
        mock_insert_result.data = []

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = (
            mock_select_result
        )
        mock_table.insert.return_value.execute.return_value = mock_insert_result

        mock_supabase.table.return_value = mock_table

        result = upsert_repository(
            owner_id=123,
            owner_name="test_owner",
            repo_id=456,
            repo_name="test_repo",
            user_id=789,
            user_name="test_user",
        )

        assert result is None


def test_upsert_repository_with_default_parameters():
    mock_owner = {"owner_id": 123, "owner_name": "test_owner"}
    mock_insert_data = [{"repo_id": 456, "created": True}]

    with patch(
        "services.supabase.repositories.upsert_repository.get_owner"
    ) as mock_get_owner, patch(
        "services.supabase.repositories.upsert_repository.supabase"
    ) as mock_supabase:

        mock_get_owner.return_value = mock_owner

        mock_select_result = Mock()
        mock_select_result.data = []

        mock_insert_result = Mock()
        mock_insert_result.data = mock_insert_data

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = (
            mock_select_result
        )
        mock_table.insert.return_value.execute.return_value = mock_insert_result

        mock_supabase.table.return_value = mock_table

        result = upsert_repository(
            owner_id=123,
            owner_name="test_owner",
            repo_id=456,
            repo_name="test_repo",
            user_id=789,
            user_name="test_user",
        )

        assert result == mock_insert_data[0]

        insert_call_args = mock_table.insert.call_args[0][0]
        assert insert_call_args["file_count"] == 0
        assert insert_call_args["blank_lines"] == 0
        assert insert_call_args["comment_lines"] == 0
        assert insert_call_args["code_lines"] == 0


def test_upsert_repository_owner_not_exists_create_owner_called():
    mock_insert_data = [{"repo_id": 456, "created": True}]

    with patch(
        "services.supabase.repositories.upsert_repository.get_owner"
    ) as mock_get_owner, patch(
        "services.supabase.repositories.upsert_repository.create_owner"
    ) as mock_create_owner, patch(
        "services.supabase.repositories.upsert_repository.supabase"
    ) as mock_supabase:

        mock_get_owner.return_value = None

        mock_select_result = Mock()
        mock_select_result.data = []

        mock_insert_result = Mock()
        mock_insert_result.data = mock_insert_data

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = (
            mock_select_result
        )
        mock_table.insert.return_value.execute.return_value = mock_insert_result

        mock_supabase.table.return_value = mock_table

        upsert_repository(
            owner_id=123,
            owner_name="test_owner",
            repo_id=456,
            repo_name="test_repo",
            user_id=789,
            user_name="test_user",
        )

        mock_create_owner.assert_called_once_with(
            owner_id=123, owner_name="test_owner", user_id=789, user_name="test_user"
        )


def test_upsert_repository_owner_exists_create_owner_not_called():
    mock_owner = {"owner_id": 123, "owner_name": "test_owner"}
    mock_repo_data = [{"repo_id": 456, "repo_name": "test_repo"}]
    mock_update_data = [{"repo_id": 456, "updated": True}]

    with patch(
        "services.supabase.repositories.upsert_repository.get_owner"
    ) as mock_get_owner, patch(
        "services.supabase.repositories.upsert_repository.create_owner"
    ) as mock_create_owner, patch(
        "services.supabase.repositories.upsert_repository.supabase"
    ) as mock_supabase:

        mock_get_owner.return_value = mock_owner

        mock_select_result = Mock()
        mock_select_result.data = mock_repo_data

        mock_update_result = Mock()
        mock_update_result.data = mock_update_data

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = (
            mock_select_result
        )
        mock_table.update.return_value.eq.return_value.execute.return_value = (
            mock_update_result
        )

        mock_supabase.table.return_value = mock_table

        upsert_repository(
            owner_id=123,
            owner_name="test_owner",
            repo_id=456,
            repo_name="test_repo",
            user_id=789,
            user_name="test_user",
        )

        mock_create_owner.assert_not_called()


def test_upsert_repository_string_formatting():
    mock_owner = {"owner_id": 123, "owner_name": "test_owner"}
    mock_insert_data = [{"repo_id": 456, "created": True}]

    with patch(
        "services.supabase.repositories.upsert_repository.get_owner"
    ) as mock_get_owner, patch(
        "services.supabase.repositories.upsert_repository.supabase"
    ) as mock_supabase:

        mock_get_owner.return_value = mock_owner

        mock_select_result = Mock()
        mock_select_result.data = []

        mock_insert_result = Mock()
        mock_insert_result.data = mock_insert_data

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = (
            mock_select_result
        )
        mock_table.insert.return_value.execute.return_value = mock_insert_result

        mock_supabase.table.return_value = mock_table

        upsert_repository(
            owner_id=123,
            owner_name="test_owner",
            repo_id=456,
            repo_name="test_repo",
            user_id=789,
            user_name="test_user",
        )

        insert_call_args = mock_table.insert.call_args[0][0]
        assert insert_call_args["created_by"] == "789:test_user"
        assert insert_call_args["updated_by"] == "789:test_user"
