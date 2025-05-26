import pytest
from utils.number.is_valid_line_number import is_valid_line_number


class TestIsValidLineNumber:
    """Test cases for is_valid_line_number function."""

    def test_valid_integer_line_numbers(self):
        """Test valid integer line numbers (> 1)."""
        assert is_valid_line_number(2) is True
        assert is_valid_line_number(10) is True
        assert is_valid_line_number(100) is True
        assert is_valid_line_number(999999) is True

    def test_invalid_integer_line_numbers(self):
        """Test invalid integer line numbers (<= 1)."""
        assert is_valid_line_number(1) is False
        assert is_valid_line_number(0) is False
        assert is_valid_line_number(-1) is False
        assert is_valid_line_number(-10) is False

    def test_valid_string_line_numbers(self):
        """Test valid string line numbers (digits > 1)."""
        assert is_valid_line_number("2") is True
        assert is_valid_line_number("10") is True
        assert is_valid_line_number("100") is True
        assert is_valid_line_number("999999") is True

    def test_invalid_string_line_numbers(self):
        """Test invalid string line numbers (<= 1 or non-digits)."""
        assert is_valid_line_number("1") is False
        assert is_valid_line_number("0") is False
        assert is_valid_line_number("-1") is False
        assert is_valid_line_number("-10") is False
        assert is_valid_line_number("abc") is False
        assert is_valid_line_number("1.5") is False
        assert is_valid_line_number("2.0") is False
        assert is_valid_line_number("") is False
        assert is_valid_line_number(" ") is False
        assert is_valid_line_number("2a") is False
        assert is_valid_line_number("a2") is False
        assert is_valid_line_number("1 2") is False

    def test_edge_cases_boundary_values(self):
        """Test boundary values around 1."""
        # Integer boundary
        assert is_valid_line_number(1) is False
        assert is_valid_line_number(2) is True
        
        # String boundary
        assert is_valid_line_number("1") is False
        assert is_valid_line_number("2") is True

    def test_non_string_non_integer_types(self):
        """Test non-string, non-integer types (should return False via decorator)."""
        assert is_valid_line_number(None) is False
        assert is_valid_line_number([]) is False
        assert is_valid_line_number({}) is False
        assert is_valid_line_number(set()) is False
        assert is_valid_line_number(1.5) is False
        assert is_valid_line_number(2.0) is False
        assert is_valid_line_number(True) is False  # bool is subclass of int, but True == 1
        assert is_valid_line_number(False) is False  # False == 0

    def test_string_with_leading_zeros(self):
        """Test strings with leading zeros."""
        assert is_valid_line_number("02") is True  # "02".isdigit() is True, int("02") is 2
        assert is_valid_line_number("001") is False  # int("001") is 1
        assert is_valid_line_number("010") is True  # int("010") is 10

    def test_large_numbers(self):
        """Test very large numbers."""
        large_int = 999999999999999999999
        large_str = "999999999999999999999"
        assert is_valid_line_number(large_int) is True
        assert is_valid_line_number(large_str) is True

    def test_super_strict_failure_case(self):
        """Super-strict test case that will fail - testing decorator behavior."""
        # This test verifies that the decorator catches exceptions and returns False
        # We'll create a scenario that might cause an exception in the underlying logic
        
        # Test with a string that would cause int() to fail if not properly handled
        # But since we check isdigit() first, this should return False, not raise an exception
        assert is_valid_line_number("not_a_number") is False
        
        # Test with a very complex object that might cause isinstance to behave unexpectedly
        class ComplexObject:
            def __str__(self):
                return "2"
        
        complex_obj = ComplexObject()
        assert is_valid_line_number(complex_obj) is False

    def test_boolean_values_specifically(self):
        """Test boolean values specifically since bool is a subclass of int."""
        # In Python, bool is a subclass of int: True == 1, False == 0
        assert is_valid_line_number(True) is False  # True == 1, which is not > 1
        assert is_valid_line_number(False) is False  # False == 0, which is not > 1

    def test_string_representations_of_boolean(self):
        """Test string representations that might be confused with booleans."""
        assert is_valid_line_number("True") is False  # Not digits
        assert is_valid_line_number("False") is False  # Not digits
        assert is_valid_line_number("true") is False  # Not digits
        assert is_valid_line_number("false") is False  # Not digits
