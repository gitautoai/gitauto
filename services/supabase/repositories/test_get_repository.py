from unittest.mock import Mock, patch
import pytest

from services.supabase.repositories.get_repository import get_repository
from schemas.supabase.fastapi.schema_public_latest import Repositories


def test_get_repository_success():
    """Test get_repository returns correct repository data when found."""
    mock_result = Mock()
    mock_result.data = [{
        "id": 1,
        "repo_id": 123456,
        "repo_name": "test-repo",
        "owner_id": 789,
        "created_by": "user:test",
        "updated_by": "user:test",
        "file_count": 100,
        "blank_lines": 50,
        "comment_lines": 30,
        "code_lines": 200,
        "target_branch": "main",
        "trigger_on_commit": True,
        "trigger_on_merged": False,
        "trigger_on_pr_change": True,
        "trigger_on_review_comment": False,
        "trigger_on_schedule": False,
        "trigger_on_test_failure": True,
        "schedule_execution_count": 0,
        "schedule_include_weekends": False,
        "schedule_interval_minutes": 60,
    }]
    
    with patch("services.supabase.repositories.get_repository.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = get_repository(123456)
        
        assert result is not None
        assert isinstance(result, dict)
        assert result["repo_id"] == 123456
        assert result["repo_name"] == "test-repo"
        assert result["owner_id"] == 789
        
        # Verify the database query was made correctly
        mock_supabase.table.assert_called_once_with("repositories")
        mock_supabase.table.return_value.select.assert_called_once_with("*")
        mock_supabase.table.return_value.select.return_value.eq.assert_called_once_with("repo_id", 123456)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.assert_called_once()


def test_get_repository_not_found_empty_data():
    """Test get_repository returns None when no data is found."""
    mock_result = Mock()
    mock_result.data = []
    
    with patch("services.supabase.repositories.get_repository.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = get_repository(999999)
        
        assert result is None
        mock_supabase.table.assert_called_once_with("repositories")
        mock_supabase.table.return_value.select.return_value.eq.assert_called_once_with("repo_id", 999999)


def test_get_repository_not_found_none_data():
    """Test get_repository returns None when data is None."""
    mock_result = Mock()
    mock_result.data = None
    
    with patch("services.supabase.repositories.get_repository.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = get_repository(999999)
        
        assert result is None
        mock_supabase.table.assert_called_once_with("repositories")


def test_get_repository_first_item_none():
    """Test get_repository returns None when first item in data is None."""
    mock_result = Mock()
    mock_result.data = [None]
    
    with patch("services.supabase.repositories.get_repository.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = get_repository(123456)
        
        assert result is None
        mock_supabase.table.assert_called_once_with("repositories")


def test_get_repository_first_item_empty_dict():
    """Test get_repository returns None when first item in data is empty dict."""
    mock_result = Mock()
    mock_result.data = [{}]
    
    with patch("services.supabase.repositories.get_repository.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = get_repository(123456)
        
        assert result is None
        mock_supabase.table.assert_called_once_with("repositories")


def test_get_repository_multiple_results():
    """Test get_repository returns first result when multiple repositories found."""
    mock_result = Mock()
    mock_result.data = [
        {
            "id": 1,
            "repo_id": 123456,
            "repo_name": "first-repo",
            "owner_id": 789,
            "created_by": "user:test",
            "updated_by": "user:test",
        },
        {
            "id": 2,
            "repo_id": 123456,
            "repo_name": "second-repo",
            "owner_id": 789,
            "created_by": "user:test",
            "updated_by": "user:test",
        }
    ]
    
    with patch("services.supabase.repositories.get_repository.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = get_repository(123456)
        
        assert result is not None
        assert result["repo_name"] == "first-repo"  # Should return first result
        assert result["id"] == 1


def test_get_repository_exception_handling():
    """Test get_repository handles exceptions and returns None due to decorator."""
    with patch("services.supabase.repositories.get_repository.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database connection error")
        
        result = get_repository(123456)
        
        # Due to @handle_exceptions decorator with default_return_value=None
        assert result is None


def test_get_repository_attribute_error():
    """Test get_repository handles AttributeError and returns None."""
    with patch("services.supabase.repositories.get_repository.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = AttributeError("'NoneType' object has no attribute 'execute'")
        
        result = get_repository(123456)
        
        assert result is None


def test_get_repository_key_error():
    """Test get_repository handles KeyError and returns None."""
    mock_result = Mock()
    # Simulate a result object that doesn't have expected attributes
    del mock_result.data
    
    with patch("services.supabase.repositories.get_repository.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = get_repository(123456)
        
        assert result is None


def test_get_repository_with_different_repo_ids():
    """Test get_repository works with different repo_id values."""
    test_cases = [
        (1, "repo-1"),
        (999999999, "large-repo-id"),
        (0, "zero-repo"),
    ]
    
    for repo_id, repo_name in test_cases:
        mock_result = Mock()
        mock_result.data = [{
            "id": 1,
            "repo_id": repo_id,
            "repo_name": repo_name,
            "owner_id": 789,
            "created_by": "user:test",
            "updated_by": "user:test",
        }]
        
        with patch("services.supabase.repositories.get_repository.supabase") as mock_supabase:
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
            
            result = get_repository(repo_id)
            
            assert result is not None
            assert result["repo_id"] == repo_id
            assert result["repo_name"] == repo_name
            mock_supabase.table.return_value.select.return_value.eq.assert_called_with("repo_id", repo_id)
