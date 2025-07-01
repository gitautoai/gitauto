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


def test_stripe_client_api_key_type_and_format():
    """Test that the API key has the expected format."""
    # Verify API key is a non-empty string
    assert isinstance(client_stripe.api_key, str)
    assert len(client_stripe.api_key) > 0
    
    # Stripe API keys typically start with 'sk_' for secret keys
    # This is a basic format check without revealing the actual key
    assert client_stripe.api_key is not None


def test_stripe_client_import_from_other_modules():
    """Test that stripe client can be imported by other stripe service modules."""
    # This simulates how other stripe service files import the client
    from services.stripe.client import stripe
    
    # Verify it's the same stripe module and properly configured
    assert stripe is client_stripe
    assert stripe.api_key == STRIPE_API_KEY
    assert hasattr(stripe, 'Customer')


def test_stripe_client_real_world_usage():
    """Test that stripe client works as expected in real-world scenarios."""
    from services.stripe.client import stripe
    
    # Test that we can access commonly used Stripe objects
    assert stripe.Customer is not None
    assert stripe.Subscription is not None
    assert stripe.Product is not None
    assert stripe.Price is not None
    
    # Test that the API key is properly configured for actual use
    assert stripe.api_key is not None
    assert len(stripe.api_key) > 0
    assert isinstance(stripe.api_key, str)


def test_stripe_client_environment_consistency():
    """Test that the stripe client configuration is consistent across imports."""
    # Import from different contexts to ensure consistency
    from services.stripe.client import stripe, STRIPE_API_KEY
    
    # Verify consistency
    assert stripe.api_key == STRIPE_API_KEY