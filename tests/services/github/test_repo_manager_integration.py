import os
import pytest
from tests.constants import OWNER, REPO, FORKED_REPO
from services.github.repo_manager import is_repo_forked


@pytest.fixture
def gh_app_token():
    token = os.getenv("GH_APP_TOKEN")
    if not token:
        pytest.skip("GH_APP_TOKEN not set")
    return token


def test_is_repo_forked_non_forked(gh_app_token):
    result = is_repo_forked(OWNER, REPO, gh_app_token)
    assert result is False, "Repository should not be detected as forked"


def test_is_repo_forked_forked(gh_app_token):
    result = is_repo_forked(OWNER, FORKED_REPO, gh_app_token)
    assert result is True, "Repository should be detected as forked"
