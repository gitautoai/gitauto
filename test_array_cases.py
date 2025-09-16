#!/usr/bin/env python3
from utils.files.should_skip_rust import should_skip_rust

def test_array_cases():
    # Test cases that should pass (return True)
    passing_cases = [
        ('const TEMPLATE: &str = "array[index] access pattern";', "Array pattern in string"),
        ('const EXAMPLE: &str = "variable[0] in string";', "Variable pattern in string"),
        ('const LIST_VAR: &[i32] = &[1, 2, 3];', "Array literal"),
        ('const ARRAY: [i32; 3] = [1, 2, 3];', "Array type declaration"),
    ]

    # Test cases that should fail (return False)
    failing_cases = [
        ('const ENV_VAR: &str = &ENV_ARRAY[0];', "Actual array indexing"),
        ('static CONFIG: &str = &DEFAULT_CONFIG[0];', "Static array indexing"),
    ]

    print("Testing cases that should PASS (return True):")
    for content, description in passing_cases:
        result = should_skip_rust(content)
        print(f"  {description}: {result} {'✓' if result else '✗'}")

    print("\nTesting cases that should FAIL (return False):")
    for content, description in failing_cases:
        result = should_skip_rust(content)
        print(f"  {description}: {result} {'✓' if not result else '✗'}")

if __name__ == "__main__":
    test_array_cases()
