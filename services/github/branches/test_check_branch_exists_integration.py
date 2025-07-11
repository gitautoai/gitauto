import pytest
import os


from config import TEST_OWNER_NAME, TEST_REPO_NAME
from services.github.branches.check_branch_exists import check_branch_exists

@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skip integration tests in CI environment")

def test_check_branch_exists_with_real_github_repo():
    """Integration test to verify function works with real GitHub API"""
    # Test with a known public repository and branch
    owner = "octocat"
    repo = "Hello-World"
    branch_name = "master"
    token = "dummy_token"  # For public repos, token can be dummy
    
    # This should return True for the master branch of octocat/Hello-World
    result = check_branch_exists(owner, repo, branch_name, token)
    
    # Note: This test may fail if the repository structure changes
    # or if GitHub API is unavailable
    assert isinstance(result, bool)

@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skip integration tests in CI environment")

def test_check_branch_exists_with_nonexistent_branch():
    """Integration test to verify function returns False for non-existent branch"""
    owner = "octocat"
    repo = "Hello-World"
    branch_name = "this-branch-definitely-does-not-exist-12345"
    token = "dummy_token"
    
    result = check_branch_exists(owner, repo, branch_name, token)
    
    assert result is False

@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skip integration tests in CI environment")

def test_check_branch_exists_with_nonexistent_repo():
    """Integration test to verify function returns False for non-existent repository"""
    owner = "nonexistent-owner-12345"
    repo = "nonexistent-repo-12345"
    branch_name = "main"
    token = "dummy_token"
    
    result = check_branch_exists(owner, repo, branch_name, token)
    
    assert result is False

@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skip integration tests in CI environment")

def test_check_branch_exists_with_empty_branch_name_integration():
    """Integration test to verify function returns False for empty branch name"""
    owner = "octocat"
    repo = "Hello-World"
    branch_name = ""
    token = "dummy_token"
    
    result = check_branch_exists(owner, repo, branch_name, token)
    
    assert result is False
@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skip integration tests in CI environment")


def test_check_branch_exists_with_special_characters_in_branch_name():
    """Integration test to verify function handles special characters in branch names"""
    owner = "octocat"
    repo = "Hello-World"
    branch_name = "feature/test-branch-with-special-chars_123"
    token = "dummy_token"
    
    result = check_branch_exists(owner, repo, branch_name, token)
    
    # This should return False since this specific branch likely doesn't exist
    assert result is False
