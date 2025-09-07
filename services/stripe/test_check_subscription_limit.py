from datetime import datetime
from unittest.mock import patch, MagicMock
import pytest
from config import TZ, ONE_YEAR_FROM_NOW
from services.stripe.check_subscription_limit import (
    check_subscription_limit,
    SubscriptionLimitResult,
)


@pytest.fixture
def mock_get_base_request_limit():
    """Fixture to mock get_base_request_limit function."""
    with patch(
        "services.stripe.check_subscription_limit.get_base_request_limit"
    ) as mock:
        yield mock


@pytest.fixture
def mock_count_completed_unique_requests():
    """Fixture to mock count_completed_unique_requests function."""
    with patch(
        "services.stripe.check_subscription_limit.count_completed_unique_requests"
    ) as mock:
        yield mock


@pytest.fixture
def sample_monthly_subscription():
    """Fixture providing a sample monthly subscription."""
    return {
        "items": {
            "data": [
                {
                    "price": {
                        "product": "prod_test123",
                        "recurring": {"interval": "month"},
                    },
                    "quantity": 1,
                }
            ]
        },
        "current_period_start": 1640995200,  # 2022-01-01 00:00:00 UTC
        "current_period_end": 1643673600,    # 2022-02-01 00:00:00 UTC
    }


@pytest.fixture
def sample_yearly_subscription():
    """Fixture providing a sample yearly subscription."""
    return {
        "items": {
            "data": [
                {
                    "price": {
                        "product": "prod_test456",
                        "recurring": {"interval": "year"},
                    },
                    "quantity": 1,
                }
            ]
        },
        "current_period_start": 1640995200,  # 2022-01-01 00:00:00 UTC
        "current_period_end": 1672531200,    # 2023-01-01 00:00:00 UTC
    }


@pytest.fixture
def sample_installation_id():
    """Fixture providing a sample installation ID."""
    return 12345


def test_check_subscription_limit_monthly_subscription_with_requests_left(
    mock_get_base_request_limit,
    mock_count_completed_unique_requests,
    sample_monthly_subscription,
    sample_installation_id,
):
    """Test monthly subscription with requests remaining."""
    # Setup mocks
    mock_get_base_request_limit.return_value = 100
    mock_count_completed_unique_requests.return_value = {"req1", "req2", "req3"}  # 3 requests used
    
    result = check_subscription_limit(sample_monthly_subscription, sample_installation_id)
    
    # Assertions
    assert result["can_proceed"] is True
    assert result["requests_left"] == 97  # 100 - 3
    assert result["request_limit"] == 100  # base_limit * 1 (quantity)
    assert result["period_end_date"] == datetime.fromtimestamp(1643673600, tz=TZ)
    
    # Verify function calls
    mock_get_base_request_limit.assert_called_once_with("prod_test123")
    mock_count_completed_unique_requests.assert_called_once_with(
        sample_installation_id, 
        datetime.fromtimestamp(1640995200, tz=TZ)
    )


def test_check_subscription_limit_monthly_subscription_no_requests_left(
    mock_get_base_request_limit,
    mock_count_completed_unique_requests,
    sample_monthly_subscription,
    sample_installation_id,
):
    """Test monthly subscription with no requests remaining."""
    # Setup mocks
    mock_get_base_request_limit.return_value = 50
    mock_count_completed_unique_requests.return_value = set(f"req{i}" for i in range(50))  # 50 requests used
    
    result = check_subscription_limit(sample_monthly_subscription, sample_installation_id)
    
    # Assertions
    assert result["can_proceed"] is False
    assert result["requests_left"] == 0  # 50 - 50
    assert result["request_limit"] == 50
    assert result["period_end_date"] == datetime.fromtimestamp(1643673600, tz=TZ)


def test_check_subscription_limit_monthly_subscription_exceeded_limit(
    mock_get_base_request_limit,
    mock_count_completed_unique_requests,
    sample_monthly_subscription,
    sample_installation_id,
):
    """Test monthly subscription with requests exceeding limit."""
    # Setup mocks
    mock_get_base_request_limit.return_value = 30
    mock_count_completed_unique_requests.return_value = set(f"req{i}" for i in range(35))  # 35 requests used
    
    result = check_subscription_limit(sample_monthly_subscription, sample_installation_id)
    
    # Assertions
    assert result["can_proceed"] is False
    assert result["requests_left"] == -5  # 30 - 35
    assert result["request_limit"] == 30


def test_check_subscription_limit_yearly_subscription(
    mock_get_base_request_limit,
    mock_count_completed_unique_requests,
    sample_yearly_subscription,
    sample_installation_id,
):
    """Test yearly subscription with 12x multiplier."""
    # Setup mocks
    mock_get_base_request_limit.return_value = 100
    mock_count_completed_unique_requests.return_value = {"req1", "req2"}  # 2 requests used
    
    result = check_subscription_limit(sample_yearly_subscription, sample_installation_id)
    
    # Assertions
    assert result["can_proceed"] is True
    assert result["requests_left"] == 1198  # (100 * 12 * 1) - 2
    assert result["request_limit"] == 1200  # base_limit * 12 * quantity
    assert result["period_end_date"] == datetime.fromtimestamp(1672531200, tz=TZ)


def test_check_subscription_limit_with_quantity_greater_than_one(
    mock_get_base_request_limit,
    mock_count_completed_unique_requests,
    sample_installation_id,
):
    """Test subscription with quantity > 1."""
    subscription_with_quantity = {
        "items": {
            "data": [
                {
                    "price": {
                        "product": "prod_test789",
                        "recurring": {"interval": "month"},
                    },
                    "quantity": 3,
                }
            ]
        },
        "current_period_start": 1640995200,
        "current_period_end": 1643673600,
    }
    
    # Setup mocks
    mock_get_base_request_limit.return_value = 100
    mock_count_completed_unique_requests.return_value = {"req1"}  # 1 request used
    
    result = check_subscription_limit(subscription_with_quantity, sample_installation_id)
    
    # Assertions
    assert result["can_proceed"] is True
    assert result["requests_left"] == 299  # (100 * 3) - 1
    assert result["request_limit"] == 300  # base_limit * quantity


