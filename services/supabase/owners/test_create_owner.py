from unittest.mock import Mock, patch
import time
import pytest
import requests
import json
from services.supabase.owners.create_owner import create_owner
from tests.constants import OWNER


def test_create_owner_success_with_all_parameters():
    mock_table = Mock()
    mock_insert = Mock()
    mock_execute = Mock()
    
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_execute
    
    with patch('services.supabase.owners.create_owner.supabase') as mock_supabase:
        mock_supabase.table.return_value = mock_table
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user",
            stripe_customer_id="cus_123",
            owner_type="Organization",
            org_rules="test rules"
        )
        
        mock_supabase.table.assert_called_once_with("owners")
        mock_table.insert.assert_called_once_with({
            "owner_id": 123,
            "owner_name": "test_owner",
            "stripe_customer_id": "cus_123",
            "created_by": "456:test_user",
            "updated_by": "456:test_user",
            "owner_type": "Organization",
            "org_rules": "test rules",
        })
        mock_insert.execute.assert_called_once()
        assert result is None


def test_create_owner_success_with_minimal_parameters():
    mock_table = Mock()
    mock_insert = Mock()
    mock_execute = Mock()
    
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_execute
    
    with patch('services.supabase.owners.create_owner.supabase') as mock_supabase:
        mock_supabase.table.return_value = mock_table
        
        result = create_owner(
            owner_id=789,
            owner_name=OWNER,
            user_id=101,
            user_name="minimal_user"
        )
        
        mock_supabase.table.assert_called_once_with("owners")
        mock_table.insert.assert_called_once_with({
            "owner_id": 789,
            "owner_name": OWNER,
            "stripe_customer_id": "",
            "created_by": "101:minimal_user",
            "updated_by": "101:minimal_user",
            "owner_type": "",
            "org_rules": "",
        })
        mock_insert.execute.assert_called_once()
        assert result is None


def test_create_owner_http_error_403():
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "Access denied"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Used": "1"
    }
    
    http_error = requests.exceptions.HTTPError(response=mock_response)
    
    with patch('services.supabase.owners.create_owner.supabase') as mock_supabase:
        mock_supabase.table.side_effect = http_error
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is None


def test_create_owner_http_error_500():
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.reason = "Internal Server Error"
    mock_response.text = "Server error"
    
    http_error = requests.exceptions.HTTPError(response=mock_response)
    
    with patch('services.supabase.owners.create_owner.supabase') as mock_supabase:
        mock_supabase.table.side_effect = http_error
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is None


def test_create_owner_json_decode_error():
    json_error = json.JSONDecodeError("Invalid JSON", "bad json", 0)
    
    with patch('services.supabase.owners.create_owner.supabase') as mock_supabase:
        mock_supabase.table.side_effect = json_error
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is None


def test_create_owner_generic_exception():
    with patch('services.supabase.owners.create_owner.supabase') as mock_supabase:
        mock_supabase.table.side_effect = Exception("Generic error")
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is None


def test_create_owner_with_special_characters():
    mock_table = Mock()
    mock_insert = Mock()
    mock_execute = Mock()
    
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_execute
    
    with patch('services.supabase.owners.create_owner.supabase') as mock_supabase:
        mock_supabase.table.return_value = mock_table
        
        result = create_owner(
            owner_id=999,
            owner_name="owner@test.com",
            user_id=888,
            user_name="user:with:colons",
            stripe_customer_id="cus_special!@#",
            owner_type="User",
            org_rules="rules with\nnewlines"
        )
        
        mock_supabase.table.assert_called_once_with("owners")
        mock_table.insert.assert_called_once_with({
            "owner_id": 999,
            "owner_name": "owner@test.com",
            "stripe_customer_id": "cus_special!@#",
            "created_by": "888:user:with:colons",
            "updated_by": "888:user:with:colons",
            "owner_type": "User",
            "org_rules": "rules with\nnewlines",
        })
        mock_insert.execute.assert_called_once()
        assert result is None


def test_create_owner_with_zero_ids():
    mock_table = Mock()
    mock_insert = Mock()
    mock_execute = Mock()
    
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_execute
    
    with patch('services.supabase.owners.create_owner.supabase') as mock_supabase:
        mock_supabase.table.return_value = mock_table
        
        result = create_owner(
            owner_id=0,
            owner_name="zero_owner",
            user_id=0,
            user_name="zero_user"
        )
        
        mock_supabase.table.assert_called_once_with("owners")
        mock_table.insert.assert_called_once_with({
            "owner_id": 0,
            "owner_name": "zero_owner",
            "stripe_customer_id": "",
            "created_by": "0:zero_user",
            "updated_by": "0:zero_user",
            "owner_type": "",
            "org_rules": "",
        })
        mock_insert.execute.assert_called_once()
        assert result is None


