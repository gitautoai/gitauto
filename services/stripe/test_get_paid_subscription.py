from unittest.mock import patch, MagicMock
import pytest
from services.stripe.get_paid_subscription import get_paid_subscription


@pytest.fixture
def mock_stripe():
    """Fixture to provide a mocked Stripe module."""
    with patch("services.stripe.get_paid_subscription.stripe") as mock:
        yield mock


@pytest.fixture
def mock_subscription_list_response():
    """Fixture to provide a mocked Stripe Subscription.list response."""
    mock_response = MagicMock()
    mock_response.has_more = False
    mock_response.data = []
    return mock_response


def create_mock_subscription(sub_id, price_id, price_amount=1000):
    """Helper to create a mock subscription with proper item structure."""
    mock_subscription = MagicMock()
    mock_subscription.id = sub_id
    mock_subscription.plan.amount = price_amount
    mock_subscription.current_period_start = 1640995200  # Jan 1, 2022
    mock_subscription.current_period_end = 1672531200  # Jan 1, 2023

    # Mock items structure that the function expects
    mock_item = {
        "price": {
            "id": price_id,
            "product": f"prod_{price_id}",
            "recurring": {"interval": "month"},
        },
        "quantity": 1,
    }

    # Mock the subscription's items data access using a direct dictionary approach
    subscription_data = {
        "items": {"data": [mock_item]},
        "current_period_start": mock_subscription.current_period_start,
        "current_period_end": mock_subscription.current_period_end,
    }

    mock_subscription.__getitem__ = lambda self, key: subscription_data[key]

    return mock_subscription


@patch(
    "services.stripe.get_paid_subscription.STRIPE_FREE_TIER_PRICE_ID", "price_free_tier"
)
def test_get_paid_subscription_with_no_subscriptions(
    mock_stripe, mock_subscription_list_response
):
    """Test get_paid_subscription when there are no active subscriptions."""
    # Arrange
    customer_id = "cus_test123"
    mock_subscription_list_response.data = []
    mock_stripe.Subscription.list.return_value = mock_subscription_list_response

    # Act
    result = get_paid_subscription(customer_id=customer_id)

    # Assert
    mock_stripe.Subscription.list.assert_called_once_with(
        customer=customer_id, status="active"
    )
    assert result is None


def test_get_paid_subscription_with_only_free_tier(
    mock_stripe, mock_subscription_list_response
):
    """Test get_paid_subscription when there's only a free tier subscription."""
    with patch(
        "services.stripe.get_paid_subscription.STRIPE_FREE_TIER_PRICE_ID",
        "price_free_tier",
    ):
        # Arrange
        customer_id = "cus_test123"
        free_subscription = create_mock_subscription("sub_free", "price_free_tier")
        mock_subscription_list_response.data = [free_subscription]
        mock_stripe.Subscription.list.return_value = mock_subscription_list_response

        # Act
        result = get_paid_subscription(customer_id=customer_id)

        # Assert
        assert result is None


@patch(
    "services.stripe.get_paid_subscription.STRIPE_FREE_TIER_PRICE_ID", "price_free_tier"
)
def test_get_paid_subscription_with_single_paid_subscription(
    mock_stripe, mock_subscription_list_response
):
    """Test get_paid_subscription when there is a single paid subscription."""
    # Arrange
    customer_id = "cus_test123"
    paid_subscription = create_mock_subscription("sub_paid", "price_paid_tier", 3000)
    mock_subscription_list_response.data = [paid_subscription]
    mock_stripe.Subscription.list.return_value = mock_subscription_list_response

    # Act
    result = get_paid_subscription(customer_id=customer_id)

    # Assert
    mock_stripe.Subscription.list.assert_called_once_with(
        customer=customer_id, status="active"
    )
    assert result == paid_subscription


