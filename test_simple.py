#!/usr/bin/env python3
"""Simple test to verify the mock setup works correctly."""

from unittest.mock import Mock

def test_mock_side_effect():
    """Test that mock side_effect works as expected."""
    mock_func = Mock()
    mock_func.side_effect = [
        ([], [], None, None, None, None, False, 50),  # First call
        ([], [], None, None, None, None, False, 75),  # Second call
    ]
    
    # First call
    result1 = mock_func()
    print(f"First call result: {result1}")
    
    # Second call
    result2 = mock_func()
    print(f"Second call result: {result2}")
    
    # Third call should raise StopIteration
    try:
        result3 = mock_func()
        print(f"Third call result: {result3}")
    except StopIteration:
        print("Third call raised StopIteration as expected")

if __name__ == "__main__":
    test_mock_side_effect()