def test_create_owner_with_negative_ids():
    mock_table = Mock()
    mock_insert = Mock()
    mock_execute = Mock()
    
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_execute
    
    with patch('services.supabase.owners.create_owner.supabase') as mock_supabase:
        mock_supabase.table.return_value = mock_table
        
        result = create_owner(
            owner_id=-1,
            owner_name="negative_owner",
            user_id=-999,
            user_name="negative_user"
        )
        
        mock_supabase.table.assert_called_once_with("owners")
        mock_table.insert.assert_called_once_with({
            "owner_id": -1,
            "owner_name": "negative_owner",
            "stripe_customer_id": "",
            "created_by": "-999:negative_user",
            "updated_by": "-999:negative_user",
            "owner_type": "",
            "org_rules": "",
        })
        mock_insert.execute.assert_called_once()
        assert result is None


def test_create_owner_rate_limit_exceeded():
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "Rate limit exceeded"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Used": "5000",
        "X-RateLimit-Reset": str(int(time.time()) + 60)
    }
    
    http_error = requests.exceptions.HTTPError(response=mock_response)
    
    with patch('services.supabase.owners.create_owner.supabase') as mock_supabase:
        mock_supabase.table.side_effect = http_error
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is None


def test_create_owner_secondary_rate_limit():
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "You have exceeded a secondary rate limit"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Used": "1",
        "Retry-After": "30"
    }
    
    http_error = requests.exceptions.HTTPError(response=mock_response)
    
    with patch('services.supabase.owners.create_owner.supabase') as mock_supabase:
        mock_supabase.table.side_effect = http_error
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is None


def test_create_owner_execute_fails():
    mock_table = Mock()
    mock_insert = Mock()
    
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.side_effect = Exception("Execute failed")
    
    with patch('services.supabase.owners.create_owner.supabase') as mock_supabase:
        mock_supabase.table.return_value = mock_table
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        mock_supabase.table.assert_called_once_with("owners")
        mock_table.insert.assert_called_once()
        mock_insert.execute.assert_called_once()
        assert result is None


def test_create_owner_attribute_error():
    with patch('services.supabase.owners.create_owner.supabase') as mock_supabase:
        mock_supabase.table.side_effect = AttributeError("'NoneType' object has no attribute 'table'")
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is None


def test_create_owner_insert_fails():
    mock_table = Mock()
    mock_table.insert.side_effect = Exception("Insert failed")
    
    with patch('services.supabase.owners.create_owner.supabase') as mock_supabase:
        mock_supabase.table.return_value = mock_table
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        mock_supabase.table.assert_called_once_with("owners")
        mock_table.insert.assert_called_once()
        assert result is None


def test_create_owner_with_empty_strings():
    mock_table = Mock()
    mock_insert = Mock()
    mock_execute = Mock()
    
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_execute
    
    with patch('services.supabase.owners.create_owner.supabase') as mock_supabase:
        mock_supabase.table.return_value = mock_table
        
        result = create_owner(
            owner_id=555,
            owner_name="",
            user_id=666,
            user_name="",
            stripe_customer_id="",
            owner_type="",
            org_rules=""
        )
        
        mock_supabase.table.assert_called_once_with("owners")
        mock_table.insert.assert_called_once_with({
            "owner_id": 555,
            "owner_name": "",
            "stripe_customer_id": "",
            "created_by": "666:",
            "updated_by": "666:",
            "owner_type": "",
            "org_rules": "",
        })
        mock_insert.execute.assert_called_once()
        assert result is None


def test_create_owner_with_large_ids():
    mock_table = Mock()
    mock_insert = Mock()
    mock_execute = Mock()
    
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_execute
    
    with patch('services.supabase.owners.create_owner.supabase') as mock_supabase:
        mock_supabase.table.return_value = mock_table
        
        result = create_owner(
            owner_id=999999999,
            owner_name="large_owner",
            user_id=888888888,
            user_name="large_user"
        )
        
        mock_supabase.table.assert_called_once_with("owners")
        mock_table.insert.assert_called_once_with({
            "owner_id": 999999999,
            "owner_name": "large_owner",
            "stripe_customer_id": "",
            "created_by": "888888888:large_user",
            "updated_by": "888888888:large_user",
            "owner_type": "",
            "org_rules": "",
        })
        mock_insert.execute.assert_called_once()
        assert result is None