from unittest.mock import Mock, patch

from tests.constants import OWNER, REPO
from services.supabase.usage.get_retry_pairs import get_retry_workflow_id_hash_pairs


def test_get_retry_workflow_id_hash_pairs_with_valid_data():
    mock_response = Mock()
    mock_response.data = [{"retry_workflow_id_hash_pairs": ["hash1", "hash2", "hash3"]}]
    
    with patch("services.supabase.usage.get_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = get_retry_workflow_id_hash_pairs(123, 456, 789)
        
        assert result == ["hash1", "hash2", "hash3"]
        mock_supabase.table.assert_called_once_with("usage")
        mock_table.select.assert_called_once_with("retry_workflow_id_hash_pairs")
        assert mock_table.eq.call_count == 3
        mock_table.eq.assert_any_call("owner_id", 123)
        mock_table.eq.assert_any_call("repo_id", 456)
        mock_table.eq.assert_any_call("pr_number", 789)
        mock_table.order.assert_called_once_with("created_at", desc=True)
        mock_table.limit.assert_called_once_with(1)
        mock_table.execute.assert_called_once()


def test_get_retry_workflow_id_hash_pairs_with_empty_response_data():
    mock_response = Mock()
    mock_response.data = []
    
    with patch("services.supabase.usage.get_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = get_retry_workflow_id_hash_pairs(123, 456, 789)
        
        assert result == []


def test_get_retry_workflow_id_hash_pairs_with_none_response_data():
    mock_response = Mock()
    mock_response.data = None
    
    with patch("services.supabase.usage.get_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = get_retry_workflow_id_hash_pairs(123, 456, 789)
        
        assert result == []


def test_get_retry_workflow_id_hash_pairs_with_none_retry_pairs():
    mock_response = Mock()
    mock_response.data = [{"retry_workflow_id_hash_pairs": None}]
    
    with patch("services.supabase.usage.get_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = get_retry_workflow_id_hash_pairs(123, 456, 789)
        
        assert result == []


def test_get_retry_workflow_id_hash_pairs_with_missing_key():
    mock_response = Mock()
    mock_response.data = [{}]
    
    with patch("services.supabase.usage.get_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = get_retry_workflow_id_hash_pairs(123, 456, 789)
        
        assert result == []


def test_get_retry_workflow_id_hash_pairs_with_exception():
    with patch("services.supabase.usage.get_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = get_retry_workflow_id_hash_pairs(123, 456, 789)
        
        assert result == []


def test_get_retry_workflow_id_hash_pairs_with_empty_list():
    mock_response = Mock()
    mock_response.data = [{"retry_workflow_id_hash_pairs": []}]
    
    with patch("services.supabase.usage.get_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = get_retry_workflow_id_hash_pairs(123, 456, 789)
        
        assert result == []
