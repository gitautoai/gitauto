# run this file locally with: python -m tests.test_github_manager

from services.github.github_manager import get_installation_access_token


def test_get_installation_token() -> None:
    "Testing GitHub App Installation Token retrieval"
    assert get_installation_access_token(installation_id=47287862) is not None


# test_get_installation_token()
