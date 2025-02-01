import pytest

from services.github.repo_manager import is_repo_forked
from tests.constants import OWNER, REPO, FORKED_REPO, GH_APP_TOKEN


def test_non_forked_repo():
    """Test that a non-forked repository returns False."""
    result = is_repo_forked(owner=OWNER, repo=REPO, token=GH_APP_TOKEN)
    assert result is False, f"Expected non-forked repo to return False, got {result}"


def test_forked_repo():
    """Test that a forked repository returns True."""
    result = is_repo_forked(owner=OWNER, repo=FORKED_REPO, token=GH_APP_TOKEN)
    assert result is True, f"Expected forked repo to return True, got {result}"


if __name__ == "__main__":
    pytest.main()
