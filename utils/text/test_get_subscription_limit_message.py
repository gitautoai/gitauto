from datetime import datetime
import pytest
from utils.text.get_subscription_limit_message import get_subscription_limit_message
from config import EMAIL_LINK
from constants.urls import PRODUCT_URL, PRICING_URL, CONTACT_URL


@pytest.fixture
def sample_datetime():
    return datetime(2025, 1, 1, 12, 0, 0)


def test_get_subscription_limit_message_basic(sample_datetime):
    """Test basic functionality with valid inputs"""
    message = get_subscription_limit_message(
        user_name="test_user", request_limit=100, period_end_date=sample_datetime
    )

    # Verify all required components are present
    assert "@test_user" in message
    assert "100" in message
    assert "2025-01-01 12:00:00" in message
    assert PRODUCT_URL in message
    assert PRICING_URL in message
    assert CONTACT_URL in message
    assert EMAIL_LINK in message


def test_get_subscription_limit_message_special_chars(sample_datetime):
    """Test with username containing special characters"""
    message = get_subscription_limit_message(
        user_name="test-user@123", request_limit=50, period_end_date=sample_datetime
    )
    assert "@test-user@123" in message
    assert "50" in message
    assert PRODUCT_URL in message
    assert PRICING_URL in message
    assert CONTACT_URL in message
    assert EMAIL_LINK in message
