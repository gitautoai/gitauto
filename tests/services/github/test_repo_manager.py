import os
import pytest
from services.github.repo_manager import is_repo_forked
from tests.constants import FORKED_REPO

def test_is_repo_forked_integration():
    """
    Integration test for is_repo_forked function.
    Verifies that the function correctly identifies a forked repository using the GitHub API.
    Documentation: https://docs.github.com/en/rest/reference/repos#get-a-repository
    """
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        pytest.skip("GITHUB_TOKEN is not set in environment variables.")
    result = is_repo_forked(FORKED_REPO, token=token)
    assert result is True, f"{FORKED_REPO} should be detected as a forked repository."