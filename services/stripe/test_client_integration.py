import stripe

from config import STRIPE_API_KEY
from services.stripe.client import stripe as client_stripe


def test_stripe_client_integration():
    """Integration test to verify stripe client is properly configured."""
    # Verify that the imported stripe client is the same as the global stripe module
    assert client_stripe is stripe
    
    # Verify that the API key is set correctly
    assert client_stripe.api_key == STRIPE_API_KEY
    assert client_stripe.api_key is not None
    assert isinstance(client_stripe.api_key, str)


def test_stripe_client_has_required_classes():
    """Test that stripe client has all required classes for the application."""
    # Test that all classes used in the stripe services are available
    assert hasattr(client_stripe, 'Customer')
    assert hasattr(client_stripe, 'Subscription')
    assert hasattr(client_stripe, 'Product')
    assert hasattr(client_stripe, 'Price')
    
    # Verify these are classes (not None or other types)
    assert client_stripe.Customer is not None
    assert client_stripe.Subscription is not None
    assert client_stripe.Product is not None
    assert client_stripe.Price is not None


def test_stripe_client_methods_available():
    """Test that stripe client classes have the required methods."""
    # Test Customer methods used in create_stripe_customer.py
    assert hasattr(client_stripe.Customer, 'create')
    assert callable(client_stripe.Customer.create)
    
    # Test Subscription methods used in get_subscription.py and subscribe_to_free_plan.py
    assert hasattr(client_stripe.Subscription, 'list')
    assert hasattr(client_stripe.Subscription, 'create')
    assert callable(client_stripe.Subscription.list)
    assert callable(client_stripe.Subscription.create)
    
    # Test Product methods used in get_base_request_limit.py
    assert hasattr(client_stripe.Product, 'retrieve')
    assert callable(client_stripe.Product.retrieve)
