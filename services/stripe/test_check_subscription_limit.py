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


def create_mock_subscription(product_id, interval, quantity=1, start_timestamp=1640995200, end_timestamp=1643673600):
    """Helper to create a mock subscription with proper structure."""
    mock_subscription = MagicMock()
    mock_subscription.current_period_start = start_timestamp
    mock_subscription.current_period_end = end_timestamp
    
    # Mock the subscription's items data access using a direct dictionary approach
    subscription_data = {
        "items": {
            "data": [
                {
                    "price": {
                        "product": product_id,
                        "recurring": {"interval": interval},
                    },
                    "quantity": quantity,
                }
            ]
        }
    }
    
    mock_subscription.__getitem__ = lambda self, key: subscription_data[key]
    return mock_subscription


@pytest.fixture
def sample_monthly_subscription():
    """Fixture providing a sample monthly subscription."""
    return create_mock_subscription("prod_test123", "month", 1, 1640995200, 1643673600)


@pytest.fixture
def sample_yearly_subscription():
    """Fixture providing a sample yearly subscription."""
    return create_mock_subscription("prod_test456", "year", 1, 1640995200, 1672531200)


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
    subscription_with_quantity = create_mock_subscription("prod_test789", "month", 3, 1640995200, 1643673600)
    
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
    yearly_subscription_with_quantity = create_mock_subscription("prod_test999", "year", 2, 1640995200, 1672531200)
    
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
    malformed_subscription = create_mock_subscription("prod_test", "month", 1, 1640995200, 1643673600)
    
    # Override the __getitem__ to return empty data array
    malformed_subscription.__getitem__ = lambda self, key: {"items": {"data": []}}[key]
    
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
    subscription = create_mock_subscription("prod_test", interval, quantity, 1640995200, 1643673600)
    
    # Setup mocks
    mock_get_base_request_limit.return_value = base_limit
    mock_count_completed_unique_requests.return_value = set()  # No requests used
    
    result = check_subscription_limit(subscription, sample_installation_id)
    
    # Assertions
    assert result["request_limit"] == expected_limit
    assert result["requests_left"] == expected_limit
    assert result["can_proceed"] is True


def test_check_subscription_limit_return_type_structure(
    mock_get_base_request_limit,
    mock_count_completed_unique_requests,
    sample_monthly_subscription,
    sample_installation_id,
):
    """Test that the function returns the correct SubscriptionLimitResult structure."""
    # Setup mocks
    mock_get_base_request_limit.return_value = 100
    mock_count_completed_unique_requests.return_value = {"req1"}
    
    result = check_subscription_limit(sample_monthly_subscription, sample_installation_id)
    
    # Verify all required keys are present
    required_keys = {"can_proceed", "requests_left", "request_limit", "period_end_date"}
    assert set(result.keys()) == required_keys
    
    # Verify types
    assert isinstance(result["can_proceed"], bool)
    assert isinstance(result["requests_left"], int)
    assert isinstance(result["request_limit"], int)
    assert isinstance(result["period_end_date"], datetime)


def test_check_subscription_limit_with_zero_base_limit(
    mock_get_base_request_limit,
    mock_count_completed_unique_requests,
    sample_monthly_subscription,
    sample_installation_id,
):
    """Test subscription with zero base request limit."""
    # Setup mocks
    mock_get_base_request_limit.return_value = 0
    mock_count_completed_unique_requests.return_value = set()
    
    result = check_subscription_limit(sample_monthly_subscription, sample_installation_id)
    
    # Assertions
    assert result["can_proceed"] is False
    assert result["requests_left"] == 0
    assert result["request_limit"] == 0


def test_check_subscription_limit_with_negative_base_limit(
    mock_get_base_request_limit,
    mock_count_completed_unique_requests,
    sample_monthly_subscription,
    sample_installation_id,
):
    """Test subscription with negative base request limit (edge case)."""
    # Setup mocks
    mock_get_base_request_limit.return_value = -10
    mock_count_completed_unique_requests.return_value = set()
    
    result = check_subscription_limit(sample_monthly_subscription, sample_installation_id)
    
    # Assertions
    assert result["can_proceed"] is False
    assert result["requests_left"] == -10
    assert result["request_limit"] == -10


def test_check_subscription_limit_datetime_conversion(
    mock_get_base_request_limit,
    mock_count_completed_unique_requests,
    sample_installation_id,
):
    """Test that timestamps are correctly converted to datetime objects with proper timezone."""
    subscription = create_mock_subscription("prod_datetime_test", "month", 1, 1609459200, 1612137600)
    
    # Setup mocks
    mock_get_base_request_limit.return_value = 100
    mock_count_completed_unique_requests.return_value = {"req1"}
    
    result = check_subscription_limit(subscription, sample_installation_id)
    
    # Verify datetime conversion with proper timezone
    assert result["period_end_date"] == datetime.fromtimestamp(1612137600, tz=TZ)
    assert result["period_end_date"].tzinfo == TZ


def test_check_subscription_limit_boundary_condition_exactly_zero_requests_left(
    mock_get_base_request_limit,
    mock_count_completed_unique_requests,
    sample_monthly_subscription,
    sample_installation_id,
):
    """Test boundary condition where requests_left is exactly 0."""
    # Setup mocks - limit equals used requests
    mock_get_base_request_limit.return_value = 5
    mock_count_completed_unique_requests.return_value = set(f"req{i}" for i in range(5))  # Exactly 5 requests used
    
    result = check_subscription_limit(sample_monthly_subscription, sample_installation_id)
    
    # When requests_left is 0, can_proceed should be False (> 0 condition)
    assert result["can_proceed"] is False
    assert result["requests_left"] == 0
    assert result["request_limit"] == 5