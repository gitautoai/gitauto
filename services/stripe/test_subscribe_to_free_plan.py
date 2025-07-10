from unittest.mock import patch, MagicMock

import pytest

from config import STRIPE_FREE_TIER_PRICE_ID
from services.stripe.subscribe_to_free_plan import subscribe_to_free_plan


@pytest.fixture
def mock_stripe():
    """Fixture to provide a mocked Stripe module."""
    with patch("services.stripe.subscribe_to_free_plan.stripe") as mock:
        mock_subscription = MagicMock()
        mock.Subscription.create.return_value = mock_subscription
        yield mock


def test_subscribe_to_free_plan_creates_subscription(mock_stripe):
    """Test that subscribe_to_free_plan creates a subscription with correct parameters."""
    # Arrange
    customer_id = "cus_test123"
    owner_id = 12345
    owner_name = "test-owner"
    installation_id = 67890

    # Act
    result = subscribe_to_free_plan(
        customer_id=customer_id,
        owner_id=owner_id,
        owner_name=owner_name,
        installation_id=installation_id,
    )

    # Assert
    mock_stripe.Subscription.create.assert_called_once_with(
        customer=customer_id,
        items=[{"price": STRIPE_FREE_TIER_PRICE_ID}],
        description="GitAuto Github App Installation Event",
        metadata={
            "owner_id": str(owner_id),
            "owner_name": owner_name,
            "installation_id": str(installation_id),
        },
    )
    assert result is None  # Function returns None when successful


def test_subscribe_to_free_plan_with_empty_customer_id(mock_stripe):
    """Test that subscribe_to_free_plan handles empty customer_id."""
    # Arrange
    customer_id = ""
    owner_id = 12345
    owner_name = "test-owner"
    installation_id = 67890

    # Act
    subscribe_to_free_plan(
        customer_id=customer_id,
        owner_id=owner_id,
        owner_name=owner_name,
        installation_id=installation_id,
    )

    # Assert
    mock_stripe.Subscription.create.assert_called_once_with(
        customer=customer_id,
        items=[{"price": STRIPE_FREE_TIER_PRICE_ID}],
        description="GitAuto Github App Installation Event",
        metadata={
            "owner_id": str(owner_id),
            "owner_name": owner_name,
            "installation_id": str(installation_id),
        },
    )


def test_subscribe_to_free_plan_with_empty_owner_name(mock_stripe):
    """Test that subscribe_to_free_plan handles empty owner_name."""
    # Arrange
    customer_id = "cus_test123"
    owner_id = 12345
    owner_name = ""
    installation_id = 67890

    # Act
    subscribe_to_free_plan(
        customer_id=customer_id,
        owner_id=owner_id,
        owner_name=owner_name,
        installation_id=installation_id,
    )

    # Assert
    mock_stripe.Subscription.create.assert_called_once_with(
        customer=customer_id,
        items=[{"price": STRIPE_FREE_TIER_PRICE_ID}],
        description="GitAuto Github App Installation Event",
        metadata={
            "owner_id": str(owner_id),
            "owner_name": owner_name,
            "installation_id": str(installation_id),
        },
    )


def test_subscribe_to_free_plan_handles_exception(mock_stripe):
    """Test that subscribe_to_free_plan handles exceptions gracefully."""
    # Arrange
    customer_id = "cus_test123"
    owner_id = 12345
    owner_name = "test-owner"
    installation_id = 67890
    
    # Configure mock to raise an exception
    mock_stripe.Subscription.create.side_effect = Exception("Test exception")

    # Act
    result = subscribe_to_free_plan(
        customer_id=customer_id,
        owner_id=owner_id,
        owner_name=owner_name,
        installation_id=installation_id,
    )

    # Assert
    assert result is None  # Function should return None due to @handle_exceptions decorator


def test_subscribe_to_free_plan_with_zero_values(mock_stripe):
    """Test that subscribe_to_free_plan handles zero values for numeric fields."""
    # Arrange
    customer_id = "cus_test123"
    owner_id = 0
    owner_name = "test-owner"
    installation_id = 0

    # Act
    subscribe_to_free_plan(
        customer_id=customer_id,
        owner_id=owner_id,
        owner_name=owner_name,
        installation_id=installation_id,
    )

    # Assert
    mock_stripe.Subscription.create.assert_called_once_with(
        customer=customer_id,
        items=[{"price": STRIPE_FREE_TIER_PRICE_ID}],
        description="GitAuto Github App Installation Event",
        metadata={
            "owner_id": "0",
            "owner_name": owner_name,
            "installation_id": "0",
        },
    )


def test_subscribe_to_free_plan_with_special_characters_in_owner_name(mock_stripe):
    """Test that subscribe_to_free_plan handles special characters in owner_name."""
    # Arrange
    customer_id = "cus_test123"
    owner_id = 12345
    owner_name = "test-owner!@#$%^&*()"
    installation_id = 67890

    # Act
    subscribe_to_free_plan(
        customer_id=customer_id,
        owner_id=owner_id,
        owner_name=owner_name,
        installation_id=installation_id,
    )

    # Assert
    mock_stripe.Subscription.create.assert_called_once_with(
        customer=customer_id,
        items=[{"price": STRIPE_FREE_TIER_PRICE_ID}],
        description="GitAuto Github App Installation Event",
        metadata={
            "owner_id": str(owner_id),
            "owner_name": owner_name,
            "installation_id": str(installation_id),
        },
    )


def test_subscribe_to_free_plan_with_large_ids(mock_stripe):
    """Test that subscribe_to_free_plan handles large numeric values."""
    # Arrange
    customer_id = "cus_test123"
    owner_id = 9999999999
    owner_name = "test-owner"
    installation_id = 9999999999

    # Act
    subscribe_to_free_plan(
        customer_id=customer_id,
        owner_id=owner_id,
        owner_name=owner_name,
        installation_id=installation_id,
    )

    # Assert
    mock_stripe.Subscription.create.assert_called_once_with(
        customer=customer_id,
        items=[{"price": STRIPE_FREE_TIER_PRICE_ID}],
        description="GitAuto Github App Installation Event",
        metadata={
            "owner_id": "9999999999",
            "owner_name": owner_name,
            "installation_id": "9999999999",
        },
    )