import os
import pytest

from services.github.repo_manager import is_repo_forked
from tests.constants import OWNER, REPO, FORKED_REPO

GH_APP_TOKEN = os.environ.get("GH_APP_TOKEN")

@pytest.mark.skipif(not GH_APP_TOKEN, reason="GH_APP_TOKEN not set")
def test_is_repo_forked_nonfork():
    """Test that a non-forked repository returns False"""
    result = is_repo_forked(OWNER, REPO, GH_APP_TOKEN)
    assert result is False, f"Expected non-forked repo to return False, got {result}"

@pytest.mark.skipif(not GH_APP_TOKEN, reason="GH_APP_TOKEN not set")
def test_is_repo_forked_fork():
    """Test that a forked repository returns True"""
    result = is_repo_forked(OWNER, FORKED_REPO, GH_APP_TOKEN)
    assert result is True, f"Expected forked repo to return True, got {result}"
