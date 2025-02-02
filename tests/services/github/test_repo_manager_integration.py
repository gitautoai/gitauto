import os
import pytest

from services.github.repo_manager import is_repo_forked
from tests.constants import OWNER, REPO, FORKED_REPO


@pytest.mark.integration
def test_non_forked_repo():
    token = os.environ.get("GH_APP_TOKEN")
    assert token, "GH_APP_TOKEN environment variable must be set"
    result = is_repo_forked(OWNER, REPO, token)
    assert result is False, f"Expected {REPO} to be a non-forked repository"


@pytest.mark.integration
def test_forked_repo():
    token = os.environ.get("GH_APP_TOKEN")
    assert token, "GH_APP_TOKEN environment variable must be set"
    result = is_repo_forked(OWNER, FORKED_REPO, token)
    assert result is True, f"Expected {FORKED_REPO} to be a forked repository"
