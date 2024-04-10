def test_handle_installation_event():
    # Test installation event handling
    pass

def test_handle_deletion_event():
    # Test deletion event handling
    pass
# run this file locally with: python -m tests.test_github_manager
import os
from services.github.github_manager import get_installation_access_token


def test_get_installation_token() -> None:
    assert get_installation_access_token(installation_id=47287862) is not None


# test_get_installation_token()
