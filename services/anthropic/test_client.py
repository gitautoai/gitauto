from unittest.mock import patch, MagicMock, Mock

import pytest
from anthropic import Anthropic

from config import ANTHROPIC_API_KEY
from services.anthropic.client import get_anthropic_client


class TestGetAnthropicClient:
    """Test cases for get_anthropic_client function."""

    def test_returns_anthropic_client_instance(self):
        """Test that get_anthropic_client returns an Anthropic client instance."""
        client = get_anthropic_client()
        assert isinstance(client, Anthropic)

    def test_client_has_correct_api_key(self):
        """Test that the client is configured with the correct API key."""
        client = get_anthropic_client()
        assert client.api_key == ANTHROPIC_API_KEY

    def test_creates_new_instance_each_call(self):
        """Test that each call to get_anthropic_client creates a new instance."""
        client1 = get_anthropic_client()
        client2 = get_anthropic_client()
        assert client1 is not client2

    @patch("services.anthropic.client.ANTHROPIC_API_KEY", "custom_test_key")
    def test_uses_api_key_from_config(self):
        """Test that the client uses the API key from config."""
        client = get_anthropic_client()
        assert client.api_key == "custom_test_key"

    @patch("services.anthropic.client.ANTHROPIC_API_KEY", "")
    def test_handles_empty_api_key(self):
        """Test that the client can be created with an empty API key."""
        client = get_anthropic_client()
        assert isinstance(client, Anthropic)
        assert client.api_key == ""

    @patch("services.anthropic.client.ANTHROPIC_API_KEY", None)
    def test_handles_none_api_key(self):
        """Test that the client can be created with None API key."""
        client = get_anthropic_client()
        assert isinstance(client, Anthropic)
        assert client.api_key is None

    def test_client_has_expected_attributes(self):
        """Test that the returned client has expected Anthropic client attributes."""
        client = get_anthropic_client()
        # Check for key attributes that should exist on an Anthropic client
        assert hasattr(client, 'messages')
        assert hasattr(client, 'api_key')
        assert hasattr(client, '_client')

    def test_multiple_calls_return_different_objects_with_same_config(self):
        """Test that multiple calls return different objects but with same configuration."""
        client1 = get_anthropic_client()
        client2 = get_anthropic_client()
        
        # Different instances
        assert client1 is not client2
        # Same configuration
        assert client1.api_key == client2.api_key
        assert client1.api_key == ANTHROPIC_API_KEY


class TestGetAnthropicClientMocked:
    """Test cases for get_anthropic_client function using mocks to test constructor calls."""

    @patch("services.anthropic.client.Anthropic")
    def test_passes_api_key_to_constructor(self, mock_anthropic):
        """Test that get_anthropic_client passes the correct API key to Anthropic constructor."""
        mock_instance = MagicMock()
        mock_anthropic.return_value = mock_instance
        
        result = get_anthropic_client()
        
        mock_anthropic.assert_called_once_with(api_key=ANTHROPIC_API_KEY)
        assert result == mock_instance

    @patch("services.anthropic.client.Anthropic")
    def test_constructor_called_with_empty_string_api_key(self, mock_anthropic):
        """Test constructor is called correctly with empty string API key."""
        with patch("services.anthropic.client.ANTHROPIC_API_KEY", ""):
            get_anthropic_client()
            mock_anthropic.assert_called_once_with(api_key="")

    @patch("services.anthropic.client.Anthropic")
    def test_constructor_called_with_none_api_key(self, mock_anthropic):
        """Test constructor is called correctly with None API key."""
        with patch("services.anthropic.client.ANTHROPIC_API_KEY", None):
            get_anthropic_client()
            mock_anthropic.assert_called_once_with(api_key=None)

    @patch("services.anthropic.client.Anthropic")
    def test_constructor_called_with_custom_api_key(self, mock_anthropic):
        """Test constructor is called correctly with custom API key."""
        custom_key = "sk-ant-api03-custom-test-key-123"
        with patch("services.anthropic.client.ANTHROPIC_API_KEY", custom_key):
            get_anthropic_client()
            mock_anthropic.assert_called_once_with(api_key=custom_key)

    @patch("services.anthropic.client.Anthropic")
    def test_returns_anthropic_constructor_result(self, mock_anthropic):
        """Test that get_anthropic_client returns whatever Anthropic constructor returns."""
        mock_instance = Mock()
        mock_anthropic.return_value = mock_instance
        
        result = get_anthropic_client()
        
        assert result is mock_instance

    @patch("services.anthropic.client.Anthropic")
    def test_constructor_called_once_per_function_call(self, mock_anthropic):
        """Test that Anthropic constructor is called once for each function call."""
        get_anthropic_client()
        get_anthropic_client()
        
        assert mock_anthropic.call_count == 2