def test_check_subscription_limit_yearly_with_quantity(
    mock_get_base_request_limit,
    mock_count_completed_unique_requests,
    sample_installation_id,
):
    """Test yearly subscription with quantity > 1."""
    yearly_subscription_with_quantity = {
        "items": {
            "data": [
                {
                    "price": {
                        "product": "prod_test999",
                        "recurring": {"interval": "year"},
                    },
                    "quantity": 2,
                }
            ]
        },
        "current_period_start": 1640995200,
        "current_period_end": 1672531200,
    }
    
    # Setup mocks
    mock_get_base_request_limit.return_value = 50
    mock_count_completed_unique_requests.return_value = set()  # 0 requests used
    
    result = check_subscription_limit(yearly_subscription_with_quantity, sample_installation_id)
    
    # Assertions
    assert result["can_proceed"] is True
    assert result["requests_left"] == 1200  # (50 * 12 * 2) - 0
    assert result["request_limit"] == 1200  # base_limit * 12 * quantity


def test_check_subscription_limit_with_empty_unique_requests(
    mock_get_base_request_limit,
    mock_count_completed_unique_requests,
    sample_monthly_subscription,
    sample_installation_id,
):
    """Test subscription with no completed requests."""
    # Setup mocks
    mock_get_base_request_limit.return_value = 100
    mock_count_completed_unique_requests.return_value = set()  # No requests used
    
    result = check_subscription_limit(sample_monthly_subscription, sample_installation_id)
    
    # Assertions
    assert result["can_proceed"] is True
    assert result["requests_left"] == 100  # 100 - 0
    assert result["request_limit"] == 100


def test_check_subscription_limit_handles_get_base_request_limit_exception(
    mock_get_base_request_limit,
    mock_count_completed_unique_requests,
    sample_monthly_subscription,
    sample_installation_id,
):
    """Test that function returns default values when get_base_request_limit raises exception."""
    # Setup mocks
    mock_get_base_request_limit.side_effect = Exception("Stripe API error")
    mock_count_completed_unique_requests.return_value = {"req1"}
    
    result = check_subscription_limit(sample_monthly_subscription, sample_installation_id)
    
    # Should return default error values due to @handle_exceptions decorator
    assert result["can_proceed"] is False
    assert result["requests_left"] == 0
    assert result["request_limit"] == 0
    assert result["period_end_date"] == ONE_YEAR_FROM_NOW


def test_check_subscription_limit_handles_count_requests_exception(
    mock_get_base_request_limit,
    mock_count_completed_unique_requests,
    sample_monthly_subscription,
    sample_installation_id,
):
    """Test that function returns default values when count_completed_unique_requests raises exception."""
    # Setup mocks
    mock_get_base_request_limit.return_value = 100
    mock_count_completed_unique_requests.side_effect = Exception("Database error")
    
    result = check_subscription_limit(sample_monthly_subscription, sample_installation_id)
    
    # Should return default error values due to @handle_exceptions decorator
    assert result["can_proceed"] is False
    assert result["requests_left"] == 0
    assert result["request_limit"] == 0
    assert result["period_end_date"] == ONE_YEAR_FROM_NOW


def test_check_subscription_limit_handles_malformed_subscription_data(
    mock_get_base_request_limit,
    mock_count_completed_unique_requests,
    sample_installation_id,
):
    """Test that function returns default values when subscription data is malformed."""
    malformed_subscription = {
        "items": {"data": []},  # Empty data array
        "current_period_start": 1640995200,
        "current_period_end": 1643673600,
    }
    
    # Setup mocks
    mock_get_base_request_limit.return_value = 100
    mock_count_completed_unique_requests.return_value = {"req1"}
    
    result = check_subscription_limit(malformed_subscription, sample_installation_id)
    
    # Should return default error values due to @handle_exceptions decorator
    assert result["can_proceed"] is False
    assert result["requests_left"] == 0
    assert result["request_limit"] == 0
    assert result["period_end_date"] == ONE_YEAR_FROM_NOW


@pytest.mark.parametrize(
    "interval,base_limit,quantity,expected_limit",
    [
        ("month", 100, 1, 100),
        ("month", 100, 2, 200),
        ("month", 50, 3, 150),
        ("year", 100, 1, 1200),
        ("year", 100, 2, 2400),
        ("year", 50, 3, 1800),
    ],
)
def test_check_subscription_limit_request_limit_calculation(
    mock_get_base_request_limit,
    mock_count_completed_unique_requests,
    sample_installation_id,
    interval,
    base_limit,
    quantity,
    expected_limit,
):
    """Test request limit calculation for various intervals and quantities."""
    subscription = {
        "items": {
            "data": [
                {
                    "price": {
                        "product": "prod_test",
                        "recurring": {"interval": interval},
                    },
                    "quantity": quantity,
                }
            ]
        },
        "current_period_start": 1640995200,
        "current_period_end": 1643673600,
    }
    
    # Setup mocks
    mock_get_base_request_limit.return_value = base_limit
    mock_count_completed_unique_requests.return_value = set()  # No requests used
    
    result = check_subscription_limit(subscription, sample_installation_id)
    
    # Assertions
    assert result["request_limit"] == expected_limit
    assert result["requests_left"] == expected_limit
    assert result["can_proceed"] is True
