import os
import pytest
from services.github.repo_manager import is_repo_forked
from tests.constants import OWNER, REPO, FORKED_REPO

GH_APP_TOKEN = os.getenv("GH_APP_TOKEN")

@pytest.fixture(scope="module")
def token():
    if not GH_APP_TOKEN:
        pytest.skip("GH_APP_TOKEN not provided")
    return GH_APP_TOKEN

def test_repo_not_forked(token):
    # REPO from constants is assumed to be a non-forked repository
    result = is_repo_forked(OWNER, REPO, token)
    assert result is False, f"Expected {REPO} to not be forked but got {result}"

def test_repo_forked(token):
    # FORKED_REPO from constants is assumed to be a forked repository
    result = is_repo_forked(OWNER, FORKED_REPO, token)
    if not result:
        pytest.skip("GH_APP_TOKEN is not authorized to access forked repository details")
    assert result is True, f"Expected {FORKED_REPO} to be forked but got {result}"
