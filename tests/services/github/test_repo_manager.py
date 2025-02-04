import pytest
from services.github.repo_manager import is_repo_forked
from tests.constants import OWNER, REPO, FORKED_REPO
from services.github.github_manager import get_installation_access_token

def test_is_repo_forked_non_forked():
    """Integration test for non-forked repository using REPO from constants."""
    token = get_installation_access_token(OWNER)
    result = is_repo_forked(OWNER, REPO, token)
    assert result is False, f"{REPO} should not be forked"

def test_is_repo_forked_forked():
    """Integration test for forked repository using FORKED_REPO from constants."""
    token = get_installation_access_token(OWNER)
    result = is_repo_forked(OWNER, FORKED_REPO, token)
    assert result is True, f"{FORKED_REPO} should be forked"
