import json
from unittest.mock import Mock, patch
import requests
from requests.exceptions import HTTPError

from tests.constants import OWNER, REPO
from services.supabase.usage.update_retry_pairs import update_retry_workflow_id_hash_pairs


def test_update_retry_workflow_id_hash_pairs_success():
    mock_response = Mock()
    mock_response.data = [{"id": 1}]
    
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["hash1", "hash2"])
        
        assert result is None
        mock_supabase.table.assert_called_once_with("usage")
        mock_table.update.assert_called_once_with({
            "retry_workflow_id_hash_pairs": ["hash1", "hash2"],
            "is_completed": True,
        })
        assert mock_table.eq.call_count == 3
        mock_table.eq.assert_any_call("owner_id", 123)
        mock_table.eq.assert_any_call("repo_id", 456)
        mock_table.eq.assert_any_call("pr_number", 789)
        mock_table.execute.assert_called_once()


def test_update_retry_workflow_id_hash_pairs_with_empty_pairs():
    mock_response = Mock()
    mock_response.data = [{"id": 1}]
    
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, [])
        
        assert result is None
        mock_table.update.assert_called_once_with({
            "retry_workflow_id_hash_pairs": [],
            "is_completed": True,
        })


def test_update_retry_workflow_id_hash_pairs_with_single_pair():
    mock_response = Mock()
    mock_response.data = [{"id": 1}]
    
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["single_hash"])
        
        assert result is None
        mock_table.update.assert_called_once_with({
            "retry_workflow_id_hash_pairs": ["single_hash"],
            "is_completed": True,
        })


def test_update_retry_workflow_id_hash_pairs_with_zero_values():
    mock_response = Mock()
    mock_response.data = [{"id": 1}]
    
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = update_retry_workflow_id_hash_pairs(0, 0, 0, ["hash1"])
        
        assert result is None
        mock_table.eq.assert_any_call("owner_id", 0)
        mock_table.eq.assert_any_call("repo_id", 0)
        mock_table.eq.assert_any_call("pr_number", 0)


def test_update_retry_workflow_id_hash_pairs_with_negative_values():
    mock_response = Mock()
    mock_response.data = [{"id": 1}]
    
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = update_retry_workflow_id_hash_pairs(-1, -2, -3, ["hash1"])
        
        assert result is None
        mock_table.eq.assert_any_call("owner_id", -1)
        mock_table.eq.assert_any_call("repo_id", -2)
        mock_table.eq.assert_any_call("pr_number", -3)


def test_update_retry_workflow_id_hash_pairs_with_large_values():
    mock_response = Mock()
    mock_response.data = [{"id": 1}]
    
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = update_retry_workflow_id_hash_pairs(999999999, 888888888, 777777777, ["hash_large"])
        
        assert result is None
        mock_table.eq.assert_any_call("owner_id", 999999999)
        mock_table.eq.assert_any_call("repo_id", 888888888)
        mock_table.eq.assert_any_call("pr_number", 777777777)


def test_update_retry_workflow_id_hash_pairs_with_many_pairs():
    mock_response = Mock()
    mock_response.data = [{"id": 1}]
    large_pairs_list = [f"hash_{i}" for i in range(100)]
    
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, large_pairs_list)
        
        assert result is None
        mock_table.update.assert_called_once_with({
            "retry_workflow_id_hash_pairs": large_pairs_list,
            "is_completed": True,
        })


def test_update_retry_workflow_id_hash_pairs_with_exception():
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["hash1"])
        
        assert result is None


def test_update_retry_workflow_id_hash_pairs_with_attribute_error():
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = AttributeError("Attribute error")
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["hash1"])
        
        assert result is None


def test_update_retry_workflow_id_hash_pairs_with_key_error():
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = KeyError("Key error")
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["hash1"])
        
        assert result is None


def test_update_retry_workflow_id_hash_pairs_with_type_error():
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = TypeError("Type error")
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["hash1"])
        
        assert result is None