@patch(
    "services.stripe.get_paid_subscription.STRIPE_FREE_TIER_PRICE_ID", "price_free_tier"
)
def test_get_paid_subscription_with_multiple_paid_subscriptions(
    mock_stripe, mock_subscription_list_response
):
    """Test get_paid_subscription when there are multiple paid subscriptions."""
    # Arrange
    customer_id = "cus_test123"

    paid_subscription1 = create_mock_subscription("sub_paid1", "price_paid_tier1", 1000)
    paid_subscription2 = create_mock_subscription("sub_paid2", "price_paid_tier2", 3000)
    paid_subscription3 = create_mock_subscription("sub_paid3", "price_paid_tier3", 500)

    mock_subscription_list_response.data = [
        paid_subscription1,
        paid_subscription2,
        paid_subscription3,
    ]
    mock_stripe.Subscription.list.return_value = mock_subscription_list_response

    # Act
    result = get_paid_subscription(customer_id=customer_id)

    # Assert
    assert result == paid_subscription2  # Should return the highest priced one


@patch(
    "services.stripe.get_paid_subscription.STRIPE_FREE_TIER_PRICE_ID", "price_free_tier"
)
def test_get_paid_subscription_with_mixed_subscriptions(
    mock_stripe, mock_subscription_list_response
):
    """Test get_paid_subscription when there are both free and paid subscriptions."""
    # Arrange
    customer_id = "cus_test123"

    free_subscription = create_mock_subscription("sub_free", "price_free_tier", 0)
    paid_subscription1 = create_mock_subscription("sub_paid1", "price_paid_tier1", 1000)
    paid_subscription2 = create_mock_subscription("sub_paid2", "price_paid_tier2", 3000)

    mock_subscription_list_response.data = [
        free_subscription,
        paid_subscription1,
        paid_subscription2,
    ]
    mock_stripe.Subscription.list.return_value = mock_subscription_list_response

    # Act
    result = get_paid_subscription(customer_id=customer_id)

    # Assert
    assert (
        result == paid_subscription2
    )  # Should return the highest priced paid subscription


def test_get_paid_subscription_handles_exception(mock_stripe):
    """Test that get_paid_subscription handles exceptions gracefully."""
    # Arrange
    customer_id = "cus_test123"
    mock_stripe.Subscription.list.side_effect = Exception("Test exception")

    # Act
    result = get_paid_subscription(customer_id=customer_id)

    # Assert
    assert (
        result is None
    )  # Function should return None due to @handle_exceptions decorator
    mock_stripe.Subscription.list.assert_called_once_with(
        customer=customer_id, status="active"
    )


@patch(
    "services.stripe.get_paid_subscription.STRIPE_FREE_TIER_PRICE_ID", "price_free_tier"
)
def test_get_paid_subscription_with_pagination(mock_stripe):
    """Test get_paid_subscription when there are multiple pages of subscriptions."""
    # Arrange
    customer_id = "cus_test123"

    # First page response
    first_page_response = MagicMock()
    first_page_response.has_more = True

    paid_subscription1 = create_mock_subscription("sub_paid1", "price_paid_tier1", 1000)
    first_page_response.data = [paid_subscription1]

    # Second page response
    second_page_response = MagicMock()
    second_page_response.has_more = False

    paid_subscription2 = create_mock_subscription("sub_paid2", "price_paid_tier2", 3000)
    second_page_response.data = [paid_subscription2]

    # Configure mock to return different responses for each call
    mock_stripe.Subscription.list.side_effect = [
        first_page_response,
        second_page_response,
    ]

    # Act
    result = get_paid_subscription(customer_id=customer_id)

    # Assert
    assert mock_stripe.Subscription.list.call_count == 2

    # First call should be with just customer_id and status
    mock_stripe.Subscription.list.assert_any_call(customer=customer_id, status="active")

    # Second call should include starting_after parameter
    mock_stripe.Subscription.list.assert_any_call(
        customer=customer_id, status="active", starting_after="sub_paid1"
    )

    # Should return the highest priced subscription
    assert result == paid_subscription2
