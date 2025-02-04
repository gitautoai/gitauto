import os
from tests.constants import OWNER, REPO, FORKED_REPO
from services.github.repo_manager import is_repo_forked

# Integration test for is_repo_forked function
# GitHub API: https://docs.github.com/en/rest/repos/repos#get-a-repository

def test_is_repo_forked_non_forked():
    token = os.getenv("GITHUB_TEST_TOKEN")
    assert token, "GITHUB_TEST_TOKEN not provided in environment"
    is_fork = is_repo_forked(OWNER, REPO, token)
    # Expect non-forked repository to return False
    assert is_fork == False, f"{REPO} should not be forked"

def test_is_repo_forked_forked():
    token = os.getenv("GITHUB_TEST_TOKEN")
    assert token, "GITHUB_TEST_TOKEN not provided in environment"
    is_fork = is_repo_forked(OWNER, FORKED_REPO, token)
    # Expect forked repository to return True
    assert is_fork == True, f"{FORKED_REPO} should be forked"
