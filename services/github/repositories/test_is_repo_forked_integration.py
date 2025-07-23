from services.github.repositories.is_repo_forked import is_repo_forked
from tests.constants import OWNER, REPO, FORKED_REPO, TOKEN


def test_integration_is_repo_forked_true():
    """Integration test to verify a forked repository returns True."""
    result = is_repo_forked(OWNER, FORKED_REPO, TOKEN)
    assert result is True


def test_integration_is_repo_forked_false():
    """Integration test to verify a non-forked repository returns False."""
    result = is_repo_forked(OWNER, REPO, TOKEN)
    assert result is False


def test_integration_is_repo_forked_nonexistent():
    """Integration test to verify a non-existent repository returns False."""
    result = is_repo_forked(OWNER, "non-existent-repo", TOKEN)
    assert result is False


def test_integration_is_repo_forked_invalid_token():
    """Integration test to verify an invalid token returns False."""
    result = is_repo_forked(OWNER, REPO, "invalid-token")
    assert result is False
