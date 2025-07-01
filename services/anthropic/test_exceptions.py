import pytest

from services.anthropic.exceptions import ClaudeOverloadedError, ClaudeAuthenticationError


class TestClaudeOverloadedError:
    """Test cases for ClaudeOverloadedError exception."""

    def test_claude_overloaded_error_is_exception_subclass(self):
        """Test that ClaudeOverloadedError is a subclass of Exception."""
        assert issubclass(ClaudeOverloadedError, Exception)

    def test_claude_overloaded_error_can_be_instantiated(self):
        """Test that ClaudeOverloadedError can be instantiated."""
        error = ClaudeOverloadedError()
        assert isinstance(error, ClaudeOverloadedError)
        assert isinstance(error, Exception)

    def test_claude_overloaded_error_with_message(self):
        """Test that ClaudeOverloadedError can be instantiated with a message."""
        message = "Claude API is overloaded"
        error = ClaudeOverloadedError(message)
        assert str(error) == message

    def test_claude_overloaded_error_with_empty_message(self):
        """Test that ClaudeOverloadedError can be instantiated with an empty message."""
        error = ClaudeOverloadedError("")
        assert str(error) == ""

    def test_claude_overloaded_error_with_multiple_args(self):
        """Test that ClaudeOverloadedError can be instantiated with multiple arguments."""
        error = ClaudeOverloadedError("Error", 529, "Overloaded")
        assert error.args == ("Error", 529, "Overloaded")

    def test_claude_overloaded_error_can_be_raised(self):
        """Test that ClaudeOverloadedError can be raised and caught."""
        with pytest.raises(ClaudeOverloadedError):
            raise ClaudeOverloadedError("Test error")

    def test_claude_overloaded_error_can_be_caught_as_exception(self):
        """Test that ClaudeOverloadedError can be caught as a generic Exception."""
        with pytest.raises(Exception):
            raise ClaudeOverloadedError("Test error")

    def test_claude_overloaded_error_docstring(self):
        """Test that ClaudeOverloadedError has the correct docstring."""
        expected_docstring = "Raised when Claude API returns 529 Overloaded error"
        assert ClaudeOverloadedError.__doc__ == expected_docstring


class TestClaudeAuthenticationError:
    """Test cases for ClaudeAuthenticationError exception."""

    def test_claude_authentication_error_is_exception_subclass(self):
        """Test that ClaudeAuthenticationError is a subclass of Exception."""
        assert issubclass(ClaudeAuthenticationError, Exception)

    def test_claude_authentication_error_can_be_instantiated(self):
        """Test that ClaudeAuthenticationError can be instantiated."""
        error = ClaudeAuthenticationError()
        assert isinstance(error, ClaudeAuthenticationError)
        assert isinstance(error, Exception)

    def test_claude_authentication_error_with_message(self):
        """Test that ClaudeAuthenticationError can be instantiated with a message."""
        message = "Authentication failed"
        error = ClaudeAuthenticationError(message)
        assert str(error) == message

    def test_claude_authentication_error_with_empty_message(self):
        """Test that ClaudeAuthenticationError can be instantiated with an empty message."""
        error = ClaudeAuthenticationError("")
        assert str(error) == ""

    def test_claude_authentication_error_with_multiple_args(self):
        """Test that ClaudeAuthenticationError can be instantiated with multiple arguments."""
        error = ClaudeAuthenticationError("Error", 401, "Unauthorized")
        assert error.args == ("Error", 401, "Unauthorized")

    def test_claude_authentication_error_can_be_raised(self):
        """Test that ClaudeAuthenticationError can be raised and caught."""
        with pytest.raises(ClaudeAuthenticationError):
            raise ClaudeAuthenticationError("Test error")

    def test_claude_authentication_error_can_be_caught_as_exception(self):
        """Test that ClaudeAuthenticationError can be caught as a generic Exception."""
        with pytest.raises(Exception):
            raise ClaudeAuthenticationError("Test error")

    def test_claude_authentication_error_docstring(self):
        """Test that ClaudeAuthenticationError has the correct docstring."""
        expected_docstring = "Raised when Claude API returns 401 Authentication error"
        assert ClaudeAuthenticationError.__doc__ == expected_docstring