from datetime import datetime
from unittest.mock import patch, MagicMock

from services.supabase.usage.is_request_limit_reached import is_request_limit_reached, DEFAULT


def test_is_request_limit_reached_exception_owner():
    """Test that exception owners are never limited"""
    # Arrange
    installation_id = 12345
    owner_id = 67890
    owner_name = "gitautoai"  # Exception owner
    
    # Act
    result = is_request_limit_reached(
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
    )
    
    # Assert
    assert result["is_limit_reached"] is False
    assert result["requests_left"] == 999999
    assert result["request_limit"] == 999999
    assert result["is_credit_user"] is False
    assert result["credit_balance_usd"] == 0


def test_is_request_limit_reached_no_stripe_customer_creation_fails():
    """Test when no Stripe customer exists and creation fails"""
    # Arrange
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    
    # Act
    with patch("services.supabase.usage.is_request_limit_reached.get_stripe_customer_id") as mock_get_customer, \
         patch("services.supabase.usage.is_request_limit_reached.create_stripe_customer") as mock_create_customer:
        
        mock_get_customer.return_value = None
        mock_create_customer.return_value = None  # Creation fails
        
        result = is_request_limit_reached(
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
        )
    
    # Assert
    assert result["is_limit_reached"] is True
    assert result["requests_left"] == 0
    assert result["request_limit"] == 0
    assert result["is_credit_user"] is False
    assert result["credit_balance_usd"] == 0


def test_is_request_limit_reached_no_stripe_customer_creation_succeeds():
    """Test when no Stripe customer exists but creation succeeds"""
    # Arrange
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    stripe_customer_id = "cus_test123"
    
    mock_subscription = MagicMock()
    mock_subscription.current_period_start = 1640995200  # 2022-01-01
    mock_subscription.current_period_end = 1643673600    # 2022-02-01
    mock_subscription.__getitem__ = lambda self, key: {
        "items": {
            "data": [{
                "price": {
                    "product": "prod_test123",
                    "recurring": {"interval": "month"}
                },
                "quantity": 1
            }]
        }
    }[key]
    
    # Act
    with patch("services.supabase.usage.is_request_limit_reached.get_stripe_customer_id") as mock_get_customer, \
         patch("services.supabase.usage.is_request_limit_reached.create_stripe_customer") as mock_create_customer, \
         patch("services.supabase.usage.is_request_limit_reached.update_stripe_customer_id") as mock_update_customer, \
         patch("services.supabase.usage.is_request_limit_reached.get_paid_subscription") as mock_get_subscription, \
         patch("services.supabase.usage.is_request_limit_reached.get_base_request_limit") as mock_get_limit, \
         patch("services.supabase.usage.is_request_limit_reached.get_owner") as mock_get_owner, \
         patch("services.supabase.usage.is_request_limit_reached.count_completed_unique_requests") as mock_count_requests:
        
        mock_get_customer.return_value = None
        mock_create_customer.return_value = stripe_customer_id
        mock_get_subscription.return_value = mock_subscription
        mock_get_limit.return_value = 100
        mock_get_owner.return_value = {"credit_balance_usd": 0}
        mock_count_requests.return_value = ["request1", "request2"]  # 2 completed requests
        
        result = is_request_limit_reached(
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
        )
    
    # Assert
    mock_update_customer.assert_called_once_with(owner_id, stripe_customer_id)
    assert result["is_limit_reached"] is False
    assert result["requests_left"] == 98  # 100 - 2
    assert result["request_limit"] == 100
    assert result["is_credit_user"] is False


def test_is_request_limit_reached_paid_subscription_monthly():
    """Test with paid monthly subscription"""
    # Arrange
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    stripe_customer_id = "cus_test123"
    
    mock_subscription = MagicMock()
    mock_subscription.current_period_start = 1640995200  # 2022-01-01
    mock_subscription.current_period_end = 1643673600    # 2022-02-01
    mock_subscription.__getitem__ = lambda self, key: {
        "items": {
            "data": [{
                "price": {
                    "product": "prod_test123",
                    "recurring": {"interval": "month"}
                },
                "quantity": 2
            }]
        }
    }[key]
    
    # Act
    with patch("services.supabase.usage.is_request_limit_reached.get_stripe_customer_id") as mock_get_customer, \
         patch("services.supabase.usage.is_request_limit_reached.get_paid_subscription") as mock_get_subscription, \
         patch("services.supabase.usage.is_request_limit_reached.get_base_request_limit") as mock_get_limit, \
         patch("services.supabase.usage.is_request_limit_reached.get_owner") as mock_get_owner, \
         patch("services.supabase.usage.is_request_limit_reached.count_completed_unique_requests") as mock_count_requests:
        
        mock_get_customer.return_value = stripe_customer_id
        mock_get_subscription.return_value = mock_subscription
        mock_get_limit.return_value = 50
        mock_get_owner.return_value = {"credit_balance_usd": 0}
        mock_count_requests.return_value = ["request1"]  # 1 completed request
        
        result = is_request_limit_reached(
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
        )
    
    # Assert
    assert result["is_limit_reached"] is False
    assert result["requests_left"] == 99  # (50 * 2) - 1
    assert result["request_limit"] == 100  # 50 * 2 quantity
    assert result["is_credit_user"] is False


