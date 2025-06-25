import pytest

from services.github.pull_requests.find_pull_request_by_branch import find_pull_request_by_branch
from tests.constants import OWNER, REPO, TOKEN


def test_integration_find_pull_request_by_branch_nonexistent():
    """Integration test to verify a non-existent branch returns None"""
    # Use a branch name that is very unlikely to exist
    non_existent_branch = "non-existent-branch-12345-test"
    result = find_pull_request_by_branch(OWNER, REPO, non_existent_branch, TOKEN)
    assert result is None


def test_integration_find_pull_request_by_branch_invalid_repo():
    """Integration test to verify an invalid repository returns None"""
    invalid_repo = "non-existent-repo-12345"
    branch_name = "main"
    result = find_pull_request_by_branch(OWNER, invalid_repo, branch_name, TOKEN)
    assert result is None


def test_integration_find_pull_request_by_branch_invalid_owner():
    """Integration test to verify an invalid owner returns None"""
    invalid_owner = "non-existent-owner-12345"
    branch_name = "main"
    result = find_pull_request_by_branch(invalid_owner, REPO, branch_name, TOKEN)
    assert result is None


def test_integration_find_pull_request_by_branch_invalid_token():
    """Integration test to verify an invalid token returns None"""
    branch_name = "main"
    result = find_pull_request_by_branch(OWNER, REPO, branch_name, "invalid-token")
    assert result is None
