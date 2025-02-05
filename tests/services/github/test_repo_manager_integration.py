import os
import pytest

from services.github.repo_manager import is_repo_forked


@pytest.fixture(scope="module")
def github_token():
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        pytest.skip("No GITHUB_TOKEN provided for integration tests")
    return token


def test_is_repo_forked_non_fork(github_token):
    # octocat/Hello-World is assumed to be a non-fork repository
    result = is_repo_forked("octocat", "Hello-World", github_token)
    assert result is False, "Expected octocat/Hello-World to not be a fork"


def test_is_repo_forked_fork(github_token):
    # octocat/Spoon-Knife is assumed to be a fork repository
    result = is_repo_forked("octocat", "Spoon-Knife", github_token)
    assert result is True, "Expected octocat/Spoon-Knife to be a fork"
