import re

def test_array_patterns():
    # Test cases
    test_cases = [
        ('const TEMPLATE: &str = "array[index] access pattern";', True),  # Should be allowed (in string)
        ('const ENV_VAR: &str = &ENV_ARRAY[0];', False),  # Should be rejected (actual indexing)
        ('const LIST_VAR: &[i32] = &[1, 2, 3];', True),  # Should be allowed (array literal)
        ('const ARRAY: [i32; 3] = [1, 2, 3];', True),  # Should be allowed (array literal)
    ]

    for line, should_be_allowed in test_cases:
        # Remove string literals first, then check for array indexing
        line_without_strings = re.sub(r'"[^"]*"', '', line)
        line_without_strings = re.sub(r"'[^']*'", '', line_without_strings)
        has_array_indexing = bool(re.search(r"\w+\[", line_without_strings))

        print(f"Line: {line}")
        print(f"Without strings: {line_without_strings}")
        print(f"Has array indexing: {has_array_indexing}")
        print(f"Should be allowed: {should_be_allowed}")
        print(f"Test passes: {has_array_indexing != should_be_allowed}")
        print("---")

test_array_patterns()
