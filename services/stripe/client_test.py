from unittest.mock import patch
import stripe

from config import STRIPE_API_KEY


def test_stripe_module_imported():
    """Test that stripe module is properly imported."""
    from services.stripe.client import stripe as client_stripe
    assert client_stripe is stripe


def test_stripe_api_key_set_from_config():
    """Test that stripe.api_key is set from config."""
    from services.stripe.client import stripe as client_stripe
    assert client_stripe.api_key == STRIPE_API_KEY


@patch('config.STRIPE_API_KEY', 'test_api_key')
def test_stripe_api_key_set_with_different_config():
    """Test that stripe.api_key is set correctly with different config value."""
    # Need to reload the module to pick up the patched value
    import importlib
    import services.stripe.client
    importlib.reload(services.stripe.client)
    
    from services.stripe.client import stripe as client_stripe
    assert client_stripe.api_key == 'test_api_key'


@patch('services.stripe.client.stripe')
def test_stripe_api_key_assignment(mock_stripe):
    """Test that the API key is assigned to stripe.api_key."""
    # Reload the module to trigger the assignment
    import importlib
    import services.stripe.client
    importlib.reload(services.stripe.client)
    
    # Verify that the api_key was set
    assert mock_stripe.api_key == STRIPE_API_KEY


def test_stripe_client_accessible_for_import():
    """Test that stripe client can be imported by other modules."""
    from services.stripe.client import stripe as client_stripe
    
    # Verify that the imported stripe has the expected attributes
    assert hasattr(client_stripe, 'Customer')
    assert hasattr(client_stripe, 'Subscription')
    assert hasattr(client_stripe, 'Product')
    assert hasattr(client_stripe, 'api_key')


@patch('services.stripe.client.STRIPE_API_KEY', '')
def test_stripe_api_key_empty_string():
    """Test behavior when STRIPE_API_KEY is empty string."""
    import importlib
    import services.stripe.client
    importlib.reload(services.stripe.client)
    
    from services.stripe.client import stripe as client_stripe
    assert client_stripe.api_key == ''


@patch('services.stripe.client.STRIPE_API_KEY', None)
def test_stripe_api_key_none():
    """Test behavior when STRIPE_API_KEY is None."""
    import importlib
    import services.stripe.client
    importlib.reload(services.stripe.client)
    
    from services.stripe.client import stripe as client_stripe
    assert client_stripe.api_key is None


def test_stripe_module_attributes():
    """Test that the stripe module has expected attributes after import."""
    from services.stripe.client import stripe as client_stripe
    
    # Test that key Stripe classes are available
    assert hasattr(client_stripe, 'Customer')
    assert hasattr(client_stripe, 'Subscription')
    assert hasattr(client_stripe, 'Product')
    assert hasattr(client_stripe, 'Price')
    assert hasattr(client_stripe, 'PaymentMethod')
    
    # Test that key methods are available
    assert callable(getattr(client_stripe.Customer, 'create', None))
    assert callable(getattr(client_stripe.Subscription, 'list', None))
    assert callable(getattr(client_stripe.Product, 'retrieve', None))


@patch('services.stripe.client.stripe.api_key', 'original_key')
def test_api_key_override():
    """Test that the API key can be overridden after module import."""
    from services.stripe.client import stripe as client_stripe
    
    # The module should have set the API key from config
    original_key = client_stripe.api_key
    
    # Override the API key
    client_stripe.api_key = 'new_test_key'
    assert client_stripe.api_key == 'new_test_key'
    
    # Restore original key
    client_stripe.api_key = original_key


def test_config_import():
    """Test that STRIPE_API_KEY is properly imported from config."""
    from services.stripe.client import STRIPE_API_KEY as imported_key
    from config import STRIPE_API_KEY as config_key
    
    assert imported_key == config_key
    assert imported_key is not None
    assert isinstance(imported_key, str)


def test_stripe_client_module_level_import():
    """Test that the stripe client can be imported at module level."""
    # This test ensures that the module can be imported without errors
    import services.stripe.client
    
    # Verify the module has the expected attributes
    assert hasattr(services.stripe.client, 'stripe')
    assert hasattr(services.stripe.client, 'STRIPE_API_KEY')


@patch('services.stripe.client.stripe')
@patch('services.stripe.client.STRIPE_API_KEY', 'mock_key_123')
def test_module_initialization_with_mock(mock_stripe):
    """Test that module initialization works correctly with mocked stripe."""
    # Reload the module to trigger initialization with mocked values
    import importlib
    import services.stripe.client
    importlib.reload(services.stripe.client)
    
    # Verify that the api_key was set on the mocked stripe object
    assert mock_stripe.api_key == 'mock_key_123'


def test_stripe_client_import_consistency():
    """Test that multiple imports of stripe client return the same object."""
    from services.stripe.client import stripe as stripe1
    from services.stripe.client import stripe as stripe2
    
    # Both imports should reference the same stripe module
    assert stripe1 is stripe2


def test_stripe_client_configuration_isolation():
    """Test that the client configuration doesn't interfere with global stripe."""
    import stripe as global_stripe
    from services.stripe.client import stripe as client_stripe
    
    # They should be the same object (not isolated)
    assert client_stripe is global_stripe
    
    # But the API key should be properly set
    assert client_stripe.api_key == STRIPE_API_KEY