def test_is_request_limit_reached_paid_subscription_yearly():
    """Test with paid yearly subscription"""
    # Arrange
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    stripe_customer_id = "cus_test123"
    
    mock_subscription = MagicMock()
    mock_subscription.current_period_start = 1640995200  # 2022-01-01
    mock_subscription.current_period_end = 1672531200    # 2023-01-01
    mock_subscription.__getitem__ = lambda self, key: {
        "items": {
            "data": [{
                "price": {
                    "product": "prod_test123",
                    "recurring": {"interval": "year"}
                },
                "quantity": 1
            }]
        }
    }[key]
    
    # Act
    with patch("services.supabase.usage.is_request_limit_reached.get_stripe_customer_id") as mock_get_customer, \
         patch("services.supabase.usage.is_request_limit_reached.get_paid_subscription") as mock_get_subscription, \
         patch("services.supabase.usage.is_request_limit_reached.get_base_request_limit") as mock_get_limit, \
         patch("services.supabase.usage.is_request_limit_reached.get_owner") as mock_get_owner, \
         patch("services.supabase.usage.is_request_limit_reached.count_completed_unique_requests") as mock_count_requests:
        
        mock_get_customer.return_value = stripe_customer_id
        mock_get_subscription.return_value = mock_subscription
        mock_get_limit.return_value = 50
        mock_get_owner.return_value = {"credit_balance_usd": 0}
        mock_count_requests.return_value = []  # 0 completed requests
        
        result = is_request_limit_reached(
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
        )
    
    # Assert
    assert result["is_limit_reached"] is False
    assert result["requests_left"] == 600  # 50 * 12 * 1
    assert result["request_limit"] == 600
    assert result["is_credit_user"] is False


def test_is_request_limit_reached_no_subscription_no_credits():
    """Test when user has no subscription and no credits"""
    # Arrange
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    stripe_customer_id = "cus_test123"
    
    # Act
    with patch("services.supabase.usage.is_request_limit_reached.get_stripe_customer_id") as mock_get_customer, \
         patch("services.supabase.usage.is_request_limit_reached.get_paid_subscription") as mock_get_subscription, \
         patch("services.supabase.usage.is_request_limit_reached.get_owner") as mock_get_owner:
        
        mock_get_customer.return_value = stripe_customer_id
        mock_get_subscription.return_value = None
        mock_get_owner.return_value = {"credit_balance_usd": 0}
        
        result = is_request_limit_reached(
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
        )
    
    # Assert
    assert result["is_limit_reached"] is True
    assert result["requests_left"] == 0
    assert result["request_limit"] == 0
    assert result["is_credit_user"] is True
    assert result["credit_balance_usd"] == 0


def test_is_request_limit_reached_no_subscription_with_credits():
    """Test when user has no subscription but has credits"""
    # Arrange
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    stripe_customer_id = "cus_test123"
    
    # Act
    with patch("services.supabase.usage.is_request_limit_reached.get_stripe_customer_id") as mock_get_customer, \
         patch("services.supabase.usage.is_request_limit_reached.get_paid_subscription") as mock_get_subscription, \
         patch("services.supabase.usage.is_request_limit_reached.get_owner") as mock_get_owner, \
         patch("services.supabase.usage.is_request_limit_reached.count_completed_unique_requests") as mock_count_requests:
        
        mock_get_customer.return_value = stripe_customer_id
        mock_get_subscription.return_value = None
        mock_get_owner.return_value = {"credit_balance_usd": 50}
        mock_count_requests.return_value = ["request1", "request2"]  # 2 completed requests
        
        result = is_request_limit_reached(
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
        )
    
    # Assert
    assert result["is_limit_reached"] is False
    assert result["requests_left"] == 999997  # 999999 - 2
    assert result["request_limit"] == 999999
    assert result["is_credit_user"] is True
    assert result["credit_balance_usd"] == 50