def test_update_retry_workflow_id_hash_pairs_with_json_decode_error():
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = json.JSONDecodeError("JSON error", "", 0)
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["hash1"])
        
        assert result is None


def test_update_retry_workflow_id_hash_pairs_with_update_exception():
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.side_effect = Exception("Update error")
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["hash1"])
        
        assert result is None


def test_update_retry_workflow_id_hash_pairs_with_eq_exception():
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.side_effect = Exception("Eq error")
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["hash1"])
        
        assert result is None


def test_update_retry_workflow_id_hash_pairs_with_execute_exception():
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.side_effect = Exception("Execute error")
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["hash1"])
        
        assert result is None


def test_update_retry_workflow_id_hash_pairs_with_special_characters_in_pairs():
    mock_response = Mock()
    mock_response.data = [{"id": 1}]
    special_pairs = ["hash@#$%", "hash with spaces", "hash\nwith\nnewlines", "hash\twith\ttabs"]
    
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, special_pairs)
        
        assert result is None
        mock_table.update.assert_called_once_with({
            "retry_workflow_id_hash_pairs": special_pairs,
            "is_completed": True,
        })


def test_update_retry_workflow_id_hash_pairs_with_unicode_pairs():
    mock_response = Mock()
    mock_response.data = [{"id": 1}]
    unicode_pairs = ["hash_🚀", "hash_中文", "hash_العربية", "hash_русский"]
    
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, unicode_pairs)
        
        assert result is None
        mock_table.update.assert_called_once_with({
            "retry_workflow_id_hash_pairs": unicode_pairs,
            "is_completed": True,
        })


def test_update_retry_workflow_id_hash_pairs_with_very_long_hash():
    mock_response = Mock()
    mock_response.data = [{"id": 1}]
    very_long_hash = "a" * 10000
    
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, [very_long_hash])
        
        assert result is None
        mock_table.update.assert_called_once_with({
            "retry_workflow_id_hash_pairs": [very_long_hash],
            "is_completed": True,
        })


def test_update_retry_workflow_id_hash_pairs_with_empty_string_pairs():
    mock_response = Mock()
    mock_response.data = [{"id": 1}]
    
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["", "  ", "\n"])
        
        assert result is None
        mock_table.update.assert_called_once_with({
            "retry_workflow_id_hash_pairs": ["", "  ", "\n"],
            "is_completed": True,
        })


def test_update_retry_workflow_id_hash_pairs_with_http_error():
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.reason = "Internal Server Error"
    mock_response.text = "Server error"
    
    http_error = HTTPError("500 Server Error")
    http_error.response = mock_response
    
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = http_error
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["hash1"])
        
        assert result is None


def test_update_retry_workflow_id_hash_pairs_with_http_error_403():
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "Access denied"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Used": "1"
    }
    
    http_error = HTTPError("403 Forbidden")
    http_error.response = mock_response
    
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = http_error
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["hash1"])
        
        assert result is None


def test_update_retry_workflow_id_hash_pairs_with_runtime_error():
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = RuntimeError("Runtime error")
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["hash1"])
        
        assert result is None


def test_update_retry_workflow_id_hash_pairs_with_connection_error():
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = ConnectionError("Connection failed")
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["hash1"])
        
        assert result is None


def test_update_retry_workflow_id_hash_pairs_with_timeout_error():
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = TimeoutError("Request timed out")
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["hash1"])
        
        assert result is None


def test_update_retry_workflow_id_hash_pairs_with_value_error():
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = ValueError("Invalid value")
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["hash1"])
        
        assert result is None


def test_update_retry_workflow_id_hash_pairs_with_index_error():
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = IndexError("Index out of range")
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["hash1"])
        
        assert result is None


def test_update_retry_workflow_id_hash_pairs_with_os_error():
    with patch("services.supabase.usage.update_retry_pairs.supabase") as mock_supabase:
        mock_supabase.table.side_effect = OSError("OS error")
        
        result = update_retry_workflow_id_hash_pairs(123, 456, 789, ["hash1"])
        
        assert result is None