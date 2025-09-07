# This is just to check the file content
from unittest.mock import patch
import pytest
from config import PRODUCT_ID_FOR_STANDARD
from services.stripe.get_base_request_limit import get_base_request_limit


@pytest.fixture
def mock_stripe_product():
    """Fixture to provide a mocked stripe.Product.retrieve method."""
    with patch(
        "services.stripe.get_base_request_limit.stripe.Product.retrieve"
    ) as mock:
        yield mock


@pytest.fixture
def sample_product_response():
    """Fixture providing a sample Stripe product response."""
    return {
        "id": "prod_test123",
        "object": "product",
        "name": "Test Product",
        "metadata": {"request_count": "100"},
    }


def test_get_base_request_limit_returns_correct_value(
    mock_stripe_product, sample_product_response
):
    """Test that get_base_request_limit returns the correct request count from product metadata."""
    mock_stripe_product.return_value = sample_product_response

    result = get_base_request_limit("prod_test123")

    assert result == 100
    mock_stripe_product.assert_called_once_with("prod_test123")


def test_get_base_request_limit_with_standard_product(mock_stripe_product):
    """Test get_base_request_limit with standard tier product."""
    standard_product_response = {
        "id": PRODUCT_ID_FOR_STANDARD,
        "object": "product",
        "name": "Standard Tier",
        "metadata": {"request_count": "1000"},
    }
    mock_stripe_product.return_value = standard_product_response

    result = get_base_request_limit(PRODUCT_ID_FOR_STANDARD)

    assert result == 1000
    mock_stripe_product.assert_called_once_with(PRODUCT_ID_FOR_STANDARD)


def test_get_base_request_limit_converts_string_to_int(mock_stripe_product):
    """Test that the function properly converts string metadata to integer."""
    product_response = {
        "id": "prod_test456",
        "object": "product",
        "metadata": {"request_count": "500"},
    }
    mock_stripe_product.return_value = product_response

    result = get_base_request_limit("prod_test456")

    assert result == 500
    assert isinstance(result, int)


def test_get_base_request_limit_handles_stripe_exception(mock_stripe_product):
    """Test that function returns default value when Stripe API raises an exception."""
    mock_stripe_product.side_effect = Exception("Stripe API error")

    result = get_base_request_limit("invalid_product_id")

    assert result == 0


def test_get_base_request_limit_handles_missing_metadata(mock_stripe_product):
    """Test that function returns default value when metadata is missing."""
    product_response = {
        "id": "prod_no_metadata",
        "object": "product",
        "name": "Product without metadata",
    }
    mock_stripe_product.return_value = product_response

    result = get_base_request_limit("prod_no_metadata")

    assert result == 0


def test_get_base_request_limit_handles_missing_request_count(mock_stripe_product):
    """Test that function returns default value when request_count is missing from metadata."""
    product_response = {
        "id": "prod_no_request_count",
        "object": "product",
        "metadata": {"other_field": "value"},
    }
    mock_stripe_product.return_value = product_response

    result = get_base_request_limit("prod_no_request_count")

    assert result == 0


def test_get_base_request_limit_handles_invalid_request_count_format(
    mock_stripe_product,
):
    """Test that function returns default value when request_count cannot be converted to int."""
    product_response = {
        "id": "prod_invalid_count",
        "object": "product",
        "metadata": {"request_count": "not_a_number"},
    }
    mock_stripe_product.return_value = product_response

    result = get_base_request_limit("prod_invalid_count")

    assert result == 0


@pytest.mark.parametrize(
    "product_id,expected_request_count",
    [
        ("prod_basic", "50"),
        ("prod_premium", "2000"),
        ("prod_enterprise", "10000"),
    ],
)
def test_get_base_request_limit_with_various_products(
    mock_stripe_product, product_id, expected_request_count
):
    """Test get_base_request_limit with various product configurations."""
    product_response = {
        "id": product_id,
        "object": "product",
        "metadata": {"request_count": expected_request_count},
    }
    mock_stripe_product.return_value = product_response

    result = get_base_request_limit(product_id)

    assert result == int(expected_request_count)
    mock_stripe_product.assert_called_once_with(product_id)


def test_get_base_request_limit_with_empty_product_id(mock_stripe_product):
    """Test get_base_request_limit with empty product ID."""
    mock_stripe_product.side_effect = Exception("Invalid product ID")

    result = get_base_request_limit("")

    assert result == 0


def test_get_base_request_limit_with_none_product_id(mock_stripe_product):
    """Test get_base_request_limit with None product ID."""
    mock_stripe_product.side_effect = Exception("Invalid product ID")

    result = get_base_request_limit(None)

    assert result == 0
