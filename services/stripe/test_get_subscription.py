from unittest.mock import patch, MagicMock
import pytest
from services.stripe.get_subscription import get_subscription


@pytest.fixture
def mock_stripe():
    """Fixture to provide a mocked Stripe module."""
    with patch("services.stripe.get_subscription.stripe") as mock:
        yield mock


@pytest.fixture
def mock_subscription_list_response():
    """Fixture to provide a mocked Stripe Subscription.list response."""
    mock_response = MagicMock()
    mock_response.has_more = False
    mock_response.data = []
    return mock_response


def test_get_subscription_with_no_subscriptions(
    mock_stripe, mock_subscription_list_response
):
    """Test get_subscription when there are no active subscriptions."""
    # Arrange
    customer_id = "cus_test123"
    mock_subscription_list_response.data = []
    mock_stripe.Subscription.list.return_value = mock_subscription_list_response

    # Act
    result = get_subscription(customer_id=customer_id)

    # Assert
    mock_stripe.Subscription.list.assert_called_once_with(
        customer=customer_id, status="active"
    )
    assert result == mock_subscription_list_response
    assert result.data == []


def test_get_subscription_with_single_subscription(
    mock_stripe, mock_subscription_list_response
):
    """Test get_subscription when there is a single active subscription."""
    # Arrange
    customer_id = "cus_test123"
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_test123"
    mock_subscription.plan.amount = 1000
    mock_subscription_list_response.data = [mock_subscription]
    mock_stripe.Subscription.list.return_value = mock_subscription_list_response

    # Act
    result = get_subscription(customer_id=customer_id)

    # Assert
    mock_stripe.Subscription.list.assert_called_once_with(
        customer=customer_id, status="active"
    )
    assert result == mock_subscription_list_response
    assert len(result.data) == 1
    assert result.data[0] == mock_subscription


def test_get_subscription_with_multiple_subscriptions(
    mock_stripe, mock_subscription_list_response
):
    """Test get_subscription when there are multiple active subscriptions."""
    # Arrange
    customer_id = "cus_test123"

    # Create mock subscriptions with different prices
    mock_subscription1 = MagicMock()
    mock_subscription1.id = "sub_test123"
    mock_subscription1.plan.amount = 1000

    mock_subscription2 = MagicMock()
    mock_subscription2.id = "sub_test456"
    mock_subscription2.plan.amount = 2000  # Higher price

    mock_subscription3 = MagicMock()
    mock_subscription3.id = "sub_test789"
    mock_subscription3.plan.amount = 500

    mock_subscription_list_response.data = [
        mock_subscription1,
        mock_subscription2,
        mock_subscription3,
    ]
    mock_stripe.Subscription.list.return_value = mock_subscription_list_response

    # Act
    result = get_subscription(customer_id=customer_id)

    # Assert
    mock_stripe.Subscription.list.assert_called_once_with(
        customer=customer_id, status="active"
    )
    assert result == mock_subscription_list_response
    assert len(result.data) == 1
    assert (
        result.data[0] == mock_subscription2
    )  # Should return the highest priced subscription


def test_get_subscription_with_pagination(mock_stripe):
    """Test get_subscription when there are multiple pages of subscriptions."""
    # Arrange
    customer_id = "cus_test123"

    # First page response
    first_page_response = MagicMock()
    first_page_response.has_more = True

    mock_subscription1 = MagicMock()
    mock_subscription1.id = "sub_test123"
    mock_subscription1.plan.amount = 1000

    first_page_response.data = [mock_subscription1]

    # Second page response
    second_page_response = MagicMock()
    second_page_response.has_more = False

    mock_subscription2 = MagicMock()
    mock_subscription2.id = "sub_test456"
    mock_subscription2.plan.amount = 2000  # Higher price

    second_page_response.data = [mock_subscription2]

    # Configure mock to return different responses for each call
    mock_stripe.Subscription.list.side_effect = [
        first_page_response,
        second_page_response,
    ]

    # Act
    result = get_subscription(customer_id=customer_id)

    # Assert
    assert mock_stripe.Subscription.list.call_count == 2

    # First call should be with just customer_id and status
    mock_stripe.Subscription.list.assert_any_call(customer=customer_id, status="active")

    # Second call should include starting_after parameter
    mock_stripe.Subscription.list.assert_any_call(
        customer=customer_id, status="active", starting_after="sub_test123"
    )

    # Should return the highest priced subscription
    assert len(result.data) == 1
    assert result.data[0] == mock_subscription2