def test_is_request_limit_reached_retry_request():
    """Test when current request is a retry (should not count against limit)"""
    # Arrange
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    owner_type = "User"
    repo_name = "test-repo"
    issue_number = 123
    stripe_customer_id = "cus_test123"
    
    current_request = f"{owner_type}/{owner_name}/{repo_name}#{issue_number}"
    
    # Act
    with patch("services.supabase.usage.is_request_limit_reached.get_stripe_customer_id") as mock_get_customer, \
         patch("services.supabase.usage.is_request_limit_reached.get_paid_subscription") as mock_get_subscription, \
         patch("services.supabase.usage.is_request_limit_reached.get_owner") as mock_get_owner, \
         patch("services.supabase.usage.is_request_limit_reached.count_completed_unique_requests") as mock_count_requests:
        
        mock_get_customer.return_value = stripe_customer_id
        mock_get_subscription.return_value = None
        mock_get_owner.return_value = {"credit_balance_usd": 50}
        mock_count_requests.return_value = [current_request, "other_request"]  # Current request is in the list
        
        result = is_request_limit_reached(
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
            owner_type=owner_type,
            repo_name=repo_name,
            issue_number=issue_number,
        )
    
    # Assert
    assert result["is_limit_reached"] is False  # Should not be limited for retries
    assert result["requests_left"] == 999997  # 999999 - 2
    assert result["request_limit"] == 999999
    assert result["is_credit_user"] is True
    assert result["credit_balance_usd"] == 50


def test_is_request_limit_reached_limit_exceeded():
    """Test when request limit is exceeded"""
    # Arrange
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    stripe_customer_id = "cus_test123"
    
    mock_subscription = MagicMock()
    mock_subscription.current_period_start = 1640995200  # 2022-01-01
    mock_subscription.current_period_end = 1643673600    # 2022-02-01
    mock_subscription.__getitem__ = lambda self, key: {
        "items": {
            "data": [{
                "price": {
                    "product": "prod_test123",
                    "recurring": {"interval": "month"}
                },
                "quantity": 1
            }]
        }
    }[key]
    
    # Act
    with patch("services.supabase.usage.is_request_limit_reached.get_stripe_customer_id") as mock_get_customer, \
         patch("services.supabase.usage.is_request_limit_reached.get_paid_subscription") as mock_get_subscription, \
         patch("services.supabase.usage.is_request_limit_reached.get_base_request_limit") as mock_get_limit, \
         patch("services.supabase.usage.is_request_limit_reached.get_owner") as mock_get_owner, \
         patch("services.supabase.usage.is_request_limit_reached.count_completed_unique_requests") as mock_count_requests:
        
        mock_get_customer.return_value = stripe_customer_id
        mock_get_subscription.return_value = mock_subscription
        mock_get_limit.return_value = 10
        mock_get_owner.return_value = {"credit_balance_usd": 0}
        # Return more requests than the limit
        mock_count_requests.return_value = ["req1", "req2", "req3", "req4", "req5", 
                                          "req6", "req7", "req8", "req9", "req10", "req11"]
        
        result = is_request_limit_reached(
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
        )
    
    # Assert
    assert result["is_limit_reached"] is True
    assert result["requests_left"] == -1  # 10 - 11
    assert result["request_limit"] == 10
    assert result["is_credit_user"] is False


def test_is_request_limit_reached_no_owner_record():
    """Test when owner record doesn't exist"""
    # Arrange
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    stripe_customer_id = "cus_test123"
    
    # Act
    with patch("services.supabase.usage.is_request_limit_reached.get_stripe_customer_id") as mock_get_customer, \
         patch("services.supabase.usage.is_request_limit_reached.get_paid_subscription") as mock_get_subscription, \
         patch("services.supabase.usage.is_request_limit_reached.get_owner") as mock_get_owner:
        
        mock_get_customer.return_value = stripe_customer_id
        mock_get_subscription.return_value = None
        mock_get_owner.return_value = None  # No owner record
        
        result = is_request_limit_reached(
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
        )
    
    # Assert
    assert result["is_limit_reached"] is True
    assert result["requests_left"] == 0
    assert result["request_limit"] == 0
    assert result["is_credit_user"] is True
    assert result["credit_balance_usd"] == 0


def test_is_request_limit_reached_exception_handling():
    """Test that exceptions are handled gracefully due to @handle_exceptions decorator"""
    # Arrange
    installation_id = 12345
    owner_id = 67890
    owner_name = "test-owner"
    
    # Act
    with patch("services.supabase.usage.is_request_limit_reached.get_stripe_customer_id") as mock_get_customer:
        mock_get_customer.side_effect = Exception("Test exception")
        
        result = is_request_limit_reached(
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
        )
    
    # Assert
    assert result == DEFAULT  # Should return default value due to exception handling