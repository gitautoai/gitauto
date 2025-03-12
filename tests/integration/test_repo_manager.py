from tests.constants import OWNER, REPO, FORKED_REPO, TOKEN
from services.github.repo_manager import is_repo_forked


def test_is_repo_forked_non_fork():
    """Integration test for is_repo_forked with a non-forked repository."""
    result = is_repo_forked(OWNER, REPO, TOKEN)
    assert result is False, f"Expected {REPO} to be non-forked, got {result}"


def test_is_repo_forked_fork():
    """Integration test for is_repo_forked with a forked repository."""
    result = is_repo_forked(OWNER, FORKED_REPO, TOKEN)
    assert result is True, f"Expected {FORKED_REPO} to be forked, got {result}"


if __name__ == '__main__':
    test_is_repo_forked_non_fork()
    test_is_repo_forked_fork()
    print("All integration tests passed!")