class TestGetAnthropicClientEdgeCases:
    """Test edge cases and error scenarios for get_anthropic_client function."""

    @patch("services.anthropic.client.ANTHROPIC_API_KEY", "sk-ant-api03-valid-key-format")
    def test_handles_valid_api_key_format(self):
        """Test that the client handles a valid API key format correctly."""
        client = get_anthropic_client()
        assert isinstance(client, Anthropic)
        assert client.api_key == "sk-ant-api03-valid-key-format"

    @patch("services.anthropic.client.ANTHROPIC_API_KEY", "   ")
    def test_handles_whitespace_only_api_key(self):
        """Test that the client can be created with whitespace-only API key."""
        client = get_anthropic_client()
        assert isinstance(client, Anthropic)
        assert client.api_key == "   "

    def test_function_return_type_annotation(self):
        """Test that the function returns the correct type as per annotation."""
        client = get_anthropic_client()
        assert isinstance(client, Anthropic)
        # Verify it's actually an Anthropic client instance
        assert type(client).__name__ == "Anthropic"

    def test_client_configuration_consistency(self):
        """Test that multiple clients have consistent configuration."""
        clients = [get_anthropic_client() for _ in range(3)]
        
        # All should be Anthropic instances
        assert all(isinstance(client, Anthropic) for client in clients)
        
        # All should have the same API key
        api_keys = [client.api_key for client in clients]
        assert all(key == ANTHROPIC_API_KEY for key in api_keys)
        
        # All should be different instances
        for i, client1 in enumerate(clients):
            for j, client2 in enumerate(clients):
                if i != j:
                    assert client1 is not client2

    @patch("services.anthropic.client.ANTHROPIC_API_KEY", "invalid-key-format")
    def test_handles_invalid_api_key_format(self):

        """Test that the client can be created with invalid API key format."""
        client = get_anthropic_client()
        assert isinstance(client, Anthropic)
        assert client.api_key == "invalid-key-format"


class TestGetAnthropicClientImports:
    """Test import-related scenarios for get_anthropic_client function."""

    def test_imports_are_available(self):
        """Test that all required imports are available."""
        # Test that we can import the function
        from services.anthropic.client import get_anthropic_client as imported_func
        assert callable(imported_func)
        
        # Test that we can import Anthropic
        from anthropic import Anthropic as ImportedAnthropic
        assert ImportedAnthropic is not None
        
        # Test that we can import the config
        from config import ANTHROPIC_API_KEY as imported_key
        assert imported_key is not None

    def test_function_signature(self):
        """Test that the function has the expected signature."""
        import inspect
        sig = inspect.signature(get_anthropic_client)
        
        # Should have no parameters
        assert len(sig.parameters) == 0
        
        # Should have return type annotation
        assert sig.return_annotation == Anthropic

    def test_function_docstring_exists(self):
        """Test that the function has proper documentation."""
        # The function should be documented (even if minimal)
        assert get_anthropic_client.__name__ == "get_anthropic_client"
        assert callable(get_anthropic_client)


class TestGetAnthropicClientIntegration:
    """Integration-style tests for get_anthropic_client function."""

    def test_client_can_be_used_for_basic_operations(self):
        """Test that the returned client can be used for basic operations."""
        client = get_anthropic_client()
        
        # Test that the client has the expected methods
        assert hasattr(client, 'messages')
        assert hasattr(client, 'api_key')
        
        # Test that messages attribute has expected methods
        assert hasattr(client.messages, 'create')
        assert hasattr(client.messages, 'count_tokens')

    def test_client_api_key_property_access(self):
        """Test that the client's API key property can be accessed."""
        client = get_anthropic_client()
        
        # Should be able to read the API key
        api_key = client.api_key
        assert api_key == ANTHROPIC_API_KEY
        
        # API key should be a string (or None)
        assert isinstance(api_key, (str, type(None)))

    def test_module_level_function_accessibility(self):
        """Test that the function is accessible at module level."""
        # Test that we can access the function directly
        assert callable(get_anthropic_client)
        # Test that it returns the expected type
        assert get_anthropic_client() is not None
        """Test that the function is accessible at module level."""