def test_get_subscription_with_empty_customer_id(
    mock_stripe, mock_subscription_list_response
):
    """Test get_subscription with empty customer_id."""
    # Arrange
    customer_id = ""
    mock_stripe.Subscription.list.return_value = mock_subscription_list_response

    # Act
    result = get_subscription(customer_id=customer_id)

    # Assert
    mock_stripe.Subscription.list.assert_called_once_with(
        customer=customer_id, status="active"
    )
    assert result == mock_subscription_list_response


def test_get_subscription_handles_exception(mock_stripe):
    """Test that get_subscription handles exceptions gracefully."""
    # Arrange
    customer_id = "cus_test123"
    mock_stripe.Subscription.list.side_effect = Exception("Test exception")

    # Act
    result = get_subscription(customer_id=customer_id)

    # Assert
    assert (
        result is None
    )  # Function should return None due to @handle_exceptions decorator
    mock_stripe.Subscription.list.assert_called_once_with(
        customer=customer_id, status="active"
    )


def test_get_subscription_with_equal_priced_subscriptions(
    mock_stripe, mock_subscription_list_response
):
    """Test get_subscription when there are multiple subscriptions with the same price."""
    # Arrange
    customer_id = "cus_test123"

    # Create mock subscriptions with the same price
    mock_subscription1 = MagicMock()
    mock_subscription1.id = "sub_test123"
    mock_subscription1.plan.amount = 1000

    mock_subscription2 = MagicMock()
    mock_subscription2.id = "sub_test456"
    mock_subscription2.plan.amount = 1000  # Same price

    mock_subscription_list_response.data = [mock_subscription1, mock_subscription2]
    mock_stripe.Subscription.list.return_value = mock_subscription_list_response

    # Act
    result = get_subscription(customer_id=customer_id)

    # Assert
    mock_stripe.Subscription.list.assert_called_once_with(
        customer=customer_id, status="active"
    )
    assert result == mock_subscription_list_response
    assert len(result.data) == 1
    # When prices are equal, max() will return the first one it encounters
    assert result.data[0] in [mock_subscription1, mock_subscription2]


def test_get_subscription_with_pagination_and_multiple_subscriptions(mock_stripe):
    """Test get_subscription with pagination and multiple subscriptions across pages."""
    # Arrange
    customer_id = "cus_test123"

    # First page response
    first_page_response = MagicMock()
    first_page_response.has_more = True

    mock_subscription1 = MagicMock()
    mock_subscription1.id = "sub_test123"
    mock_subscription1.plan.amount = 1000

    mock_subscription2 = MagicMock()
    mock_subscription2.id = "sub_test456"
    mock_subscription2.plan.amount = 1500

    first_page_response.data = [mock_subscription1, mock_subscription2]

    # Second page response
    second_page_response = MagicMock()
    second_page_response.has_more = False

    mock_subscription3 = MagicMock()
    mock_subscription3.id = "sub_test789"
    mock_subscription3.plan.amount = 2000  # Highest price

    mock_subscription4 = MagicMock()
    mock_subscription4.id = "sub_test101"
    mock_subscription4.plan.amount = 500

    second_page_response.data = [mock_subscription3, mock_subscription4]

    # Configure mock to return different responses for each call
    mock_stripe.Subscription.list.side_effect = [
        first_page_response,
        second_page_response,
    ]

    # Act
    result = get_subscription(customer_id=customer_id)

    # Assert
    assert mock_stripe.Subscription.list.call_count == 2

    # First call should be with just customer_id and status
    mock_stripe.Subscription.list.assert_any_call(customer=customer_id, status="active")

    # Second call should include starting_after parameter
    mock_stripe.Subscription.list.assert_any_call(
        customer=customer_id, status="active", starting_after="sub_test456"
    )

    # Should return the highest priced subscription
    assert len(result.data) == 1
    assert result.data[0] == mock_subscription3
