#!/usr/bin/env python3
"""Quick test to verify the HTTPError fix works."""

import requests
from utils.error.handle_exceptions import handle_exceptions

@handle_exceptions(default_return_value=[], raise_on_error=False)
def test_function():
    """Test function that raises HTTPError without response."""
    raise requests.exceptions.HTTPError("HTTP Error occurred")

@handle_exceptions(default_return_value=[], raise_on_error=True)
def test_function_with_raise():
    """Test function that raises HTTPError without response and should re-raise."""
    raise requests.exceptions.HTTPError("HTTP Error occurred")

if __name__ == "__main__":
    # Test 1: Should return default value
    result = test_function()
    assert result == [], f"Expected [], got {result}"
    print("✓ Test 1 passed: HTTPError without response returns default value")
    
    # Test 2: Should re-raise when raise_on_error=True
    try:
        test_function_with_raise()
        assert False, "Expected HTTPError to be raised"
    except requests.exceptions.HTTPError:
        print("✓ Test 2 passed: HTTPError without response re-raises when raise_on_error=True")
    
    print("All tests passed! The fix works correctly.")
