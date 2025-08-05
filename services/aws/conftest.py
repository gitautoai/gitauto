"""Pytest configuration for AWS services tests."""

def pytest_ignore_collect(path, config):
    """Ignore test_client.py to avoid naming conflicts."""
    if path.basename == "test_client.py":
        return True
    return False