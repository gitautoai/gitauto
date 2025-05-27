from unittest.mock import Mock, patch
import json
import requests

from tests.constants import OWNER
from services.supabase.owners.create_owner import create_owner


def test_create_owner_success():
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
            user_name="test_user",
            stripe_customer_id="cus_123",
            owner_type="Organization",
            org_rules="test rules"
        )
        
        assert result is True
        mock_table.insert.assert_called_once_with({
            "owner_id": 123,
            "owner_name": "test_owner",
            "stripe_customer_id": "cus_123",
            "created_by": "456:test_user",
            "updated_by": "456:test_user",
            "owner_type": "Organization",
            "org_rules": "test rules",
        })


def test_create_owner_failure_none_data():
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


def test_create_owner_failure_empty_data():
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


def test_create_owner_with_zero_user_id():
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
            user_id=0,
            user_name="test_user"
        )
        
        assert result is True
        mock_table.insert.assert_called_once_with({
            "owner_id": 123,
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
            user_name=""
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
            owner_name="test@owner!",
            user_id=456,
            user_name="test:user",
            stripe_customer_id="cus_123@test",
            owner_type="Org:Type",
            org_rules="rule1\nrule2"
        )
        
        assert result is True
        mock_table.insert.assert_called_once_with({
            "owner_id": 123,
            "owner_name": "test@owner!",
            "stripe_customer_id": "cus_123@test",
            "created_by": "456:test:user",
            "updated_by": "456:test:user",
            "owner_type": "Org:Type",
            "org_rules": "rule1\nrule2",
        })


def test_create_owner_with_large_values():
    mock_response = Mock()
    mock_response.data = [{"owner_id": 999999999}]
    
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = create_owner(
            owner_id=999999999,
            owner_name="a" * 1000,
            user_id=888888888,
            user_name="b" * 500
        )
        
        assert result is True
        mock_table.insert.assert_called_once_with({
            "owner_id": 999999999,
            "owner_name": "a" * 1000,
            "stripe_customer_id": "",
            "created_by": f"888888888:{'b' * 500}",
            "updated_by": f"888888888:{'b' * 500}",
            "owner_type": "",
            "org_rules": "",
        })


def test_create_owner_supabase_table_exception():
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True


def test_create_owner_supabase_insert_exception():
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


def test_create_owner_supabase_execute_exception():
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


def test_create_owner_http_error_500():
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Server error"
        
        http_error = requests.exceptions.HTTPError("500 Server Error")
        http_error.response = mock_response
        
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.side_effect = http_error
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True


def test_create_owner_http_error_other():
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.reason = "Bad Request"
        mock_response.text = "Invalid data"
        
        http_error = requests.exceptions.HTTPError("400 Bad Request")
        http_error.response = mock_response
        
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
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
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.side_effect = AttributeError("Attribute error")
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True


def test_create_owner_key_error():
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.side_effect = KeyError("Key error")
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True


def test_create_owner_type_error():
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.side_effect = TypeError("Type error")
        
        result = create_owner(
            owner_id=123,
            owner_name="test_owner",
            user_id=456,
            user_name="test_user"
        )
        
        assert result is True


def test_create_owner_response_data_attribute_error():
    mock_response = Mock()
    del mock_response.data
    
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
            owner_name="测试用户",
            user_id=456,
            user_name="ユーザー",
            stripe_customer_id="cus_🎉",
            owner_type="組織",
            org_rules="规则1\n规则2"
        )
        
        assert result is True
        mock_table.insert.assert_called_once_with({
            "owner_id": 123,
            "owner_name": "测试用户",
            "stripe_customer_id": "cus_🎉",
            "created_by": "456:ユーザー",
            "updated_by": "456:ユーザー",
            "owner_type": "組織",
            "org_rules": "规则1\n规则2",
        })


def test_create_owner_with_constants():
    mock_response = Mock()
    mock_response.data = [{"owner_id": 159883862}]
    
    with patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = create_owner(
            owner_id=159883862,
            owner_name=OWNER,
            user_id=123,
            user_name="test_user"
        )
        
        assert result is True
        mock_table.insert.assert_called_once_with({
            "owner_id": 159883862,
            "owner_name": OWNER,
            "stripe_customer_id": "",
            "created_by": "123:test_user",
            "updated_by": "123:test_user",
            "owner_type": "",
            "org_rules": "",
        })
