from unittest.mock import Mock, patch
import pytest
import json
import requests
from services.supabase.owners.create_owner import create_owner
from tests.constants import OWNER


def test_create_owner_success():
    mock_response = Mock()
    mock_response.data = [{"owner_id": 123, "owner_name": "test_owner"}]
    
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True
        mock_supabase.table.assert_called_once_with("owners")
        mock_table.insert.assert_called_once_with({
            "owner_id": 123,
            "owner_name": "test_owner",
            "stripe_customer_id": "",
            "created_by": "456:test_user",
            "updated_by": "456:test_user",
            "owner_type": "",
            "org_rules": "",
        })
        mock_table.execute.assert_called_once()


def test_create_owner_success_with_all_parameters():
    mock_response = Mock()
    mock_response.data = [{"owner_id": 123, "owner_name": "test_owner"}]
    
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user",
            stripe_customer_id="cus_123",
            owner_type="Organization",
            org_rules="No rules"
        )
        
        assert result is True
        mock_supabase.table.assert_called_once_with("owners")
        mock_table.insert.assert_called_once_with({
            "owner_id": 123,
            "owner_name": "test_owner",
            "stripe_customer_id": "cus_123",
            "created_by": "456:test_user",
            "updated_by": "456:test_user",
            "owner_type": "Organization",
            "org_rules": "No rules",
        })
        mock_table.execute.assert_called_once()


def test_create_owner_success_with_empty_data():
    mock_response = Mock()
    mock_response.data = []
    
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is False


def test_create_owner_success_with_none_data():
    mock_response = Mock()
    mock_response.data = None
    
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is False


def test_create_owner_with_zero_ids():
    mock_response = Mock()
    mock_response.data = [{"owner_id": 0}]
    
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = create_owner(
            owner_id=0,
            owner_name="test_owner",
            user_id=0,
            user_name="test_user"
        )
        
        assert result is True
        mock_table.insert.assert_called_once_with({
            "owner_id": 0,
            "owner_name": "test_owner",
            "stripe_customer_id": "",
            "created_by": "0:test_user",
            "updated_by": "0:test_user",
            "owner_type": "",
            "org_rules": "",
        })


def test_create_owner_with_negative_ids():
    mock_response = Mock()
    mock_response.data = [{"owner_id": -1}]
    
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = create_owner(
            owner_id=-1,
            owner_name="test_owner",
            user_id=-2,
            user_name="test_user"
        )
        
        assert result is True
        mock_table.insert.assert_called_once_with({
            "owner_id": -1,
            "owner_name": "test_owner",
            "stripe_customer_id": "",
            "created_by": "-2:test_user",
            "updated_by": "-2:test_user",
            "owner_type": "",
            "org_rules": "",
        })


def test_create_owner_with_large_ids():
    mock_response = Mock()
    mock_response.data = [{"owner_id": 999999999}]
    
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = create_owner(
            owner_id=999999999,
            owner_name="test_owner",
            user_id=888888888,
            user_name="test_user"
        )
        
        assert result is True
        mock_table.insert.assert_called_once_with({
            "owner_id": 999999999,
            "owner_name": "test_owner",
            "stripe_customer_id": "",
            "created_by": "888888888:test_user",
            "updated_by": "888888888:test_user",
            "owner_type": "",
            "org_rules": "",
        })


def test_create_owner_with_special_characters():
    mock_response = Mock()
    mock_response.data = [{"owner_id": 123}]
    
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = create_owner(
            owner_id=123,
            owner_name="test-owner@example.com",
            user_id=456,
            user_name="test:user",
            stripe_customer_id="cus_123!@#",
            owner_type="Org/Team",
            org_rules="Rule #1: No spaces"
        )
        
        assert result is True
        mock_table.insert.assert_called_once_with({
            "owner_id": 123,
            "owner_name": "test-owner@example.com",
            "stripe_customer_id": "cus_123!@#",
            "created_by": "456:test:user",
            "updated_by": "456:test:user",
            "owner_type": "Org/Team",
            "org_rules": "Rule #1: No spaces",
        })


def test_create_owner_with_empty_strings():
    mock_response = Mock()
    mock_response.data = [{"owner_id": 123}]
    
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = create_owner(
            owner_id=123,
            owner_name="",
            user_id=456,
            user_name="",
            stripe_customer_id="",
            owner_type="",
            org_rules=""
        )
        
        assert result is True
        mock_table.insert.assert_called_once_with({
            "owner_id": 123,
            "owner_name": "",
            "stripe_customer_id": "",
            "created_by": "456:",
            "updated_by": "456:",
            "owner_type": "",
            "org_rules": "",
        })


def test_create_owner_http_error_exception():
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        
        mock_response = Mock()
        mock_response.status_code = 409
        mock_response.reason = "Conflict"
        mock_response.text = "Duplicate key"
        http_error = requests.exceptions.HTTPError(response=mock_response)
        mock_table.execute.side_effect = http_error
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True


def test_create_owner_json_decode_error():
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True


def test_create_owner_attribute_error():
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_supabase.table.side_effect = AttributeError("Attribute error")
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True


def test_create_owner_key_error():
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_supabase.table.side_effect = KeyError("Key error")
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True


def test_create_owner_type_error():
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_supabase.table.side_effect = TypeError("Type error")
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True


def test_create_owner_generic_exception():
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Generic error")
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True


def test_create_owner_http_500_error():
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Server error"
        http_error = requests.exceptions.HTTPError(response=mock_response)
        mock_table.execute.side_effect = http_error
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True


def test_create_owner_http_422_error():
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.reason = "Unprocessable Entity"
        mock_response.text = "Validation error"
        http_error = requests.exceptions.HTTPError(response=mock_response)
        mock_table.execute.side_effect = http_error
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True


def test_create_owner_execute_exception():
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.side_effect = Exception("Execute error")
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True


def test_create_owner_insert_exception():
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.side_effect = Exception("Insert error")
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True


def test_create_owner_table_exception():
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Table error")
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True


def test_create_owner_with_unicode_characters():
    mock_response = Mock()
    mock_response.data = [{"owner_id": 123}]
    
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True