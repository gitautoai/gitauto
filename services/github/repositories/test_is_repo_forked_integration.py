from services.github.repositories.is_repo_forked import is_repo_forked


def test_integration_is_repo_forked_true(test_owner, test_forked_repo, test_token):
    """Integration test to verify a forked repository returns True."""
    result = is_repo_forked(test_owner, test_forked_repo, test_token)
    assert result is True


def test_integration_is_repo_forked_false(test_owner, test_repo, test_token):
    """Integration test to verify a non-forked repository returns False."""
    result = is_repo_forked(test_owner, test_repo, test_token)
    assert result is False


def test_integration_is_repo_forked_nonexistent(test_owner, test_token):
    """Integration test to verify a non-existent repository returns False."""
    result = is_repo_forked(test_owner, "non-existent-repo", test_token)
    assert result is False


def test_integration_is_repo_forked_invalid_token(test_owner, test_repo):
    """Integration test to verify an invalid token returns False."""
    result = is_repo_forked(test_owner, test_repo, "invalid-token")
    assert result is False
