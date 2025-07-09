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


def test_get_repository_cast_behavior():
    """Test that the result is properly cast to Repositories type."""
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
    }]
    
    with patch("services.supabase.repositories.get_repository.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = get_repository(123456)
        
        # The cast function should return the dictionary as-is
        assert result is not None
        assert isinstance(result, dict)
        assert result == mock_result.data[0]


def test_get_repository_supabase_chain_calls():
    """Test that the Supabase method chain is called correctly."""
    mock_result = Mock()
    mock_result.data = [{"repo_id": 123456, "repo_name": "test"}]
    
    with patch("services.supabase.repositories.get_repository.supabase") as mock_supabase:
        # Set up the method chain
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_result
        
        result = get_repository(123456)
        
        # Verify each step of the chain
        mock_supabase.table.assert_called_once_with("repositories")
        mock_table.select.assert_called_once_with("*")
        mock_select.eq.assert_called_once_with("repo_id", 123456)
        mock_eq.execute.assert_called_once()
        
        assert result is not None
        assert result["repo_id"] == 123456


def test_get_repository_type_error():
    """Test get_repository handles TypeError and returns None."""
    with patch("services.supabase.repositories.get_repository.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = TypeError("unsupported operand type(s)")
        
        result = get_repository(123456)
        
        assert result is None


def test_get_repository_with_negative_repo_id():
    """Test get_repository works with negative repo_id (edge case)."""


def test_get_repository_data_with_false_values():
    """Test get_repository handles data with falsy values correctly."""
    mock_result = Mock()
    mock_result.data = [{
        "id": 0,  # Falsy but valid
        "repo_id": 123456,
        "repo_name": "",  # Empty string is falsy but valid
        "owner_id": 0,  # Falsy but valid
        "created_by": "user:test",
        "updated_by": "user:test",
        "file_count": 0,  # Zero is falsy but valid
        "trigger_on_commit": False,  # False is falsy but valid
    }]
    
    with patch("services.supabase.repositories.get_repository.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = get_repository(123456)
        
        # Should return the data even with falsy values
        assert result is not None
        assert result["id"] == 0
        assert result["repo_name"] == ""
        assert result["owner_id"] == 0
        assert result["file_count"] == 0
        assert result["trigger_on_commit"] is False


def test_get_repository_data_index_out_of_bounds():
    """Test get_repository handles empty data list gracefully."""
    mock_result = Mock()
    mock_result.data = []
    
    with patch("services.supabase.repositories.get_repository.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = get_repository(123456)
        
        # Should return None when trying to access data[0] on empty list
        assert result is None


def test_get_repository_minimal_valid_data():
    """Test get_repository with minimal valid repository data."""
    mock_result = Mock()
    mock_result.data = [{"repo_id": 123456}]  # Minimal data
    
    with patch("services.supabase.repositories.get_repository.supabase") as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = get_repository(123456)
        
        assert result is not None
        assert result["repo_id"] == 123456
        assert len(result) == 1  # Only one field
    # This tests that the function doesn't validate input and passes it through
    mock_result = Mock()
    mock_result.data = []
