"""Simple test to verify pytest is working."""

def test_simple():
    """Simple test that should always pass."""
    assert True


def test_import():
    """Test that we can import the handle_exceptions module."""
    from utils.error.handle_exceptions import handle_exceptions
    assert handle_exceptions is not None
