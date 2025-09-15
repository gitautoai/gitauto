from unittest.mock import MagicMock, patch

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


@patch("services.stripe.get_billing_type.EXCEPTION_OWNERS")
def test_get_billing_type_handles_exceptions_gracefully(mock_exception_owners):
    """Test that the function handles exceptions and returns default value 'credit'."""
    # Mock EXCEPTION_OWNERS to raise an exception when accessed
    mock_exception_owners.__contains__.side_effect = Exception("Test exception")

    # The decorator should catch the exception and return the default value "credit"
    result = get_billing_type(
        owner_name="any_owner",
        stripe_customer_id="cus_test123",
        paid_subscription=None,
    )

    # Should return the default value specified in the decorator
    assert result == "credit"


def test_get_billing_type_function_signature():
    """Test that the function maintains its original signature after decoration."""
    # Verify the function is properly decorated but maintains its interface
    assert get_billing_type.__name__ == 'get_billing_type'
    assert callable(get_billing_type)


def test_get_billing_type_with_falsy_stripe_customer_id_values():
    """Test that get_billing_type returns 'credit' for various falsy stripe_customer_id values."""
    falsy_values = [None, "", 0, False]

    for falsy_value in falsy_values:
        result = get_billing_type(
            owner_name="regular_owner",
            stripe_customer_id=falsy_value,
            paid_subscription=None,
        )
        assert result == "credit", f"Failed for falsy value: {falsy_value}"


def test_get_billing_type_with_truthy_subscription_values(mock_subscription):
    """Test that get_billing_type returns 'subscription' for truthy paid_subscription values."""
    # Test with mock subscription
    result = get_billing_type(
        owner_name="regular_owner",
        stripe_customer_id="cus_test123",
        paid_subscription=mock_subscription,
    )
    assert result == "subscription"

    # Test with any truthy object
    result = get_billing_type(
        owner_name="regular_owner",
        stripe_customer_id="cus_test123",
        paid_subscription={"id": "sub_test"},
    )
    assert result == "subscription"


@patch("services.stripe.get_billing_type.EXCEPTION_OWNERS", [])
def test_get_billing_type_with_empty_exception_owners():
    """Test that get_billing_type works correctly when EXCEPTION_OWNERS is empty."""
    result = get_billing_type(
        owner_name="any_owner",
        stripe_customer_id="cus_test123",
        paid_subscription=None,
    )
    assert result == "credit"
