from unittest.mock import patch, MagicMock

from tests.constants import OWNER, REPO
from services.supabase.repositories.upsert_repository import upsert_repository


def test_upsert_repository_existing_owner():
    """Test upsert_repository when owner exists"""
    with patch("services.supabase.repositories.upsert_repository.get_owner") as mock_get_owner, \
         patch("services.supabase.repositories.upsert_repository.supabase") as mock_supabase:
        # Mock owner exists
        mock_get_owner.return_value = {"owner_id": 123, "owner_name": OWNER}
        
        # Mock repository doesn't exist yet
        mock_select = MagicMock()
        mock_execute = MagicMock()
        mock_execute.execute.return_value.data = []
        mock_select.eq.return_value = mock_execute
        mock_supabase.table.return_value.select.return_value = mock_select
        
        # Mock insert operation
        mock_insert = MagicMock()
        mock_insert_execute = MagicMock()
        mock_insert_execute.execute.return_value.data = [{"repo_id": 456, "repo_name": REPO}]
        mock_insert.insert.return_value = mock_insert_execute
        mock_supabase.table.return_value = mock_insert
        
        # Call the function
        result = upsert_repository(
            owner_id=123,
            owner_name=OWNER,
            repo_id=456,
            repo_name=REPO,
            user_id=789,
            user_name="testuser",
            file_count=100,
            blank_lines=200,
            comment_lines=300,
            code_lines=400
        )
        
        # Verify the result
        assert result == {"repo_id": 456, "repo_name": REPO}
        
        # Verify get_owner was called
        mock_get_owner.assert_called_once_with(123)
        
        # Verify create_owner was not called (since owner exists)
        
        # Verify repository check was performed
        mock_supabase.table.assert_called_with("repositories")
        
        # Verify insert was called with correct data
        mock_insert.insert.assert_called_once_with({
            "owner_id": 123,
            "repo_id": 456,
            "repo_name": REPO,
            "created_by": "789:testuser",
            "updated_by": "789:testuser",
            "file_count": 100,
            "blank_lines": 200,
            "comment_lines": 300,
            "code_lines": 400,
        })


def test_upsert_repository_non_existing_owner():
    """Test upsert_repository when owner doesn't exist"""
    with patch("services.supabase.repositories.upsert_repository.get_owner") as mock_get_owner, \
         patch("services.supabase.repositories.upsert_repository.create_owner") as mock_create_owner, \
         patch("services.supabase.repositories.upsert_repository.supabase") as mock_supabase:
        # Mock owner doesn't exist
        mock_get_owner.return_value = None
        
        # Mock create_owner
        mock_create_owner.return_value = True
        
        # Mock repository doesn't exist yet
        mock_select = MagicMock()
        mock_execute = MagicMock()
        mock_execute.execute.return_value.data = []
        mock_select.eq.return_value = mock_execute
        mock_supabase.table.return_value.select.return_value = mock_select
        
        # Mock insert operation
        mock_insert = MagicMock()
        mock_insert_execute = MagicMock()
        mock_insert_execute.execute.return_value.data = [{"repo_id": 456, "repo_name": REPO}]
        mock_insert.insert.return_value = mock_insert_execute
        mock_supabase.table.return_value = mock_insert
        
        # Call the function
        result = upsert_repository(
            owner_id=123,
            owner_name=OWNER,
            repo_id=456,
            repo_name=REPO,
            user_id=789,
            user_name="testuser"
        )
        
        # Verify the result
        assert result == {"repo_id": 456, "repo_name": REPO}
        
        # Verify get_owner was called
        mock_get_owner.assert_called_once_with(123)
        
        # Verify create_owner was called with correct parameters
        mock_create_owner.assert_called_once_with(
            owner_id=123,
            owner_name=OWNER,
            user_id=789,
            user_name="testuser"
        )


