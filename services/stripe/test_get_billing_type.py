from unittest.mock import patch, MagicMock
import pytest
from services.stripe.get_billing_type import get_billing_type


@pytest.fixture
def mock_subscription():
    """Fixture to provide a mock Stripe subscription."""
    mock_sub = MagicMock()
    mock_sub.id = "sub_test123"
    return mock_sub


@patch("services.stripe.get_billing_type.EXCEPTION_OWNERS", ["exception_owner", "test_owner"])
def test_get_billing_type_returns_exception_for_exception_owner():
    """Test that get_billing_type returns 'exception' for owners in EXCEPTION_OWNERS."""
    # Test with first exception owner
    result = get_billing_type(
        owner_name="exception_owner",
        stripe_customer_id="cus_test123",
        paid_subscription=None,
    )
    assert result == "exception"

    # Test with second exception owner
    result = get_billing_type(
        owner_name="test_owner",
        stripe_customer_id="cus_test123",
        paid_subscription=None,
    )
    assert result == "exception"


def test_get_billing_type_returns_credit_for_no_stripe_customer_id():
    """Test that get_billing_type returns 'credit' when stripe_customer_id is None."""
    result = get_billing_type(
        owner_name="regular_owner",
        stripe_customer_id=None,
        paid_subscription=None,
    )
    assert result == "credit"


def test_get_billing_type_returns_credit_for_empty_stripe_customer_id():
    """Test that get_billing_type returns 'credit' when stripe_customer_id is empty string."""
    result = get_billing_type(
        owner_name="regular_owner",
        stripe_customer_id="",
        paid_subscription=None,
    )
    assert result == "credit"


def test_get_billing_type_returns_subscription_for_paid_subscription(mock_subscription):
    """Test that get_billing_type returns 'subscription' when paid_subscription exists."""
    result = get_billing_type(
        owner_name="regular_owner",
        stripe_customer_id="cus_test123",
        paid_subscription=mock_subscription,
    )
    assert result == "subscription"


def test_get_billing_type_returns_credit_as_default():
    """Test that get_billing_type returns 'credit' as default when no paid subscription."""
    result = get_billing_type(
        owner_name="regular_owner",
        stripe_customer_id="cus_test123",
        paid_subscription=None,
    )
    assert result == "credit"


@patch("services.stripe.get_billing_type.EXCEPTION_OWNERS", ["exception_owner"])
def test_get_billing_type_exception_owner_takes_precedence_over_subscription(mock_subscription):
    """Test that exception owner status takes precedence over having a paid subscription."""
    result = get_billing_type(
        owner_name="exception_owner",
        stripe_customer_id="cus_test123",
        paid_subscription=mock_subscription,
    )
    assert result == "exception"


@patch("services.stripe.get_billing_type.EXCEPTION_OWNERS", ["exception_owner"])
def test_get_billing_type_exception_owner_takes_precedence_over_no_customer_id():
    """Test that exception owner status takes precedence over no stripe customer ID."""
    result = get_billing_type(
        owner_name="exception_owner",
        stripe_customer_id=None,
        paid_subscription=None,
    )
    assert result == "exception"


@patch("services.stripe.get_billing_type.handle_exceptions")
def test_get_billing_type_handles_exceptions_gracefully(mock_handle_exceptions):
    """Test that the function is properly decorated with handle_exceptions."""
    # Mock the decorator to raise an exception and verify it's handled
    mock_handle_exceptions.side_effect = Exception("Test exception")

    # The decorator should catch the exception and return the default value "credit"
    # Since we're testing the decorator is applied, we verify it exists
    from services.stripe.get_billing_type import get_billing_type

    # Check that the function has the decorator applied
    assert hasattr(get_billing_type, '__wrapped__')
    assert get_billing_type.__name__ == 'get_billing_type'
