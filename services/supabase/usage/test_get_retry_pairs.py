import json
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


def test_get_retry_workflow_id_hash_pairs_with_single_hash():
    mock_response = Mock()
    mock_response.data = [{"retry_workflow_id_hash_pairs": ["single_hash"]}]
    
    with patch("services.supabase.usage.get_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = get_retry_workflow_id_hash_pairs(123, 456, 789)
        
        assert result == ["single_hash"]


def test_get_retry_workflow_id_hash_pairs_with_attribute_error():
    with patch("services.supabase.usage.get_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = AttributeError("Attribute error")
        
        result = get_retry_workflow_id_hash_pairs(123, 456, 789)
        
        assert result == []


def test_get_retry_workflow_id_hash_pairs_with_key_error():
    with patch("services.supabase.usage.get_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = KeyError("Key error")
        
        result = get_retry_workflow_id_hash_pairs(123, 456, 789)
        
        assert result == []


def test_get_retry_workflow_id_hash_pairs_with_type_error():
    with patch("services.supabase.usage.get_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = TypeError("Type error")
        
        result = get_retry_workflow_id_hash_pairs(123, 456, 789)
        
        assert result == []


def test_get_retry_workflow_id_hash_pairs_with_json_decode_error():
    with patch("services.supabase.usage.get_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = json.JSONDecodeError("JSON error", "", 0)
        
        result = get_retry_workflow_id_hash_pairs(123, 456, 789)
        
        assert result == []


def test_get_retry_workflow_id_hash_pairs_with_zero_values():
    mock_response = Mock()
    mock_response.data = [{"retry_workflow_id_hash_pairs": ["hash1", "hash2"]}]
    
    with patch("services.supabase.usage.get_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = get_retry_workflow_id_hash_pairs(0, 0, 0)
        
        assert result == ["hash1", "hash2"]
        mock_table.eq.assert_any_call("owner_id", 0)
        mock_table.eq.assert_any_call("repo_id", 0)
        mock_table.eq.assert_any_call("pr_number", 0)


def test_get_retry_workflow_id_hash_pairs_with_negative_values():
    mock_response = Mock()
    mock_response.data = [{"retry_workflow_id_hash_pairs": ["hash1"]}]
    
    with patch("services.supabase.usage.get_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = get_retry_workflow_id_hash_pairs(-1, -2, -3)
        
        assert result == ["hash1"]
        mock_table.eq.assert_any_call("owner_id", -1)
        mock_table.eq.assert_any_call("repo_id", -2)
        mock_table.eq.assert_any_call("pr_number", -3)


def test_get_retry_workflow_id_hash_pairs_with_large_values():
    mock_response = Mock()
    mock_response.data = [{"retry_workflow_id_hash_pairs": ["hash_large"]}]
    
    with patch("services.supabase.usage.get_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = get_retry_workflow_id_hash_pairs(999999999, 888888888, 777777777)
        
        assert result == ["hash_large"]
        mock_table.eq.assert_any_call("owner_id", 999999999)
        mock_table.eq.assert_any_call("repo_id", 888888888)
        mock_table.eq.assert_any_call("pr_number", 777777777)


def test_get_retry_workflow_id_hash_pairs_with_response_data_multiple_records():
    mock_response = Mock()
    mock_response.data = [
        {"retry_workflow_id_hash_pairs": ["hash1", "hash2"]},
        {"retry_workflow_id_hash_pairs": ["hash3", "hash4"]}
    ]
    
    with patch("services.supabase.usage.get_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = get_retry_workflow_id_hash_pairs(123, 456, 789)
        
        assert result == ["hash1", "hash2"]


def test_get_retry_workflow_id_hash_pairs_with_response_execute_exception():
    with patch("services.supabase.usage.get_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.side_effect = Exception("Execute error")
        
        result = get_retry_workflow_id_hash_pairs(123, 456, 789)
        
        assert result == []


def test_get_retry_workflow_id_hash_pairs_with_response_data_access_exception():
    mock_response = Mock()
    # Create a mock object that raises KeyError when get() is called
    mock_dict = Mock()
    mock_dict.get.side_effect = KeyError("Key error")
    
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
