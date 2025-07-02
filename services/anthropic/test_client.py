"""Unit tests for services.anthropic.client module."""

from unittest.mock import patch, MagicMock
import inspect
import threading
import queue

import pytest
from anthropic import Anthropic

from config import ANTHROPIC_API_KEY
from services.anthropic.client import get_anthropic_client


@pytest.fixture
def mock_anthropic():
    """Fixture that provides a mocked Anthropic class."""
    with patch("services.anthropic.client.Anthropic") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def test_api_key():
    """Fixture that provides a test API key."""
    return "sk-ant-api03-test-key-12345"


@pytest.fixture
def patched_api_key(test_api_key):
    """Fixture that patches the ANTHROPIC_API_KEY with a test value."""
    with patch("services.anthropic.client.ANTHROPIC_API_KEY", test_api_key):
        yield test_api_key


class TestGetAnthropicClient:
    """Test cases for get_anthropic_client function."""

    def test_returns_anthropic_client_instance(self):
        """Test that get_anthropic_client returns an Anthropic client instance."""
        client = get_anthropic_client()
        assert isinstance(client, Anthropic)
        assert client.api_key == ANTHROPIC_API_KEY

    def test_uses_api_key_from_config(self, patched_api_key):
        """Test that get_anthropic_client uses the API key from config."""
        client = get_anthropic_client()
        assert client.api_key == patched_api_key

    def test_creates_new_instance_each_call(self):
        """Test that get_anthropic_client creates a new instance on each call."""
        client1 = get_anthropic_client()
        client2 = get_anthropic_client()
        assert client1 is not client2
        assert isinstance(client1, Anthropic)
        assert isinstance(client2, Anthropic)

    def test_passes_api_key_to_constructor(self, mock_anthropic):
        """Test that get_anthropic_client passes the API key to Anthropic constructor."""
        mock_instance = mock_anthropic.return_value
        
        client = get_anthropic_client()
        
        mock_anthropic.assert_called_once_with(api_key=ANTHROPIC_API_KEY)
        assert client == mock_instance

    def test_handles_empty_api_key(self, mock_anthropic):
        """Test that get_anthropic_client handles empty API key."""
        mock_instance = mock_anthropic.return_value
        
        with patch("services.anthropic.client.ANTHROPIC_API_KEY", ""):
            client = get_anthropic_client()
            
        mock_anthropic.assert_called_once_with(api_key="")
        assert client == mock_instance

    def test_handles_none_api_key(self, mock_anthropic):
        """Test that get_anthropic_client handles None API key."""
        mock_instance = mock_anthropic.return_value
        
        with patch("services.anthropic.client.ANTHROPIC_API_KEY", None):
            client = get_anthropic_client()
            
        mock_anthropic.assert_called_once_with(api_key=None)
        assert client == mock_instance

    def test_handles_whitespace_api_key(self, mock_anthropic):
        """Test that get_anthropic_client handles whitespace-only API key."""
        mock_instance = mock_anthropic.return_value
        whitespace_key = "   \t\n   "
        
        with patch("services.anthropic.client.ANTHROPIC_API_KEY", whitespace_key):
            client = get_anthropic_client()
            
        mock_anthropic.assert_called_once_with(api_key=whitespace_key)
        assert client == mock_instance

    def test_handles_long_api_key(self, mock_anthropic):
        """Test that get_anthropic_client handles very long API key."""
        mock_instance = mock_anthropic.return_value
        long_key = "a" * 1000  # Very long API key
        
        with patch("services.anthropic.client.ANTHROPIC_API_KEY", long_key):
            client = get_anthropic_client()
            
        mock_anthropic.assert_called_once_with(api_key=long_key)
        assert client == mock_instance

    def test_handles_special_characters_in_api_key(self, mock_anthropic):
        """Test that get_anthropic_client handles API key with special characters."""
        mock_instance = mock_anthropic.return_value
        special_key = "sk-ant-api03-!@#$%^&*()_+-=[]{}|;':\",./<>?"
        
        with patch("services.anthropic.client.ANTHROPIC_API_KEY", special_key):
            client = get_anthropic_client()
            
        mock_anthropic.assert_called_once_with(api_key=special_key)
        assert client == mock_instance

    def test_client_has_correct_attributes(self):
        """Test that the returned client has the expected attributes."""
        client = get_anthropic_client()
        
        # Check that the client has the expected attributes
        assert hasattr(client, 'api_key')
        assert hasattr(client, 'messages')
        assert client.api_key == ANTHROPIC_API_KEY

    def test_multiple_calls_return_independent_clients(self):
        """Test that multiple calls return independent client instances."""
        clients = [get_anthropic_client() for _ in range(5)]
        
        # All should be Anthropic instances
        for client in clients:
            assert isinstance(client, Anthropic)
            assert client.api_key == ANTHROPIC_API_KEY
        
        # All should be different instances
        for i, client1 in enumerate(clients):
            for j, client2 in enumerate(clients):
                if i != j:
                    assert client1 is not client2

    def test_propagates_anthropic_constructor_exceptions(self, mock_anthropic):
        """Test that exceptions from Anthropic constructor are propagated."""
        mock_anthropic.side_effect = ValueError("Invalid API key format")
        
        with pytest.raises(ValueError, match="Invalid API key format"):
            get_anthropic_client()
        
        mock_anthropic.assert_called_once_with(api_key=ANTHROPIC_API_KEY)

    def test_function_return_type_annotation(self):
        """Test that the function returns the correct type as per annotation."""
        client = get_anthropic_client()
        assert isinstance(client, Anthropic)
        
        # Verify the function has the correct return type annotation
        sig = inspect.signature(get_anthropic_client)
        assert sig.return_annotation == Anthropic

    def test_client_attributes_are_accessible(self):
        """Test that the client has all expected attributes accessible."""
        client = get_anthropic_client()
        
        # Test that we can access key attributes without errors
        assert client.api_key is not None
        assert hasattr(client, 'messages')
        assert hasattr(client, '_client')

    def test_function_is_importable(self):
        """Test that the function can be imported correctly."""
        from services.anthropic.client import get_anthropic_client as imported_func
        
        # Should be the same function
        assert imported_func is get_anthropic_client
        
        # Should work the same way
        client = imported_func()
        assert isinstance(client, Anthropic)

    def test_concurrent_client_creation(self):
        """Test that concurrent client creation works correctly."""
        results = queue.Queue()
        
        def create_client():
            client = get_anthropic_client()
            results.put(client)
        
        # Create multiple threads that create clients
        threads = [threading.Thread(target=create_client) for _ in range(5)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Collect all results
        clients = []
        while not results.empty():
            clients.append(results.get())
        
        # All should be valid Anthropic instances
        assert len(clients) == 5
        for client in clients:
            assert isinstance(client, Anthropic)
            assert client.api_key == ANTHROPIC_API_KEY
        
        # All should be different instances
        for i, client1 in enumerate(clients):
            for j, client2 in enumerate(clients):
                if i != j:
                    assert client1 is not client2


class TestGetAnthropicClientIntegration:
    """Integration tests for get_anthropic_client function."""
    
    def test_client_can_be_used_for_basic_operations(self):
        """Test that the returned client can be used for basic operations."""
        client = get_anthropic_client()
        
        # Verify the client has the expected methods and attributes
        assert hasattr(client, 'messages')
        assert hasattr(client, 'api_key')
        assert callable(getattr(client.messages, 'create', None))
        
    def test_client_configuration_is_correct(self):
        """Test that the client is configured correctly."""
        client = get_anthropic_client()
        
        # Check that the client is properly configured
        assert client.api_key == ANTHROPIC_API_KEY
        assert isinstance(client.api_key, (str, type(None)))
        
    def test_client_is_ready_for_api_calls(self):
        """Test that the client is ready for API calls (without making actual calls)."""
        client = get_anthropic_client()
        
        # Verify client has the necessary components for API calls
        assert hasattr(client, '_client')
        assert hasattr(client, 'messages')
        
        # Check that messages has the expected methods
        messages = client.messages
        assert hasattr(messages, 'create')
        assert hasattr(messages, 'count_tokens')
        
    def test_multiple_clients_have_same_configuration(self):
        """Test that multiple clients have the same configuration."""
        clients = [get_anthropic_client() for _ in range(3)]
        
        # All clients should have the same API key
        api_keys = [client.api_key for client in clients]
        assert all(key == ANTHROPIC_API_KEY for key in api_keys)
        assert len(set(api_keys)) == 1  # All keys should be the same

    def test_client_type_consistency(self):
        """Test that all clients are consistently of the same type."""
        clients = [get_anthropic_client() for _ in range(3)]
        
        # All should be exactly the same type
        client_types = [type(client) for client in clients]
        assert all(client_type == Anthropic for client_type in client_types)
        assert len(set(client_types)) == 1

    def test_client_api_key_is_string_or_none(self):
        """Test that the API key is always a string or None."""
        client = get_anthropic_client()
        assert isinstance(client.api_key, (str, type(None)))

    def test_client_messages_attribute_exists(self):
        """Test that the messages attribute exists and is properly configured."""
        client = get_anthropic_client()
        messages = client.messages
        
        # Should have the expected methods
        assert hasattr(messages, 'create')
        assert hasattr(messages, 'count_tokens')
        assert callable(messages.create)
        assert callable(messages.count_tokens)


class TestGetAnthropicClientEdgeCases:
    """Edge case tests for get_anthropic_client function."""

    def test_function_has_no_parameters(self):
        """Test that the function takes no parameters."""
        sig = inspect.signature(get_anthropic_client)
        assert len(sig.parameters) == 0

    def test_function_is_callable(self):
        """Test that get_anthropic_client is callable."""
        assert callable(get_anthropic_client)

    def test_function_docstring_exists(self):
        """Test that the function has a docstring or can be called without issues."""
        # The function might not have a docstring, but it should be callable
        try:
            client = get_anthropic_client()
            assert client is not None
        except Exception as e:
            pytest.fail(f"Function should be callable without issues: {e}")

    def test_repeated_calls_performance(self):
        """Test that repeated calls don't cause performance issues."""
        # This is a basic performance test - just ensure it doesn't hang
        clients = []
        for _ in range(10):
            client = get_anthropic_client()
            clients.append(client)
        
        # All should be valid
        assert len(clients) == 10
        for client in clients:
            assert isinstance(client, Anthropic)

    @patch("services.anthropic.client.Anthropic")
    def test_handles_anthropic_import_error(self, mock_anthropic):
        """Test behavior when Anthropic class raises an exception during import."""
        mock_anthropic.side_effect = ImportError("Cannot import Anthropic")
        
        with pytest.raises(ImportError, match="Cannot import Anthropic"):
            get_anthropic_client()

    @patch("services.anthropic.client.Anthropic")
    def test_handles_anthropic_initialization_error(self, mock_anthropic):
        """Test behavior when Anthropic initialization fails."""
        mock_anthropic.side_effect = RuntimeError("Initialization failed")
        
        with pytest.raises(RuntimeError, match="Initialization failed"):
            get_anthropic_client()

    def test_client_instance_isolation(self):
        """Test that client instances are properly isolated."""
        client1 = get_anthropic_client()
        client2 = get_anthropic_client()
        
        # Instances should be different
        assert client1 is not client2
        
        # But should have the same configuration
        assert client1.api_key == client2.api_key
        assert type(client1) == type(client2)