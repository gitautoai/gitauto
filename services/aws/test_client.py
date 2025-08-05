# This file causes pytest import conflicts and should be ignored
# It does not contain any tests - actual tests are in test_aws_client.py

# Adding a non-test function to prevent pytest from collecting this file
def placeholder_function():
    """Not a test function."""
    return "This is not a test"