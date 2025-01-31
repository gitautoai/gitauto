import os

import pytest

from services.github.repo_manager import is_repo_forked


def test_is_repo_forked_for_non_fork():
    token = os.getenv("GITHUB_TOKEN", "")
    result = is_repo_forked("python", "cpython", token)
    assert result is False


def test_is_repo_forked_for_fork():
    token = os.getenv("GITHUB_TOKEN", "")
    result = is_repo_forked("octocat", "Spoon-Knife", token)
    assert result is True