def test_upsert_repository_existing_repo():
    """Test upsert_repository when repository already exists"""
    with patch("services.supabase.repositories.upsert_repository.get_owner") as mock_get_owner, \
         patch("services.supabase.repositories.upsert_repository.supabase") as mock_supabase:
        # Mock owner exists
        mock_get_owner.return_value = {"owner_id": 123, "owner_name": OWNER}
        
        # Mock repository exists
        mock_select = MagicMock()
        mock_execute = MagicMock()
        mock_execute.execute.return_value.data = [{"repo_id": 456, "repo_name": REPO}]
        mock_select.eq.return_value = mock_execute
        mock_supabase.table.return_value.select.return_value = mock_select
        
        # Mock update operation
        mock_update = MagicMock()
        mock_eq = MagicMock()
        mock_update_execute = MagicMock()
        mock_update_execute.execute.return_value.data = [{"repo_id": 456, "repo_name": REPO, "updated": True}]
        mock_eq.eq.return_value = mock_update_execute
        mock_update.update.return_value = mock_eq
        mock_supabase.table.return_value = mock_update
        
        # Call the function
        result = upsert_repository(
            owner_id=123,
            owner_name=OWNER,
            repo_id=456,
            repo_name=REPO,
            user_id=789,
            user_name="testuser",
            file_count=100,
            blank_lines=200,
            comment_lines=300,
            code_lines=400
        )
        
        # Verify the result
        assert result == {"repo_id": 456, "repo_name": REPO, "updated": True}
        
        # Verify update was called with correct data
        mock_update.update.assert_called_once_with({
            "updated_by": "789:testuser",
            "file_count": 100,
            "blank_lines": 200,
            "comment_lines": 300,
            "code_lines": 400,
        })


def test_upsert_repository_update_no_data():
    """Test upsert_repository when update returns no data"""
    with patch("services.supabase.repositories.upsert_repository.get_owner") as mock_get_owner, \
         patch("services.supabase.repositories.upsert_repository.supabase") as mock_supabase:
        # Mock owner exists
        mock_get_owner.return_value = {"owner_id": 123, "owner_name": OWNER}
        
        # Mock repository exists
        mock_select = MagicMock()
        mock_execute = MagicMock()
        mock_execute.execute.return_value.data = [{"repo_id": 456, "repo_name": REPO}]
        mock_select.eq.return_value = mock_execute
        mock_supabase.table.return_value.select.return_value = mock_select
        
        # Mock update operation with no data returned
        mock_update = MagicMock()
        mock_eq = MagicMock()
        mock_update_execute = MagicMock()
        mock_update_execute.execute.return_value.data = []  # Empty data
        mock_eq.eq.return_value = mock_update_execute
        mock_update.update.return_value = mock_eq
        mock_supabase.table.return_value = mock_update
        
        # Call the function
        result = upsert_repository(
            owner_id=123,
            owner_name=OWNER,
            repo_id=456,
            repo_name=REPO,
            user_id=789,
            user_name="testuser"
        )
        
        # Verify the result is None when no data is returned
        assert result is None


def test_upsert_repository_insert_no_data():
    """Test upsert_repository when insert returns no data"""
    with patch("services.supabase.repositories.upsert_repository.get_owner") as mock_get_owner, \
         patch("services.supabase.repositories.upsert_repository.supabase") as mock_supabase:
        # Mock owner exists
        mock_get_owner.return_value = {"owner_id": 123, "owner_name": OWNER}
        
        # Mock repository doesn't exist
        mock_select = MagicMock()
        mock_execute = MagicMock()
        mock_execute.execute.return_value.data = []
        mock_select.eq.return_value = mock_execute
        mock_supabase.table.return_value.select.return_value = mock_select
        
        # Mock insert operation with no data returned
        mock_insert = MagicMock()
        mock_insert_execute = MagicMock()
        mock_insert_execute.execute.return_value.data = []  # Empty data
        mock_insert.insert.return_value = mock_insert_execute
        mock_supabase.table.return_value = mock_insert
        
        # Call the function
        result = upsert_repository(
            owner_id=123,
            owner_name=OWNER,
            repo_id=456,
            repo_name=REPO,
            user_id=789,
            user_name="testuser"
        )
        
        # Verify the result is None when no data is returned
        assert result is None


def test_upsert_repository_exception_handling():
    """Test exception handling in upsert_repository"""
    with patch("services.supabase.repositories.upsert_repository.get_owner") as mock_get_owner:
        # Mock get_owner to raise an exception
        mock_get_owner.side_effect = Exception("Test exception")
        
        # Call the function
        result = upsert_repository(
            owner_id=123,
            owner_name=OWNER,
            repo_id=456,
            repo_name=REPO,
            user_id=789,
            user_name="testuser"
        )
        
        # Verify the result is None due to exception handling
        assert result is None